#!/usr/bin/env python3
"""Check pstack discovery in an unauthenticated, sandboxed official Tabnine install.

macOS only. Downloads are staged before running vendor code. Child processes use
a disposable home, no inherited credentials, and a network-denying macOS sandbox.
No model request is submitted. Use --keep to retain binaries and diagnostic logs.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "tabnine-v1.2.0"
CHECKSUMS = {
    "arm64": "c2de207eb31f5949bd5c4b045be08e65f83faa1c7ad68c07f06fbecedeb7b98e",
    "x64": "d13762f0c1f0af7d6f4501d2f38659e36e90c31ec15b35f666e9323febd55ab6",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def smoke(sandbox, installer, arch):
    home = sandbox / "home"
    workspace = sandbox / "workspace"
    for name in ("home", "workspace", "tmp", "logs", "xdg/config", "xdg/cache", "xdg/data", "xdg/state"):
        (sandbox / name).mkdir(parents=True)
    env = {
        "HOME": str(home),
        "PATH": f"{home}/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "TMPDIR": str(sandbox / "tmp"),
        "XDG_CONFIG_HOME": str(sandbox / "xdg/config"),
        "XDG_CACHE_HOME": str(sandbox / "xdg/cache"),
        "XDG_DATA_HOME": str(sandbox / "xdg/data"),
        "XDG_STATE_HOME": str(sandbox / "xdg/state"),
        "CI": "1", "TERM": "dumb", "SHELL": "/bin/bash",
    }
    profile = sandbox / "sandbox.sb"
    rules = [
        "(version 1)", "(allow default)", "(deny network*)", "(deny file-write*)",
        f'(allow file-write* (subpath {json.dumps(str(sandbox))}) (literal "/dev/null") (literal "/dev/tty"))',
        f"(deny file-read* (subpath {json.dumps(str(Path.home().resolve()))}))",
    ]
    # Stock macOS mktemp with no arguments uses the Darwin user temp directory,
    # even with our TMPDIR set. Permit only its random tmp.<suffix> files there.
    native_temp = str(Path(tempfile.gettempdir()).resolve())
    for parent in {native_temp, native_temp.replace("/private/var/", "/var/", 1)}:
        pattern = "^" + re.escape(parent) + r"/tmp\.[A-Za-z0-9]+$"
        rules.append(f"(allow file-write* (regex {json.dumps(pattern)}))")
    profile.write_text("\n".join(rules) + "\n")
    commands = []

    def run(label, command):
        # Write stdout to a real file: some bundled Bun builds truncate large pipes.
        stdout = sandbox / "logs" / f"{label}.stdout"
        stderr = sandbox / "logs" / f"{label}.stderr"
        with stdout.open("w") as out, stderr.open("w") as err:
            result = subprocess.run(
                ["/usr/bin/sandbox-exec", "-f", str(profile), *map(str, command)],
                env=env, cwd=workspace, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, timeout=60,
            )
        commands.append({"check": label, "exit_code": result.returncode})
        require(result.returncode == 0, f"{label} failed: {stderr.read_text()[-3000:]}")
        print(f"PASS {label}", file=sys.stderr, flush=True)
        return stdout.read_text()

    source = sandbox / "integration-source"
    source.mkdir()
    for name in ("integrate.py", "upstream.lock.json"):
        shutil.copy2(ROOT / name, source / name)
    shutil.copytree(ROOT / "integration", source / "integration")
    spec = importlib.util.spec_from_file_location("pstack_integration", source / "integrate.py")
    integration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(integration)
    lock = integration.read_json(source / "upstream.lock.json")
    files, provenance = integration.source_files(None, lock)
    for name, (data, mode) in files.items():
        path = sandbox / "upstream/pstack" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)

    run("extract-official-installer", ["/bin/sh", installer, "--noexec", "--target", sandbox / "installer"])
    run("install-official-tabnine", ["/bin/bash", sandbox / "installer/install-tabnine.sh", "--no-login", "--no-modify-path", "--host", "https://sandbox.invalid"])
    launcher = home / ".local/bin/tabnine"
    tabnine_version = run("tabnine-version", [launcher, "--version"]).strip()
    config_dir = home / ".tabnine/opencode/config"
    host_config = {name: (config_dir / name).read_bytes() for name in ("opencode.json", "tui.json")}
    install = [sys.executable, source / "integrate.py", "install", "--source", sandbox / "upstream/pstack"]
    run("install-pstack-default-path", install)
    config = json.loads(run("tabnine-debug-config", [launcher, "debug", "config"]))
    skills = json.loads(run("tabnine-debug-skill", [launcher, "debug", "skill"]))
    agent_listing = run("tabnine-agent-list", [launcher, "agent", "list"])
    manifest = json.loads((config_dir / "pstack/manifest.json").read_text())
    expected = {f"pstack-{name}" for name in manifest["skills"]}
    loaded_commands = {name for name in config["command"] if name.startswith("pstack-")}
    loaded_skills = {skill["name"] for skill in skills if skill["name"].startswith("pstack-")}
    expected_agents = {Path(name).stem for name in manifest["files"] if name.startswith("agents/")}
    loaded_agents = {name for name in config["agent"] if name.startswith("pstack")}
    require(loaded_commands == expected, "Command catalogue does not match the installed skills")
    require(loaded_skills == expected, "Skill catalogue does not match the installed skills")
    require(loaded_agents == expected_agents, "Agent catalogue does not match installed definitions")
    require(all(f"{name} (" in agent_listing for name in expected_agents), "Agent list omitted an installed agent")
    require("pstack-make-bot-ui" not in loaded_skills, "Excluded Cursor skill was installed")
    require(config["enabled_providers"] == ["tabnine"], "Tabnine provider configuration changed")
    require(config["plugin"] == [[f"file://{home}/.tabnine/opencode/plugin", {"host": "https://sandbox.invalid"}]], "Official Tabnine plugin is not enabled")
    mode = config["command"]["pstack-poteto-mode"]
    require(mode["agent"] == "pstack" and mode["subtask"] is False, "poteto-mode does not select the primary coordinator")
    for name, expected_mode in (("pstack", "primary"), ("pstack-poteto-agent", "subagent"), ("pstack-how-explorer-1", "subagent")):
        agent = json.loads(run(f"resolve-{name}", [launcher, "debug", "agent", name]))
        require(agent["mode"] == expected_mode, f"Incorrect agent mode for {name}")
        require(str(config_dir / "pstack/harness.md") in agent["prompt"], f"Missing adapter in {name}")
    for skill in skills:
        if skill["name"] in expected:
            name = skill["name"].removeprefix("pstack-")
            target = config_dir / "pstack/skills" / name / "SKILL.md"
            require(target.is_file() and str(target) in skill["content"], f"Missing skill target: {name}")
    run("pstack-doctor", [sys.executable, source / "integrate.py", "doctor"])
    before = (config_dir / "pstack/manifest.json").read_bytes()
    run("reinstall-pstack", install)
    require((config_dir / "pstack/manifest.json").read_bytes() == before, "Reinstall changed the installation manifest")
    require(all((config_dir / name).read_bytes() == content for name, content in host_config.items()), "pstack modified vendor configuration")
    auth = sandbox / "xdg/data/opencode/auth.json"
    require(not auth.exists() or json.loads(auth.read_text()) == {}, "Unexpected authentication data in the sandbox")
    return {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "release": RELEASE,
        "release_url": f"https://github.com/codota/tabnine-opencode-public/releases/tag/{RELEASE}",
        "platform": f"darwin-{arch}",
        "installer_sha256": CHECKSUMS[arch],
        "tabnine_version": tabnine_version,
        "pstack_version": lock["version"],
        "pstack_commit": lock["commit"],
        "upstream_archive_verified": provenance["verified_archive"],
        "network_blocked_during_child_processes": True,
        "real_home_reads_blocked": True,
        "model_requests": 0,
        "authenticated": False,
        "vendor_config_preserved": True,
        "commands": sorted(loaded_commands),
        "skills": sorted(loaded_skills),
        "agents": sorted(loaded_agents),
        "checks": commands,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", type=Path, help="Use an already downloaded official 1.2.0 .run installer (checksum verified)")
    parser.add_argument("--report", type=Path, help="Write JSON evidence to this path")
    parser.add_argument("--keep", action="store_true", help="Keep the disposable installation and raw logs")
    args = parser.parse_args()
    require(platform.system() == "Darwin" and Path("/usr/bin/sandbox-exec").exists(), "This smoke runner requires macOS sandbox-exec")
    arch = {"arm64": "arm64", "x86_64": "x64"}.get(platform.machine())
    require(arch in CHECKSUMS, "No pinned installer for this architecture")
    sandbox = Path(tempfile.mkdtemp(prefix="pstack-tabnine-smoke-")).resolve()
    require(not sandbox.is_relative_to(Path.home().resolve()), "Sandbox must be outside the real home")
    try:
        asset = f"tabnine-opencode-1.2.0-darwin-{arch}.run"
        installer = sandbox / asset
        if args.installer:
            shutil.copy2(args.installer, installer)
        else:
            with urlopen(f"https://github.com/codota/tabnine-opencode-public/releases/download/{RELEASE}/{asset}", timeout=60) as response:
                installer.write_bytes(response.read(128 * 1024 * 1024 + 1))
        require(hashlib.sha256(installer.read_bytes()).hexdigest() == CHECKSUMS[arch], "Official installer checksum mismatch")
        report = smoke(sandbox, installer, arch)
        encoded = json.dumps(report, indent=2) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(encoded)
        print(encoded)
    finally:
        if args.keep:
            print(f"Sandbox retained at {sandbox}", file=sys.stderr)
        else:
            shutil.rmtree(sandbox)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        sys.exit(1)
