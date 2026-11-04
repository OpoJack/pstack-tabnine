import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("integrate", ROOT / "integrate.py")
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pstack-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.config = self.base / "config with spaces"
        self.source = self.base / "upstream"
        names = ["poteto-mode", "setup-pstack", "how", "statechart", "make-bot-ui"]
        names += [f"principle-fixture-{i}" for i in range(53)]
        for name in names:
            path = self.source / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f'---\nname: {name}\ndescription: "Test {name}"\ndisable-model-invocation: true\n---\n\n# {name}\n[Guide](../../docs/guide/README.md)\n[Resource](references/example.md)\n')
        for name in ("poteto-agent", "comment-sicko"):
            path = self.source / "agents" / f"{name}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"---\nname: {name}\ndescription: Test agent\n---\n\nBody\n")
        guide = self.source / "docs/guide/README.md"
        guide.parent.mkdir(parents=True)
        guide.write_text("[How](../../skills/how/SKILL.md)\n")
        resource = self.source / "skills/how/references/example.md"
        resource.parent.mkdir(parents=True)
        resource.write_text("Reference evidence.\n")
        helper = self.source / "skills/statechart/scripts/statechart"
        helper.parent.mkdir(parents=True)
        helper.write_text("#!/bin/sh\nprintf 'fixture helper\\n'\n")
        helper.chmod(0o755)
        golden = self.source / "skills/statechart/scripts/test/report.md"
        golden.parent.mkdir(parents=True)
        golden.write_text("# Golden output\n")
        (self.source / "LICENSE").write_text("Upstream license.\n")

    def run_cli(self, action="install", *extra):
        args = [action, "--config-dir", str(self.config), *map(str, extra)]
        if action == "install":
            args += ["--source", str(self.source)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return integration.main(args)

    def snapshot(self):
        return {path.relative_to(self.config).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns) for path in self.config.rglob("*") if path.is_file()}

    def test_install_exposes_skills_commands_agents_and_resources(self):
        self.assertEqual(self.run_cli(), 0)
        self.assertEqual(len(list((self.config / "skills").glob("*/SKILL.md"))), 57)
        self.assertEqual(len(list((self.config / "commands").glob("*.md"))), 57)
        self.assertFalse((self.config / "skills/pstack-make-bot-ui").exists())
        self.assertTrue((self.config / "agents/pstack.md").exists())
        self.assertTrue((self.config / "pstack/LICENSE").exists())
        self.assertEqual((self.config / "pstack/skills/how/references/example.md").read_text().splitlines()[-1], "Reference evidence.")
        command = (self.config / "commands/pstack-how.md").read_text()
        self.assertIn("$ARGUMENTS", command)
        self.assertIn(str(self.config / "pstack/skills/how/SKILL.md"), command)
        wrapper = (self.config / "skills/pstack-how/SKILL.md").read_text()
        self.assertIn('name: "pstack-how"', wrapper)
        self.assertIn(str(self.config / "pstack/skills/how/SKILL.md"), wrapper)
        skill = (self.config / "pstack/skills/how/SKILL.md").read_text()
        self.assertIn(f"](<{self.config}/pstack/docs/guide/README.md>)", skill)
        self.assertIn(f"](<{self.config}/pstack/skills/how/references/example.md>)", skill)
        helper = self.config / "pstack/skills/statechart/scripts/statechart"
        self.assertEqual(subprocess.check_output([str(helper)], text=True), "fixture helper\n")
        self.assertEqual((self.config / "pstack/skills/statechart/scripts/test/report.md").read_text(), "# Golden output\n")
        self.assertEqual(self.run_cli("doctor"), 0)

    def test_reinstall_is_idempotent_including_manifest(self):
        self.run_cli()
        before = self.snapshot()
        self.run_cli()
        self.assertEqual(before, self.snapshot())

    def test_dry_run_leaves_no_destination(self):
        self.run_cli("install", "--dry-run")
        self.assertFalse(self.config.exists())

    def test_conflict_preflight_and_force_backup(self):
        self.config.mkdir()
        path = self.config / "commands/pstack-how.md"
        path.parent.mkdir()
        path.write_text("My existing command.\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Preserving conflicting files"):
            self.run_cli()
        self.assertEqual(before, self.snapshot())
        self.run_cli("install", "--force")
        backups = list(self.config.glob("pstack-backups/*/commands/pstack-how.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "My existing command.\n")

    def test_uninstall_preserves_unrelated_files_and_refuses_local_edits(self):
        self.run_cli()
        unrelated = self.config / "opencode.json"
        unrelated.write_text('{"model": "my/model"}\n')
        edited = self.config / "pstack/skills/how/SKILL.md"
        edited.write_text(edited.read_text() + "User edit.\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Preserving conflicting files"):
            self.run_cli("uninstall")
        self.assertEqual(before, self.snapshot())
        self.run_cli("uninstall", "--force")
        self.assertTrue(unrelated.exists())
        self.assertFalse(edited.exists())
        self.assertFalse((self.config / "pstack/manifest.json").exists())
        self.assertIn("User edit.", next(self.config.glob("pstack-backups/*/pstack/skills/how/SKILL.md")).read_text())

    def test_symlinked_destination_cannot_write_outside_config(self):
        self.config.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.config / "skills").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_cli()
        self.assertFalse(list(outside.iterdir()))
        self.assertFalse((self.config / "agents").exists())

    def test_configure_models_updates_seats_and_installed_configure_works(self):
        self.run_cli()
        choices = self.base / "models.json"
        choices.write_text(json.dumps({"roles": {"arena runners": [{"model": "provider/model-a", "variant": "high"}], "how explorer": "other/model-b"}}))
        script = self.config / "pstack/integration/integrate.py"
        result = subprocess.run(["python3", str(script), "configure", "--config-dir", str(self.config), "--models", str(choices)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.config / "agents/pstack-arena-runners-2.md").exists())
        agent = (self.config / "agents/pstack-arena-runners-1.md").read_text()
        self.assertIn('model: "provider/model-a"', agent)
        self.assertIn('variant: "high"', agent)
        self.assertIn("provider/model-a (high)", (self.config / "pstack/harness.md").read_text())
        self.assertEqual(self.run_cli("doctor"), 0)

    def test_configure_preserves_edits_without_adopting_their_hash(self):
        self.run_cli()
        path = self.config / "pstack/skills/how/SKILL.md"
        path.write_text(path.read_text() + "Local edit.\n")
        choices = self.base / "models.json"
        choices.write_text("{}")
        self.run_cli("configure", "--models", choices)
        self.assertTrue(path.read_text().endswith("Local edit.\n"))
        self.assertEqual(self.run_cli("doctor"), 1)

    def test_invalid_models_do_not_mutate_install(self):
        self.run_cli()
        choices = self.base / "models.json"
        before = self.snapshot()
        for config in ({"roles": {"unknown": "inherit-parent"}}, {"roles": {"how explorer": "cursor-model-slug"}}, {"roles": {"arena runners": []}}, {"roles": {"how explorer": {"model": "inherit-parent", "variant": "high"}}}):
            choices.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                self.run_cli("configure", "--models", choices)
            self.assertEqual(before, self.snapshot())

    def test_download_checksum_rejection_does_not_mutate_config(self):
        with patch.object(integration, "urlopen", return_value=io.BytesIO(b"untrusted archive")):
            with self.assertRaisesRegex(ValueError, "checksum"):
                integration.source_files(None, integration.read_json(ROOT / "upstream.lock.json"))
        self.assertFalse(self.config.exists())

    def test_archive_traversal_is_rejected_even_with_matching_checksum(self):
        lock = integration.read_json(ROOT / "upstream.lock.json")
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w:gz") as bundle:
            entry = tarfile.TarInfo(f"plugins-{lock['commit']}/pstack/skills/../../escape")
            entry.size = 1
            bundle.addfile(entry, io.BytesIO(b"x"))
        archive = data.getvalue()
        lock["archive_sha256"] = integration.digest(archive)
        with patch.object(integration, "urlopen", return_value=io.BytesIO(archive)):
            with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                integration.source_files(None, lock)

    def test_tabnine_and_opencode_default_paths(self):
        with patch.object(Path, "home", return_value=self.base), patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.base / "xdg")}):
            with contextlib.redirect_stdout(io.StringIO()):
                integration.main(["install", "--source", str(self.source)])
                integration.main(["install", "--client", "opencode", "--source", str(self.source)])
        self.assertTrue((self.base / ".tabnine/opencode/config/pstack/manifest.json").exists())
        self.assertTrue((self.base / "xdg/opencode/pstack/manifest.json").exists())

    @unittest.skipUnless(shutil.which("opencode"), "OpenCode CLI not installed")
    def test_real_opencode_discovers_generated_commands_skills_and_agents(self):
        self.run_cli()
        env = {**os.environ, "OPENCODE_CONFIG_DIR": str(self.config)}
        for command in (["debug", "config"], ["debug", "skill"], ["debug", "agent", "pstack"]):
            # Some Bun CLI versions exit before fully flushing a large piped stdout.
            with tempfile.TemporaryFile(mode="w+") as output:
                result = subprocess.run(["opencode", "--pure", *command], env=env, stdout=output, stderr=subprocess.PIPE, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                output.seek(0)
                data = json.load(output)
            if command == ["debug", "config"]:
                self.assertIn("pstack-how", data["command"])
                self.assertEqual(data["agent"]["pstack"]["mode"], "primary")
            elif command == ["debug", "skill"]:
                local = [skill for skill in data if str(self.config / "skills") in skill["location"]]
                self.assertEqual(len(local), 57)
            else:
                self.assertEqual(data["mode"], "primary")
                self.assertIn(str(self.config / "pstack/harness.md"), data["prompt"])


if __name__ == "__main__":
    unittest.main()
