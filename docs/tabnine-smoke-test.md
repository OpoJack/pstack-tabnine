# Official Tabnine discovery smoke test

Passed on 2026-11-16 (America/New_York) using the official [Tabnine 1.2.0 release](https://github.com/codota/tabnine-opencode-public/releases/tag/tabnine-v1.2.0), macOS ARM64. The installed launcher reports `tabnine 1.2.0`. This release bundles OpenCode `1.19.5`, as recorded in the original portability research. This test executed the actual installer and installed `tabnine` launcher, with the Tabnine plugin enabled throughout.

The installer asset was `tabnine-opencode-1.2.0-darwin-arm64.run`, verified against the SHA-256 published in GitHub's release asset metadata:

```text
c2de207eb31f5949bd5c4b045be08e65f83faa1c7ad68c07f06fbecedeb7b98e
```

The staged pstack 0.15.43 source was downloaded from the repository's pinned upstream commit and passed its archive checksum check before entering the sandbox. GitHub rate-limited a repeat archive request, so this run reused the already downloaded archive and rechecked its pinned checksum.

## Isolation and scope

- A fresh temporary home, working directory, and XDG config/data/cache/state directories were used. Existing credentials and environment variables were not inherited.
- macOS `sandbox-exec` denied network access and reads of the real home directory. Writes were restricted to the disposable sandbox and the native `mktemp` files needed by the vendor installer.
- The unmodified official installer ran with `--no-login --no-modify-path --host https://sandbox.invalid`.
- No authentication or prompt ran. No model request was submitted. The sandbox contained no authentication data.
- Diagnostics used the installed `tabnine` launcher without `--pure`, so the vendor plugin remained enabled.

## Checks and results

All 12 subprocess checks passed. The [JSON evidence](tabnine-smoke-test.json) records exit codes and complete discovered command, skill, and agent names.

- `tabnine --version` confirmed the expected launcher version.
- `integrate.py install --source <verified-staged-source>` selected the default `~/.tabnine/opencode/config` destination inside the disposable home.
- `tabnine debug config` found exactly the expected **57 pstack commands and 15 agent definitions**, with no missing or extra pstack IDs.
- `tabnine debug skill` found exactly the expected **57 pstack skills**. Every discovery entry pointed to its readable installed full skill file.
- `tabnine agent list` included all 15 pstack agents.
- `tabnine debug agent` resolved `poteto` as primary, and both `pstack-poteto-agent` and `pstack-swarm-workers-1` as subagents. Their prompts referenced the installed adapter.
- `/pstack-poteto-mode` targeted the `poteto` primary coordinator with `subtask: false`.
- `make-bot-ui` remained excluded.
- `integrate.py doctor` found no missing or modified managed files. Reinstallation left the installation manifest unchanged.
- The vendor's `opencode.json` and `tui.json` stayed byte-identical. The Tabnine plugin remained registered and `enabled_providers` remained `["tabnine"]`.

The smoke runner removed its disposable installation after recording the report. A separate initial manual run also passed the discovery checks.

## What this establishes

The official Tabnine installation can discover and resolve this integration without authentication. Model entitlement, authenticated tool execution, actual subagent model routing, and behavior across conversational turns were outside the test scope.
