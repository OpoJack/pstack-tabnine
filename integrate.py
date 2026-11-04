#!/usr/bin/env python3
"""Install pstack skills, commands, and agents for Tabnine CLI or OpenCode."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
MANIFEST = "pstack/manifest.json"
PANELS = {"arena runners", "arena cross-judge pool", "architect runners", "interrogate reviewers"}
ROLES = (
    "feature, refactoring", "bug-fix", "perf-issue", "hillclimb",
    "judgment and prose", "hardest tasks", "how explorer", "how explainer",
    "why investigators", "why synthesizer", "reflect tooling",
    "reflect judgment, divergent, synthesizer", "arena runners",
    "arena cross-judge pool", "swarm workers", "architect runners", "interrogate reviewers",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def read_json(path):
    return json.loads(path.read_text())


def frontmatter(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", text, re.S)
    if not match:
        raise ValueError("Expected YAML frontmatter")
    fields = {}
    for line in match[1].splitlines():
        key, sep, value = line.partition(":")
        if sep and key in {"name", "description", "disable-model-invocation"}:
            value = value.strip()
            if value.startswith('"'):
                value = json.loads(value)
            fields[key] = value
    if not fields.get("name") or not fields.get("description"):
        raise ValueError("Missing skill name or description")
    return fields, match[2]


def markdown(fields, body):
    header = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items())
    return f"---\n{header}\n---\n\n{body.lstrip()}".encode()


def source_files(source, lock):
    if source:
        base = source.expanduser().resolve()
        if (base / "pstack/skills").is_dir():
            base /= "pstack"
        if not (base / "skills").is_dir():
            raise ValueError("--source must contain pstack's skills/ directory")
        result = {}
        for folder in ("skills", "agents", "docs"):
            for path in sorted((base / folder).rglob("*")):
                if path.is_symlink():
                    raise ValueError(f"Source symlinks are unsupported: {path}")
                if path.is_file():
                    relative = path.relative_to(base).as_posix()
                    if any(part in {"node_modules", ".git", "__pycache__"} for part in path.parts):
                        continue
                    result[relative] = (path.read_bytes(), path.stat().st_mode & 0o777)
        result["LICENSE"] = ((base / "LICENSE").read_bytes(), 0o644)
        return result, {"kind": "local", "path": str(base), "verified_archive": False}

    url = f"https://codeload.github.com/cursor/plugins/tar.gz/{lock['commit']}"
    print(f"Downloading pinned pstack {lock['version']} ({lock['commit'][:12]})", file=sys.stderr)
    with urlopen(url, timeout=60) as response:
        archive = response.read(32 * 1024 * 1024 + 1)
    if len(archive) > 32 * 1024 * 1024 or digest(archive) != lock["archive_sha256"]:
        raise ValueError("Upstream archive checksum or size check failed")
    result = {}
    prefix = f"plugins-{lock['commit']}/pstack/"
    total = 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        for member in bundle:
            if not member.name.startswith(prefix):
                continue
            relative = member.name[len(prefix):]
            path = PurePosixPath(relative)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe archive member")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Archive links and special files are unsupported")
            if not (relative.startswith(("skills/", "agents/", "docs/")) or relative == "LICENSE"):
                continue
            total += member.size
            if total > 32 * 1024 * 1024:
                raise ValueError("Extracted pstack exceeds size limit")
            result[relative] = (bundle.extractfile(member).read(), member.mode & 0o777)
    return result, {"kind": "github", "commit": lock["commit"], "verified_archive": True}


def normalize_models(value):
    if not isinstance(value, dict) or set(value) - {"roles"}:
        raise ValueError("Model config must be an object containing only 'roles'")
    roles = value.get("roles", {})
    if not isinstance(roles, dict) or set(roles) - set(ROLES):
        raise ValueError("Unknown role in model config; see the generated models.json")
    result = {}
    for role in ROLES:
        seats = roles.get(role, ["inherit-parent"] * (2 if role in PANELS else 1))
        if not isinstance(seats, list):
            seats = [seats]
        if not seats or (role not in PANELS and len(seats) != 1) or len(seats) > 16:
            raise ValueError(f"Invalid number of seats for {role}")
        normalized = []
        for seat in seats:
            if isinstance(seat, str):
                seat = {"model": seat}
            if not isinstance(seat, dict) or set(seat) - {"model", "variant"}:
                raise ValueError(f"Invalid model entry for {role}")
            model = seat.get("model")
            if not isinstance(model, str) or not (model in {"auto", "inherit-parent"} or re.fullmatch(r"[A-Za-z0-9_.:-]+/[A-Za-z0-9_./:@+-]+", model)):
                raise ValueError(f"{role}: expected inherit-parent or provider/model")
            entry = {"model": "inherit-parent" if model == "auto" else model}
            if "variant" in seat:
                variant = seat["variant"]
                if entry["model"] == "inherit-parent" or not isinstance(variant, str) or not re.fullmatch(r"[\w.-]+", variant):
                    raise ValueError(f"{role}: a variant needs a concrete model and a valid variant name")
                entry["variant"] = variant
            normalized.append(entry)
        result[role] = normalized
    return {"roles": result}


def template(name, config_dir):
    return (ROOT / "integration" / name).read_text().replace("@@CONFIG_DIR@@", str(config_dir))


def role_artifacts(models, config_dir):
    files = {}
    rows = []
    for role, seats in models["roles"].items():
        slug = re.sub(r"[^a-z0-9]+", "-", role).strip("-")
        for index, seat in enumerate(seats, 1):
            name = f"pstack-{slug}-{index}"
            fields = {"description": f"pstack role: {role}, seat {index}", "mode": "subagent"}
            if seat["model"] != "inherit-parent":
                fields.update(seat)
            body = template("poteto-agent.md", config_dir)
            _, body = frontmatter(body)
            files[f"agents/{name}.md"] = (markdown(fields, body), 0o644)
            model = seat["model"] + (f" ({seat['variant']})" if "variant" in seat else "")
            rows.append(f"| {role} | {index} | `{name}` | `{model}` |")
    table = "| Role | Seat | Agent | Model |\n| --- | --- | --- | --- |\n" + "\n".join(rows)
    harness = template("harness.md", config_dir).replace("@@ROLE_TABLE@@", table)
    files["pstack/harness.md"] = (harness.encode(), 0o644)
    files["pstack/models.json"] = (json_bytes(models), 0o644)
    return files


def adapt_text(text, relative, config_dir, client, skill_names=()):
    skills = str(config_dir / "skills")
    text = text.replace("~/.cursor/rules/pstack-models.mdc", str(config_dir / "pstack/models.json"))
    text = text.replace("~/.cursor/skills", skills).replace(".cursor/skills", ".opencode/skills")
    text = text.replace("~/.cursor/plugins/", str(config_dir) + "/")
    text = text.replace("Cursor cloud agent", "local isolated worker")
    text = text.replace("Cursor's built-in `create-skill`", "the skill-authoring procedure in the harness adapter")
    text = text.replace("Cursor's `/loop` command", "the active-session check-and-act cycle in the harness adapter")
    text = text.replace(
        ', `~/Library/Application Support/Cursor` (`state.vscdb.backup`, and `snapshots/roots/<root>` where a `<root>` named for a folder you opened as a workspace balloons)',
        "",
    )
    if relative == "skills/recall/SKILL.md":
        text = re.sub(r"^Transcripts live at .*?$", "Use explicit workspace-scoped session exports as described in the harness adapter. Read the export format instead of assuming JSONL.", text, flags=re.M)
    if relative == "skills/poteto-help/SKILL.md":
        text = text.replace("1. Install with `/add-plugin pstack` in chat, or from Customize in the sidebar.",
                            "1. Install with `python3 integrate.py install` from the pstack-tabnine checkout, then restart the host.")
        text = re.sub(r"^pstack is built for Cursor,.*?$", "This installation supports Tabnine CLI and OpenCode through the local harness adapter. Human commands use the `/pstack-` prefix; models are configured through named role agents.", text, flags=re.M)
        text = re.sub(r"^Other tools can read the skills,.*?$", "Durable wakeups and remote machines require a separately configured host capability. The adapter records the available replacements and evidence gaps.", text, flags=re.M)
        text = re.sub(r"Whether `/poteto-mode` stays on.*?(?=\n## Pick a skill)",
                      "Select the `pstack` primary agent for a persistent engineering workflow. `/pstack-poteto-mode` explicitly selects that coordinator. Other commands use the current primary agent. There is no Cursor Custom Modes keybinding in this integration.\n", text, flags=re.S)
    text = re.sub(r"^\|[^\n]*make-bot-ui[^\n]*\n", "", text, flags=re.M)
    if relative == "docs/guide/09-make-it-yours.md":
        text = re.sub(r"## Build a bot UI.*?(?=\*\*Pitfall:)", "## Excluded automation integration\n\nCursor's webhook bot UI is excluded. The portable personal-mode and evaluation workflows above remain available.\n\n", text, flags=re.S)

    def link(match):
        target = match[1]
        if target.startswith(("#", "/", "https:", "http:", "mailto:")):
            return match[0]
        path, separator, anchor = target.partition("#")
        if not PurePosixPath(path).suffix and not path.endswith("/"):
            return match[0]
        resolved = os.path.normpath(str(PurePosixPath(relative).parent / path))
        if resolved.startswith("skills/"):
            destination = config_dir / "pstack" / resolved
        elif resolved.startswith("docs/") or resolved == "README.md":
            destination = config_dir / "pstack" / resolved
        else:
            return match[0]
        # Angle brackets keep paths with spaces valid in Markdown.
        return f"](<{destination}{separator}{anchor}>)"

    text = re.sub(r"\]\(([^)]+)\)", link, text)
    if skill_names:
        names = "|".join(re.escape(name) for name in sorted(skill_names, key=len, reverse=True))
        text = re.sub(r"(?<![\w/:.-])/(" + names + r")(?![\w/-])", r"/pstack-\1", text)
    return text


def build_install(upstream, lock, models, config_dir, client):
    files = role_artifacts(models, config_dir)
    pointer = f"Read `{config_dir}/pstack/harness.md` before applying this file. Its host mappings replace upstream harness-specific instructions.\n\n"
    found = []
    skill_names = {PurePosixPath(path).parts[1] for path in upstream if path.startswith("skills/") and path.endswith("/SKILL.md")} - set(lock["excluded_skills"])
    for relative, (data, mode) in sorted(upstream.items()):
        parts = PurePosixPath(relative).parts
        if parts[0] == "skills" and parts[1] in lock["excluded_skills"]:
            continue
        if relative.startswith("docs/"):
            if not relative.startswith("docs/guide/"):
                continue
            destination = "pstack/" + relative
        elif relative == "LICENSE":
            destination = "pstack/LICENSE"
        elif relative.startswith("agents/"):
            continue
        elif relative.startswith("skills/"):
            destination = "pstack/" + relative
        else:
            destination = relative

        if relative.endswith("/SKILL.md"):
            if parts[1] in {"setup-pstack"}:
                text = template("setup-pstack.md", config_dir)
            else:
                text = adapt_text(data.decode(), relative, config_dir, client, skill_names)
            fields, body = frontmatter(text)
            name = fields["name"]
            if name != parts[1] or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                raise ValueError(f"Skill name mismatch: {relative}")
            found.append(name)
            if fields.get("disable-model-invocation") == "true":
                body = "Invoke this skill when the user requests it or a pstack workflow explicitly routes here.\n\n" + body
            data = markdown({"name": name, "description": fields["description"]}, pointer + body)
            command = (f"Read `{config_dir}/pstack/harness.md`, then read "
                       f"`{config_dir}/pstack/skills/{name}/SKILL.md` in full and follow it. "
                       "Resolve resources relative to the skill directory.\n\nUser request: $ARGUMENTS\n")
            files[f"skills/pstack-{name}/SKILL.md"] = (markdown({"name": f"pstack-{name}", "description": fields["description"]}, command.replace("\n\nUser request: $ARGUMENTS\n", "\n")), 0o644)
            command_fields = {"description": fields["description"]}
            if name == "poteto-mode":
                command_fields.update({"agent": "pstack", "subtask": False})
            files[f"commands/pstack-{name}.md"] = (markdown(command_fields, command), 0o644)
        elif relative.endswith(".md") and "/scripts/" not in relative:
            text = template("setup-guide.md", config_dir) if relative == "docs/guide/01-setup.md" else data.decode()
            data = (pointer + adapt_text(text, relative, config_dir, client, skill_names)).encode()
        elif relative.endswith("worktree-audit.sh"):
            text = data.decode()
            start = text.index("# Transcripts dir:")
            end = text.index("now=$(date +%s)", start)
            text = text[:start] + '# Explicitly scoped, exported host transcripts only.\ntranscripts="${PSTACK_TRANSCRIPTS_DIR:-}"\n' + text[end:]
            data = text.encode()
        files[destination] = (data, 0o755 if mode & 0o111 else 0o644)

    expected = lock["skills"] - len(lock["excluded_skills"])
    if len(found) != expected:
        raise ValueError(f"Expected {expected} portable skills, found {len(found)}; audit the source and lock")
    for name in ("poteto-agent", "comment-sicko"):
        text = template("poteto-agent.md", config_dir) if name == "poteto-agent" else upstream[f"agents/{name}.md"][0].decode()
        fields, body = frontmatter(text)
        files[f"agents/pstack-{name}.md"] = (markdown({"description": fields["description"], "mode": "subagent"}, pointer + body), 0o644)
    primary = (pointer + f"Read `{config_dir}/pstack/skills/poteto-mode/SKILL.md` in full. "
               "Apply its engineering workflow to each task throughout this session. You own the playbook and delegates.\n")
    files["agents/pstack.md"] = (markdown({"description": "Persistent pstack engineering workflow", "mode": "primary"}, primary), 0o644)
    files["pstack/README.md"] = (("# pstack\n\nThis is the Tabnine/OpenCode adaptation. Read `harness.md` before the guide. "
                                     "Use `/pstack-poteto-help` for routing and `/pstack-poteto-mode` to start a task. "
                                     "Select the `pstack` primary agent for persistent mode.\n").encode(), 0o644)
    # Ship a self-contained configure command for /pstack-setup-pstack.
    files["pstack/integration/integrate.py"] = (Path(__file__).read_bytes(), 0o755)
    files["pstack/integration/upstream.lock.json"] = (json_bytes(lock), 0o644)
    for path in sorted((ROOT / "integration").glob("*.md")):
        files["pstack/integration/integration/" + path.name] = (path.read_bytes(), 0o644)
    return files, found


def safe_path(config_dir, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe managed path: {relative}")
    target = config_dir.joinpath(*path.parts)
    for parent in [target, *target.parents]:
        if parent == config_dir:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing managed symlink: {parent}")
    return target


def load_manifest(config_dir):
    path = safe_path(config_dir, MANIFEST)
    if not path.exists():
        return None
    manifest = read_json(path)
    if not isinstance(manifest, dict) or manifest.get("format") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unrecognized installation manifest")
    for relative in manifest["files"]:
        safe_path(config_dir, relative)
    return manifest


def atomic_write(path, data, mode):
    if path.is_file() and path.read_bytes() == data and path.stat().st_mode & 0o777 == mode:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pstack-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_changes(config_dir, files, old, metadata, force=False, dry_run=False, remove=False, preserve_hashes=None):
    tracked = (old or {}).get("files", {})
    stale = set(tracked) - set(files)
    conflicts = []
    for relative in sorted(set(files) | stale):
        path = safe_path(config_dir, relative)
        if path.exists():
            if not path.is_file():
                raise ValueError(f"Managed path is not a file: {path}")
            actual = digest(path.read_bytes())
            expected = tracked.get(relative)
            desired = digest(files[relative][0]) if relative in files else None
            if actual != expected and actual != desired:
                conflicts.append(relative)
    if conflicts and not force:
        raise ValueError("Preserving conflicting files (use --force to back up and replace):\n" + "\n".join(conflicts))
    if dry_run:
        print(json.dumps({"config_dir": str(config_dir), "write": sorted(files), "remove": sorted(stale), "backup": conflicts}, indent=2))
        return
    if conflicts:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = config_dir / "pstack-backups" / stamp
        for relative in conflicts:
            source = safe_path(config_dir, relative)
            destination = safe_path(config_dir, f"pstack-backups/{stamp}/{relative}")
            atomic_write(destination, source.read_bytes(), source.stat().st_mode & 0o777)
        print(f"Backed up {len(conflicts)} conflicting file(s) to {backup}", file=sys.stderr)
    for relative, (data, mode) in sorted(files.items()):
        path = safe_path(config_dir, relative)
        if not path.exists() or path.read_bytes() != data or path.stat().st_mode & 0o777 != mode:
            atomic_write(path, data, mode)
    for relative in sorted(stale):
        safe_path(config_dir, relative).unlink(missing_ok=True)
    if remove:
        safe_path(config_dir, MANIFEST).unlink(missing_ok=True)
    else:
        hashes = {name: digest(data) for name, (data, _) in sorted(files.items())}
        hashes.update(preserve_hashes or {})
        manifest = {"format": 1, **metadata, "files": hashes}
        atomic_write(safe_path(config_dir, MANIFEST), json_bytes(manifest), 0o644)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "configure", "uninstall", "doctor"))
    parser.add_argument("--client", choices=("tabnine", "opencode"), default="tabnine")
    parser.add_argument("--config-dir", type=Path, help="Default: ~/.tabnine/opencode/config, or XDG_CONFIG_HOME/opencode with --client opencode")
    parser.add_argument("--source", type=Path, help="Install from a local pstack tree instead of downloading the pinned archive")
    parser.add_argument("--models", type=Path, help="JSON role-to-model configuration")
    parser.add_argument("--force", action="store_true", help="Back up conflicting files before replacing them")
    parser.add_argument("--dry-run", action="store_true", help="Print the file plan without writing")
    args = parser.parse_args(argv)
    if args.source and args.action != "install":
        parser.error("--source applies only to install")
    if args.models and args.action not in {"install", "configure"}:
        parser.error("--models applies only to install or configure")
    default = Path.home() / ".tabnine/opencode/config" if args.client == "tabnine" else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "opencode"
    config_dir = (args.config_dir or default).expanduser().resolve()
    if any(character in str(config_dir) for character in "\n\r`'@@"):
        raise ValueError("Config path contains unsupported prompt or shell delimiters")
    old = load_manifest(config_dir)
    preserve_hashes = None
    if args.action == "doctor":
        if not old:
            raise ValueError(f"No managed pstack installation in {config_dir}")
        missing = [name for name in old["files"] if not safe_path(config_dir, name).is_file()]
        changed = [name for name, expected in old["files"].items() if name not in missing and digest(safe_path(config_dir, name).read_bytes()) != expected]
        print(json.dumps({"config_dir": str(config_dir), "source": old["source"], "skills": len(old["skills"]), "missing": missing, "changed": changed, "executables": {name: shutil.which(name) for name in ("tabnine", "opencode", "git", "gh", "bun", "node", "java", "jq", "rg")}}, indent=2))
        return 1 if missing or changed else 0
    if args.action == "uninstall":
        if not old:
            raise ValueError(f"No managed pstack installation in {config_dir}")
        apply_changes(config_dir, {}, old, {}, args.force, args.dry_run, remove=True)
        print("pstack uninstall planned" if args.dry_run else "Removed managed pstack files; unrelated files and backups preserved.")
        return 0
    models_path = args.models or config_dir / "pstack/models.json"
    models = normalize_models(read_json(models_path) if models_path.exists() else {})
    if args.models and not args.models.exists():
        raise ValueError(f"Model config does not exist: {args.models}")
    if args.action == "configure":
        if not old:
            raise ValueError("Install pstack before configuring it")
        if not args.models:
            raise ValueError("configure requires --models <json-file>; use a separate file to preserve conflict detection")
        generated = role_artifacts(models, config_dir)
        # Retain all existing managed files except role agents being regenerated.
        previous_roles = set(old.get("role_files", []))
        files = {}
        for name in old["files"]:
            if name not in previous_roles:
                path = safe_path(config_dir, name)
                if not path.is_file():
                    raise ValueError(f"Managed file missing: {name}; reinstall first")
                files[name] = (path.read_bytes(), path.stat().st_mode & 0o777)
        files.update(generated)
        # Configuring models does not adopt edits to unrelated managed skills.
        preserve_hashes = {name: expected for name, expected in old["files"].items() if name not in previous_roles}
        metadata = {key: old[key] for key in ("client", "source", "skills", "upstream")}
        metadata["role_files"] = sorted(generated)
    else:
        lock = read_json(ROOT / "upstream.lock.json")
        upstream, provenance = source_files(args.source, lock)
        files, skills = build_install(upstream, lock, models, config_dir, args.client)
        metadata = {"client": args.client, "source": provenance, "skills": sorted(skills), "upstream": lock, "role_files": sorted(role_artifacts(models, config_dir))}
    apply_changes(config_dir, files, old, metadata, args.force, args.dry_run, preserve_hashes=preserve_hashes)
    if not args.dry_run:
        print(f"{'Installed' if args.action == 'install' else 'Configured'} {len(metadata['skills'])} pstack skills in {config_dir}")
        print("Restart the CLI, then use /pstack-poteto-mode or select the pstack primary agent.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, tarfile.TarError) as error:
        print(f"pstack: {error}", file=sys.stderr)
        sys.exit(1)
