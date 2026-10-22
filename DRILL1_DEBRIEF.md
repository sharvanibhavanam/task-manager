\# Drill 1 — Debrief



\*\*Q1. What did you change between v1 and v2, and which prompt part did the change belong to?\*\*



I improved the Constraints and Verification sections. In v2, I added a rule preventing Claude from modifying files outside the specified target and told it to skip functions that already follow the AppError pattern. I also changed Verification to require running `pytest -q` after every updated function instead of only at the end.



\*\*Q2. What is the practical difference between putting this prompt in CLAUDE.md versus in a slash command?\*\*



CLAUDE.md provides project-wide instructions that apply throughout the session. A slash command runs only when I explicitly invoke it. Slash commands are better for recurring tasks because they keep CLAUDE.md concise, support `$ARGUMENTS` for different files, and allow the same workflow to be reused without rewriting the prompt.



\*\*Q3. When you ran the command against services/users.py, did Claude behave correctly? What does that reveal about your Constraints section?\*\*



Claude found that `create\_user()` did not properly handle non-string inputs and updated it to raise `ValidationError`. It left the other five functions unchanged because they already followed the AppError pattern. This showed that the Constraints section helped Claude avoid unnecessary changes while still fixing actual error-handling problems. All 280 tests passed after the update.
