# Set up pstack

From the pstack-tabnine checkout, run `@@PYTHON_COMMAND@@ integrate.py install`. On Windows, use `python` if the `py` launcher is unavailable. The default destination is Tabnine's `~/.tabnine/opencode/config` (`%USERPROFILE%\.tabnine\opencode\config` on Windows); use `--config-dir` for another root or `--client opencode` for standalone OpenCode. Restart the host after installation.

Start with the host CLI, Git, and Python 3.10+; Git Bash supplies Bash on Windows. Add other tools only when a selected workflow needs them, following the harness adapter's **Workflow dependencies** guidance.

## Pick models

Run `/pstack-setup-pstack`. It discovers the host's available models, asks for a reasoning budget and role choices, validates them, and updates `@@CONFIG_DIR@@/pstack/models.json` and the named role agents. Restart the host to reload them.

Defaults inherit the session model. `auto` and `inherit-parent` mean the same thing. Panel lists set the number of independent seats; two seats on one model do not provide model diversity. The Arena cross-judge pool selects one eligible judge from another model family. Tabnine's `tabnine/` provider prefix is shared across model families.

The budget choices are unlimited (target max), large (target xhigh), medium (target high), and small (target medium). Use only variants the chosen provider actually offers. To spend less, choose cheaper models, reduce panel seats, or reserve poteto-mode for tasks that need rigorous design and review.

## Add verification

Setup offers `/pstack-create-verification-skill` when the project lacks a real-app driver. It generates a project-local Agent Skill and proves the driver works. Accept or decline; the offer does not block setup.

It also offers `/pstack-create-formal-verification-skill` when a costly failure property would benefit from formal checking. Use it for important invariants in concurrency, retries, protocols, state machines, and parsers. Checks state their scope and bounds. App drivers and formal tools must actually run before proof can be claimed.

## Start a task

```text
/pstack-poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

This command selects the `pstack` primary coordinator. It matches a playbook, lists the steps, delegates where useful, and verifies the result. Follow up normally. Select another primary agent to leave the persistent engineering workflow.

Read [the harness adapter](../../harness.md) for tool mappings, optional dependencies, history exports, and excluded Cursor services. Continue with [routing work](02-poteto-mode.md).
