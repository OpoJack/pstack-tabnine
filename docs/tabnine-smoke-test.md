# Official Tabnine discovery smoke test

Passed on 2026-11-03 using the official [Tabnine 1.2.0 release](https://github.com/codota/tabnine-opencode-public/releases/tag/tabnine-v1.2.0), macOS ARM64. The installed launcher reports `tabnine 1.2.0`; its bundled executable reports OpenCode `1.19.5`. This test executed the actual installer and installed `tabnine` launcher, with the Tabnine plugin enabled throughout.

The installer asset was `tabnine-opencode-1.2.0-darwin-arm64.run`, verified against the SHA-256 published in GitHub's release asset metadata:

```text
c2de207eb31f5949bd5c4b045be08e65f83faa1c7ad68c07f06fbecedeb7b98e
```

The staged pstack 0.15.36 source was downloaded from the repository's pinned upstream commit and passed its archive checksum check before entering the sandbox.

## Isolation and scope

- A fresh temporary home, working directory, and XDG config/data/cache/state directories were used. Existing credentials and environment variables were not inherited.
- macOS `sandbox-exec` denied network access and reads of the real home directory. Writes were restricted to the disposable sandbox and the native `mktemp` files needed by the vendor installer.
- The unmodified official installer ran with `--no-login --no-modify-path --host https://sandbox.invalid`.
- No authentication or prompt ran. No model request was submitted. The sandbox contained no authentication data.
- Diagnostics used the installed `tabnine` launcher without `--pure`, so the vendor plugin remained enabled.

## Checks and results

All 13 subprocess checks passed. The [JSON evidence](tabnine-smoke-test.json) records exit codes and complete discovered command, skill, and agent names.

- `tabnine --version` and the bundled executable's `--version` confirmed the expected versions.
- `integrate.py install --source <verified-staged-source>` selected the default `~/.tabnine/opencode/config` destination inside the disposable home.
- `tabnine debug config` found exactly the expected **57 pstack commands and 24 agent definitions**, with no missing or extra pstack IDs.
- `tabnine debug skill` found exactly the expected **57 pstack skills**. Every discovery entry pointed to its readable installed full skill file.
- `tabnine agent list` included all 24 pstack agents.
- `tabnine debug agent` resolved `pstack` as primary, and both `pstack-poteto-agent` and `pstack-how-explorer-1` as subagents. Their prompts referenced the installed adapter.
- `/pstack-poteto-mode` targeted the `pstack` primary coordinator with `subtask: false`.
- `make-bot-ui` remained excluded.
- `integrate.py doctor` found no missing or modified managed files. Reinstallation left the installation manifest unchanged.
- The vendor's `opencode.json` and `tui.json` stayed byte-identical. The Tabnine plugin remained registered and `enabled_providers` remained `["tabnine"]`.

The smoke runner removed its disposable installation after recording the report. A separate initial manual run also passed the discovery checks.

## Reproduce

From this checkout on macOS:

```sh
python3 scripts/smoke_tabnine.py --report /tmp/tabnine-smoke-test.json
```

The runner downloads the pinned official release. To reuse an existing matching download and retain diagnostics:

```sh
python3 scripts/smoke_tabnine.py \
  --installer /path/to/tabnine-opencode-1.2.0-darwin-arm64.run \
  --report /tmp/tabnine-smoke-test.json \
  --keep
```

The runner supports pinned macOS ARM64 and x64 installer assets; only ARM64 was executed for this report. It fails if an installer checksum, diagnostic exit code, inventory, resource pointer, agent mode, or preservation check differs.

## What this establishes

The official Tabnine installation can discover and resolve this integration without authentication. Model entitlement, authenticated tool execution, actual subagent model routing, and behavior across conversational turns were outside the test scope.
