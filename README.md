<img src="assets/icon.svg" width="64" height="64" alt="">

# pstack-tabnine

Install [pstack](https://github.com/cursor/plugins/tree/main/pstack)'s engineering workflows into Tabnine's OpenCode-based CLI. The installer defaults to `~/.tabnine/opencode/config` and supports standalone OpenCode as well.

pstack is a collection of agent instructions and helper scripts, rather than an MCP server. This integration installs **57 skills**, matching slash commands, two adapted delegate prompts, configurable role agents, and a persistent `pstack` primary agent. Cursor Automations and the `make-bot-ui` skill are excluded.

## Install

Start with **Tabnine CLI, Git, and Python 3.10+**.

Run from this checkout in Git Bash:

```sh
py -3 integrate.py install --dry-run
py -3 integrate.py install
```

Use `python` instead of `py -3` if the Python launcher is unavailable.

Restart Tabnine CLI, then use:

```text
/pstack-setup-pstack
/pstack-poteto-mode implement <your task>
/pstack-how explain <subsystem>
/pstack-interrogate review <change>
```

Select the **pstack** primary agent to keep the engineering workflow active across tasks. Slash commands load a workflow for an invocation; persistent mode uses the host's agent selector.

Tabnine's current [configuration documentation](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode/sign-in-and-models.md) identifies `~/.tabnine/opencode/config` inside its `~/.tabnine` home. Its [migration helper](https://github.com/codota/tabnine-opencode-public/blob/2bdafbd14e36a681074b27a3eb7f1a05d2e30940/migration_helper/README.md) confirms additive OpenCode discovery of `skills/`, `commands/`, and `agents/`. Discovery has been verified with the **official Tabnine 1.2.0 installation, bundled OpenCode 1.19.5**, on macOS ARM64, with the Tabnine plugin enabled, network blocked, and no authentication or prompts. All 57 commands, 57 skills, and 24 agent definitions were accessible; see the [smoke-test report](docs/tabnine-smoke-test.md). Standalone OpenCode 1.18.10 discovery also passed. Child model routing and persistent behavior during actual conversations remain unverified. Older `tabnine-legacy` configuration is outside this integration's scope.

For a different config root or OpenCode:

```sh
py -3 integrate.py install --config-dir 'C:/path/to/config'
py -3 integrate.py install --client opencode
py -3 integrate.py install --client opencode --config-dir 'C:/path/to/project/.opencode'
```

OpenCode's global destination defaults to `$XDG_CONFIG_HOME/opencode`, or `~/.config/opencode`. The installer writes namespaced skill entries, commands, agents, and its own `pstack/` directory containing the full upstream resource trees. Native skill IDs and commands use `pstack-<name>` so they do not shadow unrelated skills such as `how` or `tdd`. It preserves existing host configuration and permissions.

## What doesn't carry over

The engineering workflows and bundled resources carry over through the [host adapter](integration/harness.md). The main exceptions are:

- **Cursor-only features:** Automations, routines, webhook wakes, secret-request cards, `make-bot-ui`, and automation bot templates are excluded. Bugbot setup and required bot runs are replaced by ordinary PR review.
- **Cloud and background execution:** workers run locally. Durable scheduling, remote machines, and work after the CLI exits require separate host support.
- **Cursor model rules and Custom Modes:** role models are configured locally, and the **pstack** primary agent provides persistent mode.
- **History and external tools:** transcript-based workflows need explicit session exports. MCP providers, credentials, GitHub access, and app drivers must be configured separately.

## Models

**Model setup is 100% optional.** If you skip it, workflows use your current session model for every role, with no role-specific model or reasoning overrides. Panels still run independent agents on that same model, so they provide no model diversity, and Arena's cross-family judge is skipped.

Run `/pstack-setup-pstack` only if you want to customize those defaults. It discovers the models available in your CLI, helps you choose a reasoning budget and models for each role, and checks model IDs and supported reasoning variants. It then updates `pstack/models.json`, the role agents, and the adapter's role table using the installed configure script. It needs no checkout or download. Restart the CLI afterward to load the changes.

Choose models around the work you expect to do:

- **Task difficulty:** use stronger reasoning for architecture, difficult implementation, and adversarial review; use faster, cheaper models for routine exploration and straightforward edits.
- **Cost and latency:** panel workflows run multiple agents, so both model choice and seat count affect spend. Setup offers small, medium, large, and unlimited reasoning budgets, targeting medium, high, xhigh, and max reasoning respectively, where the provider supports them.
- **Independent perspectives:** choose different model families for Arena, Architect, and Interrogate panels when available. Two runs on the same model provide independent attempts, but no model diversity. Arena's cross-family judge is skipped unless a different family is configured.
- **Availability:** choose models your organization enables and reasoning variants your provider supports. Tabnine IDs use `tabnine/<key>`; inspect choices with `tabnine models`.

For manual configuration, copy [examples/models.json](examples/models.json) to a separate input file, edit the role choices, then run:

```sh
py -3 integrate.py configure --models 'C:/path/to/my-models.json'
```

Roles accept a `provider/model` string or an object such as `{"model": "provider/model", "variant": "high"}`. Panels accept lists; omitted roles inherit the session model. The script validates the file's structure, so check model access and supported variants in your CLI before applying it. Restart afterward.

## Updates, local sources, and removal

[upstream.lock.json](upstream.lock.json) pins pstack **0.15.36**, its commit, and archive checksum. Re-running installation keeps that version. Upgrades require updating the lock and inventory after auditing upstream changes.

Check installed files or remove the integration with:

```sh
py -3 integrate.py doctor
py -3 integrate.py uninstall --dry-run
py -3 integrate.py uninstall
```

Install and uninstall protect local edits and unrelated files. Use `--force` to back up conflicting files under `pstack-backups/<timestamp>/` before replacing or removing them. `doctor` checks file integrity and optional executables; it does not verify credentials or live workflows.
