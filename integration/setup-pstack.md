---
name: setup-pstack
description: Configure pstack role models and provider reasoning variants for Tabnine CLI or OpenCode.
---

# Configure pstack

Read `@@CONFIG_DIR@@/pstack/harness.md`, including the role table, before changing models.

1. Discover models with the host's model-list command (`tabnine models`). Inspect the host's provider configuration for supported reasoning variants. A model ID uses `provider/model`; Tabnine exposes organization-enabled `tabnine/<key>` models. A variant is a separate agent field. Offer the upstream budgets `unlimited — max reasoning`, `large — xhigh reasoning`, `medium — high reasoning`, and `small — medium reasoning`. Map the chosen target to supported variants; if a provider lacks the target, show its actual options rather than inventing a slug. Keep `inherit-parent` when no override is wanted. Offer independent models for the Arena, Architect, and Interrogate panels when available.
2. Read `@@CONFIG_DIR@@/pstack/models.json`. Its `roles` object maps each role from the harness table to a model string, an object such as `{"model": "provider/model", "variant": "high"}`, or a list of those entries for a panel. Panel order and length determine seats. Single-worker roles accept exactly one entry. Confirm real IDs and variants against what the host actually supports before writing them. Avoid changing provider credentials or global permissions.
3. Write the chosen configuration to a temporary JSON file, then run the following through the shell with correctly quoted paths. The configure command validates the file and updates managed agents and the harness without downloading upstream. Resolve the actual CLI executable for model discovery separately; this command is Python.

   ```sh
   @@PYTHON_COMMAND@@ '@@CONFIG_DIR@@/pstack/integration/integrate.py' configure --config-dir '@@CONFIG_DIR@@' --models '<temporary-json-file>'
   ```

4. Confirm the updated role table and the exact files changed. On Windows, use `python` if the `py` launcher is unavailable. Tell the user to restart the host to reload agent definitions. If configuration fails due to an edited managed file, show the conflict and preserve the edit; `--force` backs up conflicts before replacing them.
5. If the project has no real-app verification harness, offer `create-verification-skill`. If it lacks formal verification for a property worth proving, offer `create-formal-verification-skill`. These offers are optional and do not block setup.
