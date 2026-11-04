# pstack for Tabnine CLI and OpenCode

Read this adapter before following any pstack skill or reference. Its mappings replace upstream harness-specific instructions. The engineering steps, evidence requirements, and permission gates in the skills still apply. The host's instructions and actual tool schemas take priority.

Invoke the host CLI as `tabnine`.

The installation root is `@@CONFIG_DIR@@`. The local pstack reference root is `@@CONFIG_DIR@@/pstack`. Full skills and their resources live at `@@CONFIG_DIR@@/pstack/skills/<name>/SKILL.md`. Native discovery entries are named `pstack-<name>` under `@@CONFIG_DIR@@/skills/` and point to those full skills. Resolve a full skill's relative paths from its directory, including `scripts/`, `references/`, and `playbooks/`. The namespace avoids shadowing unrelated skills with names such as `how` or `tdd`.

## Tools and agents

| Upstream wording | This harness |
| --- | --- |
| `Task` | The host's `task` tool. Pass only fields its schema accepts. |
| `generalPurpose` | `general`, unless the role table supplies an agent. |
| `poteto-agent` | `pstack-poteto-agent`. Include the absolute poteto-mode skill path in the brief. |
| `comment-sicko` | `pstack-comment-sicko`. |
| `AskQuestion` | `question`, when available; otherwise ask in the conversation. |
| `Read`, `Grep`, `Glob`, `Shell` | `read`, `grep`, `glob`, `bash`, or their available equivalents. |
| Todo list | `todowrite`, when available; otherwise maintain a short written checklist. |
| `/name`, `/pstack:name`, or another pstack skill | Read `@@CONFIG_DIR@@/pstack/skills/<name>/SKILL.md` in full and follow it. Human commands and native skill IDs are `pstack-<name>`. |

Select a model by choosing the named agent from the role table below as `subagent_type`. The task tool does not accept Cursor's per-call `model`, `readonly`, `run_in_background`, `environment`, `cloud_base_branch`, or `file_attachments` fields. Put file paths, branch, output directory, scope, and read-only constraints in the prompt. Omit unsupported fields. For a fresh task omit `task_id`; a supported resume uses the returned task ID. Execute independent tasks concurrently only when the host supports it. Otherwise run them sequentially and retain independent briefs and output directories. Report that limitation.

A named reviewer agent is general-purpose and can edit files. Give review-only briefs explicit read-only scope and inspect `git status` afterward. Use built-in `explore` for code-only read-only exploration when appropriate. Avoid granting additional permissions in host config merely to run a workflow.

Task agents share the host's working directory. For competing writers, prepare distinct worktrees using the host's isolation feature if available. A worktree path in a prompt alone does not bind the task's tools to that directory. If the host cannot bind a worker's cwd, run a separate CLI process in the worktree, or serialize writers and review each diff. Never claim worktree isolation while workers share a checkout.

## Workflow dependencies

Start local work with the host CLI, Git, and Python 3.10+. Check extra executables only when the selected workflow reaches a step that uses them. Prefer the host's read/search tools or `git grep` for repository exploration and Python's standard library for JSON processing when they provide equivalent results. Git Bash supplies Bash and common Unix utilities on Windows; `gh`, `jq`, and `rg` are separate tools whose availability must be checked.

PR operations need an authenticated forge CLI or an available equivalent integration. The bundled PR watcher specifically needs Bun and `gh`; the multi-phase plan validator needs Node; Statechart needs a supported JavaScript runtime and its Java/TLC toolchain. Run helpers with their actual dependencies. If an equivalent cannot preserve a required check, report that step's missing dependency and continue independent work. Claim verification only from checks that ran. Missing optional executables in `doctor` are informational; its exit status checks managed-file integrity.

## Windows execution

Use the host's actual shell. Paths in this adapter use forward slashes, including Windows drive paths, so Markdown links and prompts keep their separators. Quote paths containing spaces. Python is `py -3` on a standard Windows installation, or `python` when the Python launcher is unavailable.

Run the bundled `.sh` helpers through Bash, for example `bash '<skill-directory>/scripts/worktree-audit.sh' ...` and `bash '<skill-directory>/scripts/log.sh' ...`. Git Bash or a separately configured WSL environment supplies the Unix tools those helpers use; execute Git operations in the same environment as the working tree. For the TypeScript entry points, invoke the runtime explicitly: `bun '<poteto-mode-directory>/scripts/watch-pr/watch-pr' ...` or `bun '<statechart-directory>/scripts/statechart.ts' ...`. Node and Deno alternatives remain in the Statechart skill. Windows does not execute Unix shebang launchers directly.

Use Windows-compatible tools for process, performance, and disk inspection. Skip upstream cleanup steps for unsupported platforms. Missing Bash, runtimes, or native app drivers are dependencies to resolve, not successful verification.

## Models

`@@CONFIG_DIR@@/pstack/models.json` owns role choices. The generated agent files implement them. Read this table instead of upstream model-rule lines, fallback slugs, or effort ladders. Default agents inherit the session model. Two independent seats on one model are not a multi-model review. Report reduced diversity; skip Arena's cross-family judge unless its configured model family differs from the parent's. Determine family from actual model identity, such as Claude or GPT; all Tabnine models share the `tabnine/` provider prefix. The cross-judge pool is an ordered choice for one judge, not a fan-out panel. A rejected configured model is a visible configuration error: fix the role choice with the user instead of silently substituting a vendor model. Only use variants the configured provider actually supports.

@@ROLE_TABLE@@

`/pstack-setup-pstack` configures roles. After a change, restart the host to reload agents. For a persistent poteto-mode session, select the primary agent `poteto`. A slash command applies to its invocation; it is not Cursor's Custom Modes UI.

## Portable replacements

- Cloud workers become local task agents subject to the isolation rule above. Remote machines, cloud dashboards, fleet APIs, and Project stores are unavailable. Keep program state in project-local Markdown files such as `notes.md`; report when a workflow needs persistent orchestration the host does not offer.
- `/loop` means continue the task's check-and-act cycle during the active session. For PR state use the bundled `watch-pr` helper or the forge CLI, subject to the host's execution limits. Durable timers, scheduled wakeups, background completion events, and work after the CLI exits require a separately configured host scheduler. Report the limitation and leave a resumable state capsule when the session cannot continue. Do not claim a scheduled wakeup exists.
- PR creation and review-thread triage use `gh` or the upstream playbook's supported forge CLI. Existing bot comments are normal review evidence. Starting, configuring, or waiting specifically for Bugbot or Cursor security automation is excluded. Missing bot output does not block an independent review. Preserve ordinary CI and human-review gates.
- `create-skill` means author an Agent Skills directory with `SKILL.md`, a matching lowercase kebab-case `name`, and a useful `description`. Read related local skills for conventions, use relative resource paths, and verify discovery. For project-local skills use the host's known project skills directory; for personal skills use `@@CONFIG_DIR@@/skills/`. Preserve explicit user-only invocation instructions in the skill body because discovery metadata differs between hosts.
- `/deslop` from `cursor-team-kit` becomes a direct diff review for redundant abstractions, dead code, style drift, and unnecessary comments, using pstack's principles and `no-comments`. `control-ui` and `control-cli` mean an available browser driver, PTY driver, or project verification harness. If none can drive the changed surface, record the missing live proof; compilation is not a substitute.
- Discover MCP tools from the host's actual enabled tool catalog. Use only available integrations and report missing evidence sources. MCP providers are configured separately from this installer.

## History and excluded features

For `recall`, `reflect`, `correct`, `automate-me`, session pickup, and transcript-based evals, export the relevant session using the host's supported export command, for example `tabnine export <session-id>`, or use a transcript file the user provides. Verify the session belongs to the active workspace before reading it. Inspect `tabnine export --help` for supported options. Exported history may be JSON rather than JSONL. Never infer an internal database path or scan unrelated projects. If history is unavailable, name the evidence gap and use the current conversation and live repository state. Do not claim that a transcript-dependent audit passed.

The worktree audit helper scans history only when `PSTACK_TRANSCRIPTS_DIR` names an explicitly scoped directory of exported transcripts. With no export directory, chat recency is unknown; inspect live sessions separately before deleting any worktree.

Cursor Automations, routines, webhook wakes, `update_state`, Cursor secret-request cards, `/make-bot-ui`, and the automation bot templates are excluded. When a larger workflow reaches one of these steps, say `Skipped in this harness: <step>. <reason>.` and continue independent work. If a required output is missing, name the blocked dependency and a concrete host-supported alternative. Keep secrets in the host's secret mechanism or environment, never in prompts or generated model config.
