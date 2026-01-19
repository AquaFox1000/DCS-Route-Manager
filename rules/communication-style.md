---
trigger: always_on
---

*   **Environment:** This runs inside a flight simulator (DCS World). Performance is PARAMOUNT.
*   **Memory:* Eliminate memory leaks. Dereference unused objects.
*   **Efficiency:** Avoid expensive loops in `Update()` functions. Use event-driven logic where possible.
*   **Context:** Remember that Lua runs in a specific DCS environment (Export.lua, Hooks).

## 6. COMMUNICATION STYLE
* **Manager Mode:** Keep the "Agent Management Window" open.
* **Concise:** Do not explain the code unless asked. State the action: "Index updated. Waiting for testing."