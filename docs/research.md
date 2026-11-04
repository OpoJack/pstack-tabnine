# pstack portability research for Tabnine CLI

Researched on 2026-11-03. This is an implementation brief, not an implementation. The goal is to expose every portable pstack workflow through a script and Tabnine/OpenCode discovery while excluding Cursor product integrations.

## Source versions and method

| Source | Pinned revision | What was inspected |
| --- | --- | --- |
| cursor/plugins | [`fd268b808c786469e6dd8c8d9db864d0de4d669e`](https://github.com/cursor/plugins/commit/fd268b808c786469e6dd8c8d9db864d0de4d669e) | Complete `pstack/` tree, plugin manifests, skills, agents, playbooks, references, utilities, guide, harness adapter, and dormant automation pack. Both manifests identify pstack **0.15.36**. |
| Tabnine public distribution material | [`2bdafbd14e36a681074b27a3eb7f1a05d2e30940`](https://github.com/codota/tabnine-opencode-public/commit/2bdafbd14e36a681074b27a3eb7f1a05d2e30940) | README, changelog, migration helper, and field mappings. Product source is not public in this repository. |
| Tabnine public release | [`tabnine-v1.2.0`](https://github.com/codota/tabnine-opencode-public/releases/tag/tabnine-v1.2.0), published 2026-10-28 | Downloaded the Darwin arm64 archive and read its `manifest.json`, without running its installer or binary. It reports `pluginVersion: 1.2.0`, **`opencodeVersion: 1.19.5`**, and `jqVersion: 1.8.2`. |
| OpenCode version matching that bundle | [`v1.19.5`, `810c0eba1a7348036f8bdf61e6632d0c36c6876c`](https://github.com/anomalyco/opencode/tree/810c0eba1a7348036f8bdf61e6632d0c36c6876c) | Skill, command, agent, configuration, task-tool, and headless-run loaders. This is the recommended initial compatibility baseline. |
| Current OpenCode HEAD | [`4f271bcd150a31d7e5e5430df9fe05e9046e131d`](https://github.com/anomalyco/opencode/commit/4f271bcd150a31d7e5e5430df9fe05e9046e131d) | Root package reports **2.2.5**. Inspected V2 loaders and task replacement to distinguish current upstream from Tabnine's published bundle. |

The public release archive inspected is [tabnine-opencode-1.2.0-darwin-arm64.tar.gz](https://github.com/codota/tabnine-opencode-public/releases/download/tabnine-v1.2.0/tabnine-opencode-1.2.0-darwin-arm64.tar.gz). Its manifest describes that archive, not every enterprise deployment. Official Tabnine web documentation is cited separately because those pages are not pinned. Repository checkout inspection used temporary copies outside this project. No product commands, installers, or upstream test suites were executed.

The scope inventory is **58 registered skills: 34 workflow/helper skills and 24 principle skills; two agents; 23 poteto-mode playbooks; five utility commands across three script trees; and three additional dormant Benny instruction skills**. The 573 tracked files under `pstack/` include references, assets, script modules, and a large statechart test corpus. Benny's three instruction skills are outside the registered skill root. The Cursor manifest registers only `./skills/` and `./agents/`; it does not declare hooks, MCP servers, rules, or a separate commands directory. Sources: [manifest][manifest], [Cursor manifest][Cursor manifest], [upstream README][upstream README], and the [pinned tree](https://github.com/cursor/plugins/tree/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack).

Inventory reproduction, in an upstream checkout at the pinned commit:

```sh
git ls-tree -r --name-only HEAD pstack
find pstack/skills -name SKILL.md
find pstack/agents -name '*.md'
find pstack/skills/poteto-mode/playbooks -name '*.md'
find pstack/automations/benny -name SKILL.md
```

## Findings that determine the design

1. **Target the OpenCode-based Tabnine product.** Official Tabnine material describes a managed OpenCode distribution with a Tabnine plugin, rather than establishing an independently maintained public fork. The new installer assigns it `tabnine`; the older CLI becomes `tabnine-legacy`. Legacy TOML commands and `.tabnine/agent/` configuration are source formats for migration, not the new destination. See [Tabnine product documentation](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode.md), [legacy CLI notice](https://docs.tabnine.com/main/getting-started/tabnine-cli), and [Tabnine migration mapping][Tabnine migration mapping].
2. **Most of pstack is executable agent instruction, not shell automation.** A script can install/discover/read those instructions and launch a Tabnine session; it cannot replace model judgment, adversarial review, runtime verification, or unavailable credentials by printing a prompt. Preserve the full instruction/reference trees and the utility implementations. pstack itself warns that Agent Skills format alone does not port its delegation and mode behavior. See [poteto help][poteto help].
3. **Cursor tool parameters are not OpenCode task parameters.** In the matched V1 source, `task` accepts `description`, `prompt`, `subagent_type`, `task_id`, `command`, and optionally experimental `background`. It selects the model from the chosen agent configuration, otherwise the parent. It has no per-call Cursor `model`, `readonly`, `environment`, `cloud_base_branch`, `file_attachments`, or `run_in_background` fields. Role-specific agent definitions are needed for multi-model behavior. See [V1 task implementation][V1 task implementation].
4. **Skills and slash commands are related but version-sensitive.** V1.19.5 automatically adds loaded skills to its command catalogue unless a command of the same name already exists. Explicit Markdown wrappers remain useful for stable names, argument forwarding, agent choice, and older versions. Do not claim that a separate command is always required, or that every OpenCode-derived build automatically does this. See [V1 command catalogue][V1 command catalogue].
5. **Exclude Cursor services without discarding portable engineering work.** Keep PR review/stack shipping, local parallel analysis, verification, formal methods, session learning, and decision logs. Remove Cursor Automations/Grok Bot/Benny deployment, cloud-machine controls, Custom Mode UI, and built-in `/loop` instructions. Durable wakeups, VM isolation, and Project-store orchestration need real substitutes before equivalent behavior can be claimed. The upstream [Claude Code adapter][Claude Code adapter] already distinguishes portable mechanics from Cursor-only services.
6. **Tabnine controls model availability and governance.** Use discovered `tabnine/<key>` models and supported variants. Cursor slugs and `-fast` suffixes are not portable identifiers. In headless mode, approval prompts can prevent work; a wrapper must report those failures rather than infer that the workflow succeeded. See [Tabnine models](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode/sign-in-and-models.md) and [scripts and CI](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode/scripts-and-ci.md).

## Complete registered-skill inventory

Each linked source is the skill at the pinned pstack commit. “Portable” means the workflow can be retained, with the common tool adapter described below. It does not mean every external tool is installed. “Adapt” identifies an additional host dependency. “Exclude” identifies the Cursor-specific capability outside the requested scope.

### Workflow and helper skills: 34

| Skill and source | Capability to preserve | Mapping and dependencies |
| --- | --- | --- |
| [poteto-mode][poteto-mode] | Main engineering coordinator: routes tasks to playbooks, copies their steps into todos, applies principles, delegates, verifies, and reports evidence. | Adapt. Use an opt-in primary `pstack` agent plus command entry point. Rewrite Cursor tools, model rules, built-in dependencies, and wake mechanisms. Keep coordinator ownership in the receiving chat. |
| [poteto-help][poteto-help] | Explains setup, routing, costs, recovery, and customization; returns an actionable prompt without performing a help question’s task. | Adapt install/model/mode instructions and help links. Help must describe the actual supported feature set. |
| [setup-pstack][setup-pstack] | Discovers models, preserves custom role choices, chooses one of four reasoning budgets, validates roles, writes configuration, and offers behavioral/formal verification skills. | Adapt `.mdc` output and Cursor slug parsing. Preserve all 17 role lines and panel multiplicity; generate supported agent model/variant settings. |
| [in-your-own-words][in-your-own-words] | Restates the goal and the problem before work. | Portable. Prompt-only. |
| [sharpen][sharpen] | Deepens a proposed task using professional methods, primary material, and independent proof, then rewrites the prompt. | Portable. Preserve the boundary that it rewrites the task rather than executing it. |
| [how][how] | Explores runtime flow and ownership; one explainer for simple scope, two to four explorers plus a synthesizer for complex scope. | Adapt read-only agents and role models. Preserve explorer/explainer references and output contract. |
| [why][why] | Finds rationale across source control, tickets, documents, team chat, infrastructure observability, error tracking, and analytics. | Adapt MCP discovery. Preserve one investigator per available source/category, provenance/confidence, null results, explicit coverage gaps, and citation checking. |
| [recall][recall] | Reconstructs recent topic context from workspace chat history, shared records, and live git/PR state. | Adapt transcript/session retrieval, time/window filtering, and source citations. Keep workspace scope. Do not scan Cursor history or unrelated projects. |
| [ketchup][ketchup] | Read-only catch-up since the user’s previous message, including results, existing visuals, pending decisions, recommendations, and risk. | Adapt session/agent status and artifact display. Preserve all pending user decisions, even older ones. |
| [ketchup-video][ketchup-video] | Produces a silent subtitled video catch-up from real artifacts, with decisions left as text. | Adapt media output/embedding. No bundled video renderer exists; a capable renderer and verification of frames/hold durations are required. Preserve ordinary catch-up when media is unavailable, with the limitation stated. |
| [blast-radius][blast-radius] | Finds downstream effects beyond symbol references and runs a proof of the key safety assumption. | Portable with git/source/runtime tools. Optional Arena for wide scope; preserve proven versus unproven findings. |
| [architect][architect] | Grounds existing behavior, explores distinct type/module designs through Arena, synthesizes a usage-first sketch and rationale, then implements or scraps the shape. | Adapt delegation. Preserve the opt-in human checkpoint and full runner/rationale/red-flag references. |
| [arena][arena] | Parallel same-task candidates, rubric, independent cross-family judge, base selection, grafting, and verification. | Adapt model seats and isolated output paths/worktrees. A single available family cannot satisfy the independent cross-family judge; report that loss. |
| [swarm][swarm] | Parallel partition coverage or races, with declared first-pass/rank-all/best-of selection and one aggregate report. | Adapt cloud/background spawn. Preserve exact SHAs, measurement method, independent outputs, dropout gaps, and retry once for missing receipts. |
| [interrogate][interrogate] | Adversarial multi-model review of a diff or design; keeps only findings reproduced against intent. | Adapt role agents and worktrees, including uncommitted changes. Preserve all verified findings rather than selecting one reviewer. Reports findings; it does not apply fixes. |
| [automate-me][automate-me] | Mines recurring preferences, interviews the user, and drafts or revises a personal mode skill. | Adapt workspace session mining, `create-skill`, and output paths. This is portable personalization, not Cursor Automations. Preserve manual/explicit invocation and user iteration. |
| [make-bot-ui][make-bot-ui] | Builds a page/server that wakes a Grok Bot using a Cursor webhook routine, secret handoff, and Tailscale exposure. | Exclude the end-to-end integration. It relies on `update_state`, `SendToUser`, Cursor routine UI, `api2.cursor.sh`, and routine wake events. A different webhook backend would be new functionality, not an existing portable implementation. |
| [reflect][reflect] | Three transcript-review lenses, synthesis into accepted/rejected/backlog findings, and approved edits to skills. | Adapt session evidence, models, authoring support, cache paths, and tracker access. Preserve explicit approval before accepted edits and never edit a package cache. |
| [correct][correct] | Groups repeated mistakes and eliminates them with architecture, types, lint/CI, then tests; documents unenforced judgment rules last. | Portable. Keep evidence of recurrence, one change per class, and proving a check fails on a past mistake. |
| [teach][teach] | Combines How and Why into a plain progressive explanation, with diagrams or spatial illustrations. | Adapt diagram/image-generation and display tools. Preserve Why’s confidence language. Image generation is a host capability, not bundled pstack code. |
| [tdd][tdd] | Writes a cheap failing regression first, fixes it, and shows passing-after evidence. | Portable. Preserve conditional use and executable alternatives when a new test would be expensive or brittle. |
| [benchmark-checklist][benchmark-checklist] | Audits limiter, production tuning, physical limits, errors, repeated runs, end-to-end relevance, and whether timed work actually ran. | Portable. Adapt OS-specific tools such as `nproc`, `pidstat`, and `strace` to the machine. Preserve the ballpark exception and inconclusive results. |
| [no-comments][no-comments] | Uses Comment Sicko, audits findings, removes accepted comments/workarounds, and offers structural encodings of constraints. | Adapt named review agent. Preserve scope, exceptions, rejection/rerun limits, and the approval boundary for constraint encodings. |
| [typescript-best-practices][typescript-best-practices] | Type-system rules, schema-derived types, discriminated unions, branded values, exhaustive handling, and examples. | Portable. Preserve `references/patterns.md`; Cursor `paths` metadata does not establish an OpenCode file-trigger mechanism. |
| [figure-it-out][figure-it-out] | Designs a bespoke falsifiable workflow for ambitious work, with verification first, hypothesis loops, atomic units, and an audit trail. | Portable with adapted agents. Preserve the framing checkpoint for a multi-hour run and truthful verification states. |
| [show-me-your-work][show-me-your-work] | Maintains an append-only TSV decision log, audits it against the session, and requests independent cross-family scrutiny. | Adapt transcript evidence and reviewer role. Preserve `log.sh`, six-column format, run-boundary rows, superseding corrections, and the Attention report. |
| [create-verification-skill][create-verification-skill] | Creates and executes a project-local app control skill with launch, doctor, drive, evidence, cleanup, helpers, and a feature map. | Adapt `.cursor/skills/` to the selected skill root. Preserve real selectors/commands, instance isolation, evidence after cleanup, and a full first proof. |
| [maintain-verification-skill][maintain-verification-skill] | Checks every mapped feature from source and live behavior, and ships at most one correction PR. | Adapt discovery/agents. Preserve one coordinator driving the app, product-code exclusion, and clean/changed/blocked outcomes. |
| [create-formal-verification-skill][create-formal-verification-skill] | Chooses a costly failure property and a suitable formal/code-level tool; produces a rerunnable project skill and proves it detects a broken variant. | Adapt output paths/tools. Retain code links, scope/bounds, sync commit, and counterexamples. TLA+ checks route to Statechart. |
| [maintain-formal-verification-skill][maintain-formal-verification-skill] | Diffs covered code since its sync commit, updates verification, and distinguishes model drift from product bugs. | Portable with adapted discovery. Never advance a blocked sync commit, weaken a property to pass, or silently change product code. |
| [statechart][statechart] | Runs TLA+/TLC, writes readable Mermaid states, marks rule failures, and supplies shortest counterexample paths. | Portable utility plus skill. Keep the complete TypeScript tree, runtime launcher, bounded-check semantics, optional view module, and Pele rendering recipe. |
| [unslop][unslop] | Edits prose to remove vague, repetitive, artificial, or hard-to-read patterns. | Portable. Retain stable rule numbers referenced by other skills. |
| [bro][bro] | Restates the previous response simply and concisely. | Portable. Prompt-only. |
| [technical-writing][technical-writing] | Applies Diátaxis, developer style, STE, and Global English to technical prose, PR descriptions, and commit bodies. | Portable. Preserve the distinction between document structure and the sentence rules applicable to PRs/commits. |

### Principle skills: 24

All 24 are portable behavioral instructions. Preserve each leaf and its exact identifier, since the coordinator and other skills refer to it. Tool-dependent examples must use the adapter. The principle name alone is not a substitute for reading the leaf.

| Skill and source | Rule |
| --- | --- |
| [principle-attack-the-premise][principle-attack-the-premise] | After repeated failures under one assumption, test that assumption directly. |
| [principle-boundary-discipline][principle-boundary-discipline] | Validate at external boundaries; keep typed internal logic and pure business functions. |
| [principle-build-the-lever][principle-build-the-lever] | Build a rerunnable tool that performs or proves substantial work. |
| [principle-encode-lessons-in-structure][principle-encode-lessons-in-structure] | Encode recurring instructions as checks, types, metadata, or tools. |
| [principle-exhaust-the-design-space][principle-exhaust-the-design-space] | Compare structurally distinct prototypes before novel design decisions. |
| [principle-experience-first][principle-experience-first] | Prefer a polished user experience when scope and implementation convenience compete. |
| [principle-explain-the-number][principle-explain-the-number] | Find the limiter and validate the measurement before trusting a result. |
| [principle-fix-root-causes][principle-fix-root-causes] | Trace a symptom to the first incorrect state and fix the mechanism. |
| [principle-foundational-thinking][principle-foundational-thinking] | Choose the core data structures and shared-state model before downstream logic. |
| [principle-guard-the-context-window][principle-guard-the-context-window] | Keep bulk evidence out of the coordinator and retain bounded summaries. |
| [principle-laziness-protocol][principle-laziness-protocol] | Prefer deletion and the smallest useful change over abstractions and indirection. |
| [principle-make-operations-idempotent][principle-make-operations-idempotent] | Make lifecycle and retry operations converge after crashes or partial completion. |
| [principle-migrate-callers-then-delete-legacy-apis][principle-migrate-callers-then-delete-legacy-apis] | Move callers and remove the old internal API in the same work wave. |
| [principle-minimize-reader-load][principle-minimize-reader-load] | Reduce layers, hidden state, and unnecessary wrappers. |
| [principle-model-the-domain][principle-model-the-domain] | Represent states and invariants structurally rather than through scattered conditions. |
| [principle-never-block-on-the-human][principle-never-block-on-the-human] | Proceed with authorized reversible work without unnecessary permission questions. |
| [principle-outcome-oriented-execution][principle-outcome-oriented-execution] | Converge on the target design instead of building temporary compatibility layers. |
| [principle-prove-it-works][principle-prove-it-works] | Inspect and execute the actual artifact before declaring success. |
| [principle-redesign-from-first-principles][principle-redesign-from-first-principles] | Integrate new constraints as if they were present in the original design. |
| [principle-separate-before-serializing-shared-state][principle-separate-before-serializing-shared-state] | Eliminate shared writers before introducing serialization. |
| [principle-sequence-verifiable-units][principle-sequence-verifiable-units] | Deliver small ordered units, each with its own check. |
| [principle-subtract-before-you-add][principle-subtract-before-you-add] | Remove dead and redundant code before extending the design. |
| [principle-test-behavior-not-implementation][principle-test-behavior-not-implementation] | Check observable behavior without binding tests to incidental structure. |
| [principle-type-system-discipline][principle-type-system-discipline] | Make illegal states unrepresentable and derive types from authoritative schemas. |

## All 23 poteto-mode playbooks

These are routed reference files inside the coordinator skill, not 23 additional registered skills. Preserve them as readable files; optional explicit playbook selection can route through the same coordinator. Dependencies below supplement the common adapter.

| Playbook and source | Capability | Portability work |
| --- | --- | --- |
| [playbook-investigation][playbook-investigation] | Read-only grounded answers and design questions. | How/Why, source citations, and read-only tool policy. |
| [playbook-bug-fix][playbook-bug-fix] | Reproduce, eliminate hypotheses, prove the mechanism, fix, and repeat the original surface check. | Replace long-hunt `/loop`; provide a real driver and profiler. |
| [playbook-perf-issue][playbook-perf-issue] | Baseline a measured slowdown, isolate its cause, improve it, and remeasure. | Runtime profiling and Benchmark Checklist; no Cursor requirement in the method. |
| [playbook-hillclimb][playbook-hillclimb] | Sustained one-metric optimization with frozen measurement, one hypothesis per attempt, and accepted-win commits. | Retain keep/revert discipline, decision trail, and real target predicate. |
| [playbook-runtime-forensics][playbook-runtime-forensics] | Diagnose a live leak, spin, or glitch using instrumentation. | Host profiler/control access. Diagnosis is its deliverable, not an implied fix. |
| [playbook-trace-forensics][playbook-trace-forensics] | Reduce a captured CPU, heap, trace, or spindump artifact to a source-grounded cause. | Appropriate artifact parser/profiler, with bulk parsing outside the coordinator. |
| [playbook-feature][playbook-feature] | Ground and design new behavior, plan independent work, delegate implementation, and verify. | Role agents, isolated writers, runtime driver, and PR flow. |
| [playbook-refactoring][playbook-refactoring] | Change structure while proving behavior remains equivalent. | Grounding, design, measured equivalence, and small ordered commits. |
| [playbook-prototype][playbook-prototype] | Build a cheap throwaway sketch to resolve a design or empirical question. | Scratch/output isolation and observable evidence; preserve disposal of the sketch. |
| [playbook-visual-parity][playbook-visual-parity] | Match implementations pixel for pixel through baseline screenshots and image diffs. | Real UI driver and image diff; replace `/loop` with an explicit bounded execution method. |
| [playbook-authoring-a-skill][playbook-authoring-a-skill] | Author or edit a discoverable, tested skill. | Replace Cursor built-in `create-skill` with documented authoring/validation instructions. |
| [playbook-eval][playbook-eval] | Blind candidates to evaluation, compare variants with a blinded judge, and verify file-reading behavior. | Sanitized directories, model-diverse workers, and actual session tool evidence. Self-report cannot replace transcripts. |
| [playbook-babysit][playbook-babysit] | Drive PRs/stacks toward merge-ready, or perform background, threads-only, or one-shot checks. | Keep GitHub watcher/optional Origin path. Replace Cursor loop wakeups and Bugbot initiation; ordinary existing bot review threads remain usable. |
| [playbook-shipping][playbook-shipping] | Independently verify each patch, then land the contiguous verified stack bottom-up. | Use `gh` or optional Origin. Replace cloud verifiers/loop; retain current-head verdicts, patch-id logic, and retarget/rebase rules. |
| [playbook-autonomous-run][playbook-autonomous-run] | Continue one long task to a falsifiable finish condition, with evidence and a trail. | Cursor `/loop` is not bundled. A durable scheduler/event bridge must be separately provided; a synchronous CLI invocation alone does not survive termination. |
| [playbook-orchestrate][playbook-orchestrate] | Coordinate a multi-day program with PR owners, sub-coordinators, independent verifiers, and supervision. | Replace Cursor Project tracker/store, cloud VMs, fork semantics, and event subscriptions. This playbook explicitly prohibits scripts/polling loops as its own coordination mechanism, so a polling-shell rewrite is a deliberate behavioral change. |
| [playbook-autopilot-full][playbook-autopilot-full] | Own independent PRs through build, code-ready verification, babysitting, and authorized merge. | Replace cloud owner lifecycle, audit `/loop`, and unavailable control/deslop integrations. Preserve fresh verification after material patch changes. |
| [playbook-autopilot-stack][playbook-autopilot-stack] | Apply autopilot ownership and verification, stopping before merge for operator review. | Same dependencies as autopilot-full, with the no-merge rule preserved in every resumed run. |
| [playbook-session-pickup][playbook-session-pickup] | Recover another run from its trail, inspect actual state, and verify inherited claims. | Use scoped OpenCode session exports/branches, not Cursor transcript paths or cloud URLs. |
| [playbook-pause-safely][playbook-pause-safely] | Checkpoint or back out the current unit, preserve work, and write a concrete resume handoff. | Portable using files/git/session identifiers. Pausing is an explicit request, not inactivity. |
| [playbook-multi-phase-plan][playbook-multi-phase-plan] | Create a program checklist, per-PR dependency/build/live/perf/review/merge gates, and evidence appendices. | Port the template and `check-plan.mjs` together. The validator contains Cursor `/loop 1h` and repository-path literals; copying only the prose will fail its checks. |
| [playbook-worktree-cleanup][playbook-worktree-cleanup] | Audit disk, worktrees, merge status, dirty work, PRs, and stale simulators before gated cleanup. | Keep git/PR audit; replace Cursor chat lookup and omit Cursor application caches. Xcode/simulator operations remain optional platform-specific work. |
| [playbook-opening-a-pr][playbook-opening-a-pr] | Produce small ordered commits and ready PRs, with conventional titles, a concise rationale, and stack-aware bases. | Use `gh` by default, optional Origin. Replace built-in PR tool and external deslop; preserve the distinction between opening a PR and authorization to merge. |

## Agents, utilities, documentation, and dormant integrations

### Both bundled agents

| Agent and source | Capability | Recommended mapping |
| --- | --- | --- |
| [poteto-agent][poteto-agent] | Delegate wrapper that reads poteto-mode and its principle index before work; it does not take over the parent’s coordinator role. | Install an OpenCode `mode: subagent` definition. Resolve its skill path from the managed installation, not `~/.cursor/plugins/` or a Cursor version manifest. Translate `is_background: true`; that frontmatter is not an OpenCode scheduling switch. Generate model-specific copies when a role needs a different model. |
| [comment-sicko][comment-sicko] | Scoped comment reviewer, exception list, suppression audit, and `MUST KILL` refactor flags. | Install a read-only `mode: subagent` definition and let No Comments own accepted edits. The agent says report-only; the calling skill nevertheless audits a report/diff. Prefer the stricter report-only boundary and have the parent edit. Read-only shell policy needs more than a prompt if enforcement matters. |

### Five utility entry points

| Utility and sources | Existing functionality | Dependencies and port notes |
| --- | --- | --- |
| [watch-pr launcher][watch-pr launcher], [watch-pr CLI][watch-pr CLI], [watch-pr GitHub client][watch-pr GitHub client], [utility bootstrap][utility bootstrap] | One GitHub PR, connected stack, or frozen queued stack; JSON/NDJSON or pretty output; one-shot `--status-only`, polling cadence/deadline/error budget, and merge-readiness verdicts. | Bun, `gh` authentication/network, and Commander 14.0.0. Bootstrap installs locked dependencies and restarts the command when needed. Preserve all watch-pr modules, package.json, and bun.lock together. It does not implement Origin support, and it does not itself supply Cursor’s wake mechanism. |
| [check-plan][check-plan] | Validates plan sections, checklist shape, per-PR verification blocks, and program rules with file/line errors. | Node and filesystem only. Several checks require upstream-specific text, `/loop 1h`, and `git show origin/main:` patterns. Change its assumptions with the adapted plan template and fixtures. |
| [worktree-audit][worktree-audit] | Inventories worktrees, sizes, ages, merge/remote/dirty/PR states, latest matching chat, and suggested cleanup buckets. | Bash, git, standard Unix tools, `jq`, `rg`, and `gh` or Origin when available. It can fetch the selected remote base; “audit” is not entirely network-free. Replace its hardcoded Cursor transcript scan; missing session data must stay unknown. It audits, rather than performing the playbook’s destructive cleanup. |
| [decision-log helper][decision-log helper] | Creates a TSV header and appends timestamped rows, sanitizing line separators and spreadsheet formula prefixes. | Bash, date, dirname, mkdir, and tr. Portable. Preserve append-only semantics and independent files for simultaneous writers. |
| [statechart launcher][statechart launcher], [statechart runtime][statechart runtime], [statechart rendering][statechart rendering] | Statechart’s full TLA+ runner/parser/graph pipeline. Writes chart/report and checker evidence; supports views, grouped/parallel states, bug marks, and shortest paths. | TypeScript-capable Node 22.18–22.x, Node 23.6+, Bun 1.1.5+, or Deno 2+. Uses `mise` to obtain pinned TLC 1.7.4 and Temurin 25, or supplied `TLA2TOOLS`/`JAVA` (Java 11+). Rendering recipe pins `pele@1.9.0` for SVG. Keep all imported modules. |

These are five utility commands across three skill-owned script trees. Internal TypeScript modules are supporting code, not separate end-user capabilities.

Statechart has important output limits. Above 500 model states it draws only violation paths, and writes no chart when no rule breaks. After the first violation, subsequent checking runs stop at 100,000 distinct states; unchecked rules remain unknown. Its CLI writes to a new or empty output folder and distinguishes a verified pass, a violated rule, and an execution failure. Preserve these distinctions in a dispatcher. Although its launcher selects several JavaScript runtimes, the implementation also uses `/bin/sh` and process-group cleanup, so native Windows portability is not established by runtime availability alone. Source: [statechart][statechart] and [Statechart CLI][Statechart CLI].

The upstream README also documents a repository-root generator, `scripts/generate-pstack-harness-trees.mjs`, for the generated Claude Code distribution under `harness/pstack/`. That is upstream distribution maintenance, not a sixth pstack runtime command. A Tabnine port needs its own reproducible transformation step, not the Claude-specific generated tree. See [upstream README][upstream README] and [Claude Code adapter][Claude Code adapter].

### Docs and supporting resources

Preserve the guide and rewrite host-specific installation, model setup, persistence, tool, and loop advice. The full guide consists of [guide index][guide index] plus these ten chapters:

- [01-setup][01-setup].
- [02-poteto-mode][02-poteto-mode].
- [03-understand][03-understand].
- [04-design][04-design].
- [05-build-and-clean][05-build-and-clean].
- [06-verify-and-ship][06-verify-and-ship].
- [07-overnight][07-overnight].
- [08-principles][08-principles].
- [09-make-it-yours][09-make-it-yours].
- [10-recipes-and-pitfalls][10-recipes-and-pitfalls].

The guide’s six JPEGs and the logo are explanatory/branding assets, not additional capabilities. Keep supporting references with their owning skill: Architect’s three design references; How’s explorer/explainer prompts; Why’s investigator, synthesizer, epistemics, source routing, and eight source examples (code archaeology, Linear, Notion, Slack, Datadog, Sentry, Databricks, incident postmortems); Reflect’s four review/synthesis prompts; Poteto Help’s prompting/recipes; TypeScript’s examples; verification feature-map examples; the decision-log TSV template; Statechart’s render recipe; and poteto-mode’s review-triage rubric. These resolve relative to their skill directory. The script trees’ tests/corpus are supporting validation material, not additional slash workflows. Sources are the [pinned skills tree](https://github.com/cursor/plugins/tree/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills) and the per-skill links above.

### Benny: inventory it, exclude its Cursor deployment

Benny is expressly dormant and outside slash discovery. Its capability is two cooperating Slack issue-report automations, configured through a third setup instruction. Preserve the distinction between these sources and normal installed skills. See [Benny README][Benny README] and [Benny intent][Benny intent].

| Dormant instruction and source | Capability and dependencies | Scope decision |
| --- | --- | --- |
| [setup-benny][setup-benny] | Merge the pack into a target repo, configure Slack/tracker/control/model/budget choices, enable pstack in `.cursor/settings.json`, and hand off two reviewed Cursor Automations via built-in `/automate`. | Exclude Cursor provisioning/editor flows. |
| [triage-issue-reports][triage-issue-reports] | Read report threads/attachments, classify and trace ownership, deduplicate tracker issues, and reply once in the original thread with a triage marker. | Portable reasoning exists, but the shipped automation/trigger/credentials are Cursor-bound. Do not install a replacement Slack bot implicitly. |
| [reproduce-and-fix-issues][reproduce-and-fix-issues] | Wait for trusted triage, respect existing ownership, verify possible prior fixes, reproduce twice through real UI, and optionally produce one bounded draft fix with before/after proof. | Exclude live automation. Its control adapter, feature-map example, existing-fix verification reference, configuration, routing example, and prompt templates remain documented source material. |

A separate future integration could reuse Benny’s thread invariants, duplicate/ownership gates, and evidence standards with a non-Cursor scheduler. That would need explicit Slack/tracker access, a host control adapter, trigger handling, state, and a credential contract. It is outside the request to omit Cursor features.

## Verified OpenCode discovery and execution contracts

The following table applies to the matching **V1.19.5** source. The official [skills](https://opencode.ai/docs/skills/), [commands](https://opencode.ai/docs/commands/), and [agents](https://opencode.ai/docs/agents/) pages describe the public interface. Pinned source resolves details or discrepancies.

| Area | Observed contract | Consequence for this port |
| --- | --- | --- |
| Native skill directories | Scans `{skill,skills}/**/SKILL.md` under config directories. Project `.opencode/skills/<name>/SKILL.md` and global `~/.config/opencode/skills/<name>/SKILL.md` are the documented forms. Config paths include global config, discovered project `.opencode` directories, and `OPENCODE_CONFIG_DIR` in addition. | Use plural `skills/`. Do not treat `OPENCODE_CONFIG_DIR` as a replacement for the ordinary global directory. Sources: [V1 skill loader][V1 skill loader] and [V1 config paths][V1 config paths]. |
| Compatible skill locations | `.agents/skills/**/SKILL.md` and `.claude/skills/**/SKILL.md`, both home and project ancestor scopes, subject to external-skill flags. Also supports configured `skills.paths` and `skills.urls`. | `.agents/skills` is a possible shared fallback, but it does not register agents/commands. Avoid duplicate installations under several discovery roots. Source: [V1 skill loader][V1 skill loader]. |
| Skill frontmatter and paths | The loader consumes `name`, optional `description`, location, and content. The public format is stricter about required description and names. V1 does not use Cursor `disable-model-invocation`, `paths`, `icon`, or `color` for invocation policy. | Preserve valid Agent Skills names/descriptions and relative resource trees. Rewrite paths used in the body and references. Preserve manual-only intent in the adapter/commands instead of assuming unknown frontmatter enforces it. Source: [V1 skill loader][V1 skill loader]. |
| Slash commands | Scans `{command,commands}/**/*.md`. Filename/path determines name; YAML plus body becomes command configuration/template. Configured commands take priority over same-named auto skill commands. | Prefer `.opencode/commands/<name>.md` or namespaced files under `commands/pstack/`. Preserve `$ARGUMENTS`, positional placeholders, and body references. Choose and document names consistently. Sources: [V1 command file loader][V1 command file loader] and [V1 command catalogue][V1 command catalogue]. |
| Command execution | Expands arguments, shell interpolation, and file references. With a subagent target, command execution becomes a subtask unless `subtask: false`; a primary agent is the direct conversational runner. | `poteto-mode` must target the primary coordinator and use `subtask: false`. It must not launch `poteto-agent` as a wrapper for the whole playbook. Sources: [V1 command execution][V1 command execution] and [poteto-mode][poteto-mode]. |
| Agent discovery/configuration | Scans `{agent,agents}/**/*.md`. Supported V1 fields include description, mode, model, variant, prompt, hidden, permission, and steps. Markdown body supplies the prompt. | Use plural `agents/` and valid V1 frontmatter. Remove Cursor `is_background`; unknown agent keys can become provider options, so merely leaving them in place is undesirable. Sources: [V1 agent file loader][V1 agent file loader] and [V1 agent schema][V1 agent schema]. |
| Primary versus subagent | `mode: primary` runs the user-facing coordinator; `mode: subagent` supplies task workers. The headless `--agent` path rejects a subagent as the direct primary runner and falls back. | Define `pstack` primary separately from `poteto-agent` and `comment-sicko` workers. Source: [V1 run CLI][V1 run CLI]. |
| Model routing | Task chooses its selected agent’s configured model, otherwise inherits the parent. Agent variant is separately supported. | Generate role/panel-seat agents with confirmed model IDs and supported variants. `auto`/`inherit-parent` means omit configured model, not pass those words as model IDs. Verify the resulting model/variant in actual child session evidence. Sources: [V1 task implementation][V1 task implementation], [V1 agent schema][V1 agent schema], and [V1 command execution][V1 command execution]. |
| Background and nesting | `background: true` requires `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true`; otherwise task calls are foreground. Default configured subagent depth is one, and child `task`/`todowrite` permissions are restricted unless configured. | Do not promise Cursor-style background/nested delegation from copied frontmatter. Discover these capabilities, configure only what the workflow needs, and expose a degraded synchronous mode when appropriate. Source: [V1 task implementation][V1 task implementation]. |
| Isolation | V1 task schema has no Cursor cloud/environment or worktree field and constructs a child session without a fresh VM request. | A separate git worktree/output directory is required for independent writers. A prompt that says “isolated” does not create isolation. Local worktrees do not replace VM/process/credential isolation. Source: [V1 task implementation][V1 task implementation]. |
| Headless execution | `run --command <name> <arguments>` dispatches a command; `--agent`, `--model`, `--format json`, file attachments, explicit session selection, and fork are available. | A script can launch native workflows through this interface. Capture structured events and session identifiers. Do not use `--continue` implicitly for parallel work. Source: [V1 run CLI][V1 run CLI]. |
| Session evidence | OpenCode exposes session listing/export and stores its own session records. It is not Cursor’s JSONL directory layout. | Build history-dependent features around explicit scoped session exports/API access. Keep an exact session/project mapping and tool-call evidence for eval/audit. Source: [V1 session CLI][V1 session CLI] and [V1 export CLI][V1 export CLI]. |

Tabnine’s own migration helper independently recommends the same plural directories, global/project destinations, and `debug paths`, `debug skill`, and `agent list` verification. It also confirms that the Tabnine wrapper’s config directory is additive. This is direct vendor evidence, not just an inference from OpenCode ancestry: [Tabnine migration helper][Tabnine migration helper] and [Tabnine migration mapping][Tabnine migration mapping].

### OpenCode V2 is a separate compatibility target

At the inspected HEAD, configuration loading moved to `packages/core/src/config/plugin/`. V2 has its own agent and command schemas/migration paths, skill parser, and a `subagent` tool with `agent`, `model`, `sessionID`, and `background` fields. Its parser understands `disable-model-invocation` as an autoinvocation signal. The V2 `run` handler differs from V1 and does not forward the same `--command` input shown in V1’s implementation. Do not build this Tabnine port against current HEAD merely because it is newer. Sources: [V2 package version][V2 package version], [V2 skill parser][V2 skill parser], [V2 command loader][V2 command loader], [V2 agent loader][V2 agent loader], [V2 subagent tool][V2 subagent tool], and [V2 run handler][V2 run handler].

## Recommended mapping and script contract

This section is a recommendation, not a claim that the repository already implements it.

### Ship an installable instruction package and a thin dispatcher

Use a pinned vendored pstack snapshot with a small explicit host adapter and deterministic transformed files. Preserve original MIT attribution and the upstream license. Preserve every portable skill, all 24 principles, all 23 playbooks with their host adaptations, both agents, relative references, utility dependencies, and useful guide chapters. Keep a machine-readable record of each source path, upstream commit, adaptation, and exclusion. The upstream license permits modification and redistribution with its notice retained: [pstack license][pstack license].

A reviewable script interface could provide these operations:

| Proposed script operation | Purpose |
| --- | --- |
| `pstack install --project <repo>` or `--global` | Install adapted skills, commands, and agents at verified discovery locations. Project scope is easiest to review and reproduce. Respect user-owned files, report conflicts, and support a dry-run. |
| `pstack list` | Print every capability and mark portable, adapted, externally dependent, or excluded, with its upstream source. |
| `pstack show <skill-or-playbook>` | Emit complete instructions with resolved resource locations so Tabnine can read them through its shell/read tools. This fallback makes the script usable even where native discovery differs. It must not claim that displaying instructions executed a workflow. |
| `pstack run <skill> -- <task>` | Invoke the verified Tabnine native command/primary agent. For the initial V1 target, use the supported `tabnine run --command <installed-name> <task>` route. Preserve argument boundaries, task exit/error events, and the session identifier. |
| `pstack doctor` | Report binary/bundle/OpenCode versions, discovery roots, installed catalogue, task/background/nesting support, model/variant availability, external tool availability, and any required dependency that is absent. |
| `pstack tool <name> ...` | Optional convenience forwarding to the five existing utilities, preserving their actual inputs, outputs, errors, and runtime requirements. |

Support both native discovery and explicit instruction reading. An installer alone cannot make Cursor-specific tool parameters valid, and a single generic prompt wrapper cannot preserve multi-model panels. Stable namespaced command names such as `/pstack/poteto-mode` reduce collisions; ordinary names such as `/poteto-mode` match upstream examples but may conflict. Pick one public convention rather than accidentally installing both through multiple roots. The command catalogue’s same-name priority should be used intentionally.

### Host adapter: exact substitutions and exclusions

| Upstream dependency | Tabnine/OpenCode mapping | Fidelity and boundary |
| --- | --- | --- |
| Cursor `Task` | Native V1 `task` with a discovered `subagent_type`; `generalPurpose` maps to a suitable configured worker such as `general` or a pstack role agent. | Translate only fields the running tool accepts. Role-specific agent configs carry models. |
| Cursor `run_in_background`, `resume`, attachments | Experimental `background`, `task_id`, and explicit path references in the prompt, where supported. | Fresh task by default. Resumption only for the upstream stateful exceptions. No automatic conversion into unsupported tool fields. |
| `readonly: true` | A dedicated reader/reviewer agent with denied edits and an appropriate shell policy; keep MCP reads needed by Why/Reflect. | `edit: deny` alone does not prevent arbitrary Bash writes. Cursor’s claim that read-only mode strips MCP is not an OpenCode rule. |
| Cloud agents and `cloud_base_branch` | Explicit local worktree/base SHA and output ownership; optionally an independently configured VM runner. | Exclude Cursor VM dashboards/lifecycle. A local worktree is a partial substitute with shared machine state. |
| `AskQuestion`, todo lists, Read/Grep/Glob/Shell | Native `question`, `todowrite`, `read`, `grep`, `glob`, and `bash`, as actually available. | Headless questions and permissions need a declared policy or an interactive run; never invent an answer. |
| `~/.cursor/rules/pstack-models.mdc` | A pstack-owned config file plus generated V1 agent definitions; load its role choices explicitly from the coordinator. | Do not add arbitrary top-level keys to `opencode.json`. Keep the setup flow/budgets/panel sizes, translating effort to available variants rather than editing slug suffixes. |
| Cursor built-in `create-skill` | A bundled host-neutral authoring/validation procedure or an installed equivalent. | It is an external dependency, not part of upstream pstack. Preserve explicit Reflect approvals and its separation of structural enforcement from prose edits. |
| `cursor-team-kit` `deslop` | Port/install a separately reviewed cleanup workflow or document a concrete available alternative. | `unslop` edits prose and is not an equivalent code-cleanup implementation. Do not silently omit the pre-commit gate. |
| `cursor-team-kit` `control-ui`, `control-cli` | Repo-provided verification skill, browser driver, PTY harness, HTTP probe, or platform control adapter. | Keep required live-proof gates and evidence. If unavailable, mark verification blocked or inconclusive. |
| MCP discovery via Cursor’s `mcps/` directory | Inspect the host’s enabled MCP/tool catalogue and actual schemas. | pstack bundles source playbooks, not those servers, credentials, or service entitlements. Preserve unavailable-category gaps. |
| Cursor transcript paths | Explicit OpenCode/Tabnine session IDs and scoped export/API retrieval. | Adapt all consumers, including Reflect reference prompts, Eval, Recall, Automate Me, Show Me Your Work, pickup, and worktree audit. |
| Custom Mode UI / Option+Enter | An opt-in primary `pstack` agent with persistent prompt and verified skill/config loading. | Remove Cursor keybinding claims. Test persistence across turns/compaction rather than assuming a command attachment persists. |
| Cursor built-in `/loop` | Retain the in-session hypothesis loop; for durable wakeups require a separate scheduler/event mechanism and checkpoint/resume contract. | Never list `/loop` as a shipped pstack command. Automatic background wakeups are unsupported until such a mechanism exists. Adapt plan validation as well as prose. |
| Cursor Project tracker/store and cloud fork | A documented file/session record and explicit owner/coordinator state, backed by a real host integration if supplied. | Do not invent an equivalent Project service. Report the reduced durability/supervision where absent. |
| Built-in PR tool, Bugbot/security review | `gh` is already upstream’s default; optional Origin is supported by the playbooks. Review existing bot comments as ordinary forge threads. | Exclude starting/configuring Cursor Bugbot or security-review services. Do not claim their absence is a clean independent review. |
| Cursor Automations, `/automate`, `update_state`, `SendToUser`, Grok Bot webhook | Exclude the integration, plus Make Bot UI’s Cursor backend and Benny’s live deployment. | Do not replace them with guessed endpoints, secret APIs, schedules, or implicit Slack posting. |
| Cursor caches in cleanup | Omit Cursor application-cache targets and transcript heuristics; retain portable worktree safety checks and optional Xcode tooling. | Unknown usage/history cannot become evidence that a worktree is abandoned. |
| Image generation, `/visualize`, video embedding | Use available image/media tools or export supported artifacts. | These are host capabilities referenced by teaching/catch-up workflows, not guaranteed bundled tools. Preserve a clear unsupported/degraded result. |

The upstream model configuration has 17 role entries: `feature, refactoring`; `bug-fix`; `perf-issue`; `hillclimb`; `judgment and prose`; `hardest tasks`; `how explorer`; `how explainer`; `why investigators`; `why synthesizer`; `reflect tooling`; `reflect judgment, divergent, synthesizer`; `arena runners`; `arena cross-judge pool`; `swarm workers`; `architect runners`; and `interrogate reviewers`. Generate one worker definition per configured role/seat when its model or permissions differ. The cross-judge pool is ordered selection for one judge, not a fan-out panel. Since Tabnine uses one provider prefix for all models, compare model families from real model identity, not from the `tabnine` provider string. Source: [setup-pstack][setup-pstack] and [arena][arena].

Apply pstack's autonomy instructions within the user's authorization and the running host's policies. Installing a workflow does not grant permission to post messages, merge, deploy, or bypass organization controls. Reflect's explicit edit approval and the playbooks' merge/irreversible-action gates still need to remain visible in interactive and headless use.

## Remaining Tabnine-specific assumptions and limits

| Question | Evidence established | What remains to verify on the user’s installation |
| --- | --- | --- |
| Which product/binary is present? | Vendor docs distinguish `tabnine` from `tabnine-legacy`; the public repository’s README still describes an older beta and executable name. | No `tabnine` executable was found on this research process’s PATH. Do not use the unrelated installed `opencode` as proof of Tabnine compatibility. Check the chosen binary, `install.json`, and actual OpenCode version. |
| Exact packaged version | The downloaded public 1.2.0 archive declares OpenCode 1.19.5. | Enterprise hosts may publish different bundles. Validate the installed version, not only `tabnine --version`, which reports the bundle. Vendor [install documentation](https://docs.tabnine.com/main/getting-started/tabnine-plugin-for-opencode/install.md) describes the install marker and version distinction. |
| Discovery and config precedence | Vendor migration instructions confirm global/project plural roots and additive wrapper configuration. Model docs place wrapper config under `~/.tabnine/opencode/config/` and describe its precedence. | Confirm effective roots with the running binary and preserve its provider/governance config. An installation into ordinary global roots may interact with an existing OpenCode install. |
| Multi-model/variant panels | Models must be org-enabled `tabnine/<key>` values; V1 role-agent model routing exists. | Available families, variants, nested/background permissions, and model inheritance must be measured in child sessions. If there is only one family, mark independent cross-family review unavailable. Never silently label repeated same-family seats as diverse. |
| Background and long-lived work | V1 has an experimental background task path; Cursor `/loop` is external to pstack. | Verify that the bundle exposes the flag/tool, that completions wake the correct parent, and that process/session shutdown behavior is acceptable. No evidence here establishes an included Tabnine durable scheduler or VM fleet. |
| Read-only MCP investigators | V1 has configurable agent permissions and registered MCP tools. | Tabnine governance may deny tools, MCP servers, or subprocesses. Verify a reader can query required sources without granting writes. |
| History completeness | OpenCode has session list/export interfaces. | Confirm workspace/time scoping, child session inclusion, complete tool-call/resource evidence, and access after restart. A user-supplied digest can support Reflect’s fallback, but cannot prove Eval file-reading behavior. |
| Headless interaction | Vendor documents `tabnine run`, `--command`, `--agent`, JSON output, and rejection of ask-first tools without a UI. | Check all required actions under actual org policy. Preserve the failure and return a truthful blocked result; do not blanket-enable permissions from an installer. |
| Runtime and media dependencies | Utility launchers and host-neutral workflows name concrete runtime/tool requirements. | Check Bun, Node/TypeScript execution, Java/TLC or mise, `gh` auth, optional Origin, UI/PTY control, image/media renderers, and platform tools as each workflow needs them. |

These unknowns do not justify removing portable capabilities from the inventory. They determine what the eventual script can claim as supported, conditionally supported, or blocked. “Installed” and “equivalent to Cursor” must remain distinct claims.

## Suggested implementation acceptance checks

These checks are for the implementation task; they were not run as part of this research.

1. Enumerate all 58 upstream registered skill IDs, two agents, 23 playbooks, five utility entry points, and three dormant automation instruction IDs. Account for every item as retained, adapted, or deliberately excluded, including Make Bot UI and Benny. Detect newly added upstream paths on update.
2. In a disposable target repository, verify native skill/command/agent discovery from project and global installs, argument handling, relative references, namespacing, and restart behavior with the actual Tabnine bundle. Include paths containing spaces and an existing user-owned config.
3. Trace one coordinator workflow through How/Architect/Arena and a worker. Verify the coordinator remains primary, workers use selected role models/variants, all required principles/resources are readable, and independent writers have real independent worktrees/output paths.
4. Verify explicit invocation policy. V1 ignores Cursor invocation metadata, so help/rewrite/Reflect actions must not run incidentally. Confirm selecting another primary agent exits pstack’s persistent mode.
5. Verify failure paths: unavailable model family, denied MCP, unavailable control driver, missing transcript evidence, unsupported background/nesting, and a permission prompt in headless execution. None may be reported as complete verification.
6. Run adapted upstream utility checks at their owning script tree. Check `check-plan.mjs` against the adapted template, `watch-pr --status-only` against fixture or authorized forge data, TSV escaping/append behavior, and a small passing/failing TLA+ example with preserved counterexample artifacts. Do not launch ongoing watchers merely to test installation.
7. Check that runnable instructions do not still direct the user to Cursor install commands, `.mdc` rules, transcript directories, Custom Mode shortcuts, `/loop`, Automations, `SendToUser`, Cursor cache cleanup, or unsupported Task parameters. Historical references and explicit exclusion documentation can retain those names.
8. Review update/uninstall ownership and provenance. Preserve user edits, external tool/governance settings, license attribution, and any private verification artifacts. A pinned source revision plus a deterministic transform is easier to audit than untracked manual search-and-replace.

## Source links

Links above use pinned GitHub commits wherever source files are available. Tabnine product pages are current first-party documentation, and the public release archive is versioned. No secondary-source claim is used as compatibility evidence.

[Statechart CLI]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/statechart/scripts/statechart.ts
[01-setup]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/01-setup.md
[02-poteto-mode]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/02-poteto-mode.md
[03-understand]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/03-understand.md
[04-design]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/04-design.md
[05-build-and-clean]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/05-build-and-clean.md
[06-verify-and-ship]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/06-verify-and-ship.md
[07-overnight]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/07-overnight.md
[08-principles]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/08-principles.md
[09-make-it-yours]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/09-make-it-yours.md
[10-recipes-and-pitfalls]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/10-recipes-and-pitfalls.md
[Benny README]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/automations/benny/README.md
[Benny intent]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/automations/benny/FOR_AGENTS.md
[Claude Code adapter]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/harness/claude-code.md
[Cursor manifest]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/.cursor-plugin/plugin.json
[Tabnine migration helper]: https://github.com/codota/tabnine-opencode-public/blob/2bdafbd14e36a681074b27a3eb7f1a05d2e30940/migration_helper/README.md
[Tabnine migration mapping]: https://github.com/codota/tabnine-opencode-public/blob/2bdafbd14e36a681074b27a3eb7f1a05d2e30940/migration_helper/skills/migrate-from-tabnine-cli/references/mapping.md
[V1 agent file loader]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/config/agent.ts
[V1 agent schema]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/core/src/v1/config/agent.ts
[V1 command catalogue]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/command/index.ts
[V1 command execution]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/session/prompt.ts
[V1 command file loader]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/config/command.ts
[V1 config paths]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/config/paths.ts
[V1 export CLI]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/cli/cmd/export.ts
[V1 run CLI]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/cli/cmd/run.ts
[V1 session CLI]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/cli/cmd/session.ts
[V1 skill loader]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/skill/index.ts
[V1 task implementation]: https://github.com/anomalyco/opencode/blob/810c0eba1a7348036f8bdf61e6632d0c36c6876c/packages/opencode/src/tool/task.ts
[V2 agent loader]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/packages/core/src/config/plugin/agent.ts
[V2 command loader]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/packages/core/src/config/plugin/command.ts
[V2 package version]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/package.json
[V2 run handler]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/packages/cli/src/commands/handlers/run.ts
[V2 skill parser]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/packages/core/src/config/plugin/skill-file.ts
[V2 subagent tool]: https://github.com/anomalyco/opencode/blob/4f271bcd150a31d7e5e5430df9fe05e9046e131d/packages/core/src/tool/plugin/subagent.ts
[architect]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/architect/SKILL.md
[arena]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/arena/SKILL.md
[automate-me]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/automate-me/SKILL.md
[benchmark-checklist]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/benchmark-checklist/SKILL.md
[blast-radius]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/blast-radius/SKILL.md
[bro]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/bro/SKILL.md
[check-plan]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/check-plan.mjs
[comment-sicko]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/agents/comment-sicko.md
[correct]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/correct/SKILL.md
[create-formal-verification-skill]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/create-formal-verification-skill/SKILL.md
[create-verification-skill]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/create-verification-skill/SKILL.md
[decision-log helper]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/show-me-your-work/scripts/log.sh
[figure-it-out]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/figure-it-out/SKILL.md
[guide index]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/docs/guide/README.md
[how]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/how/SKILL.md
[in-your-own-words]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/in-your-own-words/SKILL.md
[interrogate]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/interrogate/SKILL.md
[ketchup]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/ketchup/SKILL.md
[ketchup-video]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/ketchup-video/SKILL.md
[maintain-formal-verification-skill]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/maintain-formal-verification-skill/SKILL.md
[maintain-verification-skill]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/maintain-verification-skill/SKILL.md
[make-bot-ui]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/make-bot-ui/SKILL.md
[manifest]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/plugin.json
[no-comments]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/no-comments/SKILL.md
[playbook-authoring-a-skill]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/authoring-a-skill.md
[playbook-autonomous-run]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/autonomous-run.md
[playbook-autopilot-full]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/autopilot-full.md
[playbook-autopilot-stack]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/autopilot-stack.md
[playbook-babysit]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/babysit.md
[playbook-bug-fix]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/bug-fix.md
[playbook-eval]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/eval.md
[playbook-feature]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/feature.md
[playbook-hillclimb]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/hillclimb.md
[playbook-investigation]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/investigation.md
[playbook-multi-phase-plan]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md
[playbook-opening-a-pr]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/opening-a-pr.md
[playbook-orchestrate]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/orchestrate.md
[playbook-pause-safely]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/pause-safely.md
[playbook-perf-issue]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/perf-issue.md
[playbook-prototype]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/prototype.md
[playbook-refactoring]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/refactoring.md
[playbook-runtime-forensics]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/runtime-forensics.md
[playbook-session-pickup]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/session-pickup.md
[playbook-shipping]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/shipping.md
[playbook-trace-forensics]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/trace-forensics.md
[playbook-visual-parity]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/visual-parity.md
[playbook-worktree-cleanup]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/playbooks/worktree-cleanup.md
[poteto help]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-help/SKILL.md
[poteto-agent]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/agents/poteto-agent.md
[poteto-help]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-help/SKILL.md
[poteto-mode]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/SKILL.md
[principle-attack-the-premise]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-attack-the-premise/SKILL.md
[principle-boundary-discipline]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-boundary-discipline/SKILL.md
[principle-build-the-lever]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-build-the-lever/SKILL.md
[principle-encode-lessons-in-structure]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-encode-lessons-in-structure/SKILL.md
[principle-exhaust-the-design-space]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-exhaust-the-design-space/SKILL.md
[principle-experience-first]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-experience-first/SKILL.md
[principle-explain-the-number]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-explain-the-number/SKILL.md
[principle-fix-root-causes]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-fix-root-causes/SKILL.md
[principle-foundational-thinking]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-foundational-thinking/SKILL.md
[principle-guard-the-context-window]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-guard-the-context-window/SKILL.md
[principle-laziness-protocol]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-laziness-protocol/SKILL.md
[principle-make-operations-idempotent]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-make-operations-idempotent/SKILL.md
[principle-migrate-callers-then-delete-legacy-apis]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md
[principle-minimize-reader-load]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-minimize-reader-load/SKILL.md
[principle-model-the-domain]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-model-the-domain/SKILL.md
[principle-never-block-on-the-human]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-never-block-on-the-human/SKILL.md
[principle-outcome-oriented-execution]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-outcome-oriented-execution/SKILL.md
[principle-prove-it-works]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-prove-it-works/SKILL.md
[principle-redesign-from-first-principles]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-redesign-from-first-principles/SKILL.md
[principle-separate-before-serializing-shared-state]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md
[principle-sequence-verifiable-units]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-sequence-verifiable-units/SKILL.md
[principle-subtract-before-you-add]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-subtract-before-you-add/SKILL.md
[principle-test-behavior-not-implementation]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-test-behavior-not-implementation/SKILL.md
[principle-type-system-discipline]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/principle-type-system-discipline/SKILL.md
[pstack license]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/LICENSE
[recall]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/recall/SKILL.md
[reflect]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/reflect/SKILL.md
[reproduce-and-fix-issues]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md
[setup-benny]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/automations/benny/skills/setup-benny/SKILL.md
[setup-pstack]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/setup-pstack/SKILL.md
[sharpen]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/sharpen/SKILL.md
[show-me-your-work]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/show-me-your-work/SKILL.md
[statechart]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/statechart/SKILL.md
[statechart launcher]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/statechart/scripts/statechart
[statechart rendering]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/statechart/references/render.md
[statechart runtime]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/statechart/scripts/run.ts
[swarm]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/swarm/SKILL.md
[tdd]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/tdd/SKILL.md
[teach]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/teach/SKILL.md
[technical-writing]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/technical-writing/SKILL.md
[triage-issue-reports]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/automations/benny/skills/triage-issue-reports/SKILL.md
[typescript-best-practices]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/typescript-best-practices/SKILL.md
[unslop]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/unslop/SKILL.md
[upstream README]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/README.md
[utility bootstrap]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/bootstrap.ts
[watch-pr CLI]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts
[watch-pr GitHub client]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/watch-pr/github.ts
[watch-pr launcher]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/watch-pr/watch-pr
[why]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/why/SKILL.md
[worktree-audit]: https://github.com/cursor/plugins/blob/fd268b808c786469e6dd8c8d9db864d0de4d669e/pstack/skills/poteto-mode/scripts/worktree-audit.sh
