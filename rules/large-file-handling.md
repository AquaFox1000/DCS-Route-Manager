---
trigger: always_on
---

* **Context Awareness:** The project contains large files (>5000 lines).
* **Read Before Write:** Before writing ANY code, you must scan the file for existing:
    * Global variables (do not create duplicates like `alt` if `altitude` exists).
    * Event Listeners (do not add a second `update` listener; hook into the existing one).
* **Refactor vs. Create:** Prefer modifying existing functions over creating new helper functions.
* **Verification:** If you propose a new variable, you must list 3 similar existing variables and justify why they cannot be used.