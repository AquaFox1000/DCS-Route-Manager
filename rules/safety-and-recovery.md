---
trigger: always_on
---

* **Pre-Flight:** Run `npm run agent-save` immediately after user approval (or before major changes), BEFORE writing code.
* **Emergency:** If the user indicates "Broken", "Error", or "Undo", immediately stop and run `npm run agent-undo`.
* **backup directory**: `_DevOps/behavior/backups/`. save the previous version of the code before making any changes. use `npm run agent-save` to save the code.
* **Diary Updates**: Before running `npm run agent-save`, you MUST append a summary to `_DevOps/behavior/project_diary.md`.
    *   **Format**: Use the format: `### [Date/Time] Task Name`.
    *   **Tags**: You MUST include a line `**Tags**: #keyword1 #keyword2 ...` to make it searchable (e.g., `#ui`, `#fix`, `#map`, `#pointer`).
*   **Diary Indexing**: `_DevOps/behavior/project_diary.md` is the source of truth for project history.