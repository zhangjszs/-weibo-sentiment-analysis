# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready`              | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

The active issue lifecycle is `ready / in-progress / in-review / blocked / needs-info / done` (single vocabulary, one lifecycle label per issue; priority is `priority:P0`–`priority:P4`). The old `ready-for-agent` label is retired — do not apply it; the agent-ready role is spelled `ready`.

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.
