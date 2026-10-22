

\## Goal

Audit $ARGUMENTS for missing AppError handling. Replace raw exceptions with appropriate existing AppError subclasses from utils/errors.py.



\## Context

\- Follow the canonical error-handling pattern in services/users.py.

\- Use the existing AppError hierarchy in utils/errors.py.

\- Preserve the project's existing architecture.



\## Constraints

\- Do not modify utils/errors.py or any file outside $ARGUMENTS.

\- Do not add new AppError subclasses.

\- Preserve all existing function signatures.

\- Skip functions that already follow the correct AppError pattern.

\- Do not make unrelated changes.



\## Verification

Run pytest -q after every function you update. All existing tests must pass before moving to the next function. Report the final pytest output.
