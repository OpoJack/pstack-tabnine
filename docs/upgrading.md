# Updating pstack

## 0.15.36 to 0.15.43

Checked upstream on 2026-11-16. The latest commit changing `pstack/` was
[`2f87c854fe3e2fcda44ca86b46ede35aad3c46b7`](https://github.com/cursor/plugins/commit/2f87c854fe3e2fcda44ca86b46ede35aad3c46b7).
Both plugin manifests identify version **0.15.43**. The downloaded commit archive's
SHA-256 is recorded in `upstream.lock.json` and checked on every remote install.

The registered inventory remains 58 skills, of which 57 are installed.
`make-bot-ui` and the Cursor automation trees remain excluded. There are two
upstream agents and 22 playbooks, down from 23.

Changes relevant to this adapter:

- Poteto adds `worker.md`, which carries the operator's rules into every agent.
  The adapter and generated delegate prompts point to the installed file.
- How now uses one explorer/explainer. Why and Reflect no longer have investigator
  panels. Architect routes contested designs to Arena. Their old reference files
  and the Orchestrate playbook are removed upstream.
- The plan validator is removed. The adapter no longer lists it as a dependency.
- Upstream retires eight model roles: hardest tasks, How explorer and explainer,
  Why investigators and synthesizer, both Reflect roles, and Architect runners.
  Reinstallation drops these entries with a diagnostic and removes their managed
  agents. Choices and provider variants for the nine active roles stay intact.
  Default configuration now produces 15 agents instead of 24.
- Setup offers small, medium, and large budgets. Upstream Cursor model slugs
  remain overridden by the adapter's provider model configuration; the default
  remains session-model inheritance. Existing explicit provider variants stay
  unchanged during installation.
- Statechart's Mermaid renderer and several workflow and principle texts changed.
  Full resource trees are installed; script sources and test fixtures remain
  unmodified except for the existing scoped-transcript worktree-audit adaptation.

The original portability research in `research.md` describes **0.15.36** and is
historical. This audit records the inventory and mapping changes since then.

Validation used the actual old and new upstream trees in a temporary installation:
the upgrade preserved a custom model and reasoning variant, removed obsolete
managed files, installed `worker.md`, passed `doctor`, and made a second install
with identical bytes and modification times. The unit suite passed 16 tests; one direct-CLI test was skipped because Tabnine
is not installed globally. It covers role retirement, file removal, and preservation
of unrelated host configuration. The separate official Tabnine 1.2.0 sandbox run
passed all 12 subprocess checks with 57 commands, 57 skills, and 15 agents; see
[the report](tabnine-smoke-test.md).

## Installing the pinned update

Run from this checkout, using `py -3` on Windows or `python3` on macOS/Linux:

```sh
python3 integrate.py install --dry-run
python3 integrate.py install
python3 integrate.py doctor
```

Use the same `--client` and `--config-dir` as the original installation. Restart
the host after installation. Edited managed files are protected by the installer's
normal conflict checks; `--force` backs up conflicts before replacement.

## Updating the pin in future

There is no automatic latest-version updater. The installer always uses the lock.
To prepare another update:

1. Find the newest upstream commit affecting `pstack/`, download that commit's
   codeload archive, and compare both plugin manifests' version numbers.
2. Compare against the current pinned tree. Audit skill additions/removals,
   agents, roles, playbooks, helper scripts, and host-specific instructions.
3. Update the commit, version, SHA-256, skill count, and exclusions in the lock.
   Adjust adapter templates, role migration, examples, and this audit as needed.
4. Run `python3 -m unittest discover -s tests -v`, exercise an actual old-to-new
   install with custom models, and check `doctor` and reinstall idempotence.
5. On macOS, rerun `python3 scripts/smoke_tabnine.py --report
   docs/tabnine-smoke-test.json` and update the report's prose to match the evidence.

Inspect the file plan before applying the update to a real installation.
