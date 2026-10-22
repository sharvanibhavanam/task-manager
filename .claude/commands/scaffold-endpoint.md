

\## Goal

Create or update an API endpoint using the resource name and HTTP method supplied in $ARGUMENTS.



Create or update:

\- Route: routes/api.py

\- Service: services/<resource>.py

\- Schema: schemas/<resource>.py



\## Context

\- The assignment references routes/tasks.py as the canonical pattern.

\- This repository uses routes/api.py instead, so follow its existing Flask route conventions.

\- Follow the architecture in services/tasks.py and services/users.py.

\- Use existing AppError subclasses from utils/errors.py.

\- Check existing endpoints before implementing anything.



\## Constraints

\- Do not put business logic inside route handlers.

\- Routes should validate requests, call service functions, and return HTTP responses.

\- Do not modify utils/errors.py, migrations/, or .env.

\- Do not modify unrelated files.

\- Preserve existing function signatures.

\- Do not duplicate existing endpoints.

\- Create schemas/ only if the new endpoint requires a schema file.

\- Do not change existing behavior unnecessarily.



\## Verification

Run pytest -q after implementation.

Test the endpoint with a valid request.

Verify that it returns the expected HTTP status code.

Report the pytest results and all files changed.
