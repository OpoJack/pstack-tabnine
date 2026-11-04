<img src="assets/icon.svg" width="64" height="64" alt="">

# pstack-tabnine

Install [pstack](https://github.com/cursor/plugins/tree/main/pstack)'s engineering workflows into Tabnine's OpenCode-based CLI. The installer defaults to `~/.tabnine/opencode/config` and supports standalone OpenCode as well.

pstack is a collection of agent instructions and helper scripts, rather than an MCP server. This integration installs **57 skills**, matching slash commands, two adapted delegate prompts, configurable role agents, and a persistent `pstack` primary agent. Cursor Automations and the `make-bot-ui` skill are excluded.

## Install

Requires Python 3.10+ and internet access to GitHub for the pinned upstream download. Run from this checkout:

```sh
python3 integrate.py install --dry-run
python3 integrate.py install
```

Restart Tabnine CLI, then use:

```text
/pstack-setup-pstack
/pstack-poteto-mode implement <your task>
/pstack-how explain <subsystem>
/pstack-interrogate review <change>
```

Select the **pstack** primary agent to keep the engineering workflow active across tasks. Slash commands load a workflow for an invocation; persistent mode uses the host's agent selector.

Tabnine's current [configuration documentation](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode/sign-in-and-models.md) identifies `~/.tabnine/opencode/config` inside its `~/.tabnine` home. Its [migration helper](https://github.com/codota/tabnine-opencode-public/blob/2bdafbd14e36a681074b27a3eb7f1a05d2e30940/migration_helper/README.md) confirms additive OpenCode discovery of `skills/`, `commands/`, and `agents/`. The public Tabnine 1.2.0 bundle uses OpenCode 1.19.5; this integration has been checked with the available **OpenCode 1.18.10** CLI. Tabnine runtime discovery, child model routing, and persistent behavior still need verification on an authenticated Tabnine installation. No Tabnine executable was available during development. Older `tabnine-legacy` configuration is outside this integration's scope.

For a different config root or OpenCode:

```sh
python3 integrate.py install --config-dir /path/to/config
python3 integrate.py install --client opencode
python3 integrate.py install --client opencode --config-dir /path/to/project/.opencode
```

OpenCode's global destination defaults to `$XDG_CONFIG_HOME/opencode`, or `~/.config/opencode`. The installer writes namespaced skill entries, commands, agents, and its own `pstack/` directory containing the full upstream resource trees. Native skill IDs and commands use `pstack-<name>` so they do not shadow unrelated skills such as `how` or `tdd`. It preserves existing host configuration and permissions.

## What carries over

- Engineering workflows: poteto-mode and its 23 playbooks, architecture exploration, Arena candidate comparisons, Swarm coverage, adversarial review, TDD, code cleanup, TypeScript guidance, and 24 engineering principles.
- Research and communication: how, why, teach, recall, reflect, correct, automate-me, prompt sharpening, progress summaries, technical writing, and decision trails.
- Verification and shipping: app verification skill generation and maintenance, formal verification, TLA+ statecharts, benchmark review, worktree audits, plan checks, GitHub PR watching, review triage, and stack shipping.
- Bundled references, guide pages, examples, scripts, and executable permissions.

The adapter is [integration/harness.md](integration/harness.md). Every installed skill and agent points to it. It takes precedence over upstream tool names and model-selection instructions; the engineering procedures remain upstream's. This follows the mapping approach used by pstack's own [Claude Code adapter](https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/harness/claude-code.md).

| Cursor dependency | Adaptation |
| --- | --- |
| `Task`, `AskQuestion`, todos, file tools | Actual host tools and accepted schemas. |
| Task-specific models and effort slugs | Named agents with `provider/model` and optional `variant`. |
| Cursor model rules | `pstack/models.json` and generated role agents. |
| Custom Modes | The `pstack` primary agent. |
| Cloud agents | Local task agents; separate writers require real cwd isolation or serialized work. |
| `/loop`, scheduled wakeups, fleet orchestration | Active-session progress; persistent scheduling requires host support. |
| Cursor transcript paths | Explicit session exports scoped to the current workspace. |
| PR tooling and Bugbot | Forge CLI and normal review threads; no Cursor bot setup or required bot runs. |
| `create-skill`, `deslop`, `control-ui`, `control-cli` | Agent Skills authoring, direct diff review, and available app drivers. |
| Automations, routines, secret-request cards, `make-bot-ui` | Excluded. |

Background execution, durable wakeups, cloud machines, and multi-model diversity depend on the host's capabilities. The installer cannot provide them through prompts alone. Missing live drivers or history are reported as gaps in proof. Connected MCP providers, credentials, and GitHub access are configured separately.

## Models

By default every role inherits the session model. Panel workflows keep two independent seats, but independent runs on the same model do not provide model diversity. Arena's cross-family judge is skipped unless a different family is configured.

Run `/pstack-setup-pstack`, or copy [examples/models.json](examples/models.json) and edit it. A role accepts a model string or an object with a model and provider-supported reasoning variant. Panels accept lists. For example, after replacing these placeholders with IDs your CLI lists:

```json
{
  "roles": {
    "how explorer": "provider/model-a",
    "architect runners": [
      { "model": "provider/model-a", "variant": "high" },
      "other-provider/model-b"
    ]
  }
}
```

```sh
python3 integrate.py configure --models /path/to/my-models.json
```

Use a separate input file so conflict detection can protect the installed `pstack/models.json`. Omitted roles inherit the session model. Tabnine model IDs use `tabnine/<key>`; run `tabnine models` to find organization-enabled choices. The script validates configuration shape; model entitlement and supported variants must be checked with the CLI's model list and provider config. Restart the host after changes. Setup ships a local copy of the configure script, so configuring an installed integration needs neither this checkout nor a download.

## Updates, local sources, and removal

[upstream.lock.json](upstream.lock.json) pins pstack **0.15.36**, its commit, and the archive's SHA-256. Installation verifies the archive before reading its files. Re-running installation uses the same version and is idempotent. To upgrade upstream, audit the new capabilities and harness dependencies, then update the commit, version, checksum, and inventory together. Installation never follows a moving `main` branch.

For an offline or modified source tree:

```sh
python3 integrate.py install --source /path/to/cursor-plugins/pstack
```

Local sources must have the expected skill inventory. The manifest records a local source as unverified rather than claiming it matches the pinned archive. Keep pstack's upstream MIT license, which is installed at `pstack/LICENSE`.

```sh
python3 integrate.py doctor
python3 integrate.py uninstall --dry-run
python3 integrate.py uninstall
```

The manifest tracks installed files by hash. Install and uninstall refuse conflicting user files and local edits before changing anything. `--force` saves conflicts under `pstack-backups/<timestamp>/` before replacing or removing them. Uninstall preserves unrelated files and backups; it may leave empty directories. Model configuration preserves unrelated skill edits, which `doctor` continues to report. `doctor` checks file integrity and reports optional executables; it does not claim that credentials or a live workflow are working.

Optional workflow dependencies include Git, `gh`, `jq`, and `rg`. The PR watcher uses Bun and installs its locked dependencies on first invocation. The statechart helper supports modern Node, Bun, or Deno and requires Java/TLC for model checking; see its bundled skill for exact versions. Video summaries need a suitable rendering/encoding tool. The installer itself uses only Python's standard library and does not install these tools.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests cover installation, resource paths, executable scripts, checksum and path validation, model configuration, conflict backups, idempotence, and safe removal. If OpenCode is installed, a discovery test checks generated commands, skills, and agents through the real CLI without making a model request.

The upstream capability audit and primary-source references live in [docs/research.md](docs/research.md).
