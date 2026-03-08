# Project Rules

## Documentation
* Every new feature or functionality must be documented in `README.md` under an appropriate header.
* Use f-strings whenever possible
* Make sure that README.md is always up to date with the present code. Make sure that the documentation is conscise. Provide small examples and rationale whenever possible. 
* Complete all TODOs that you see in code. They are denoted by #TODO.

## Dependencies
- Never add a new dependency without first checking if the required functionality is already available via existing imports in the codebase.
- If a new dependency is genuinely needed, verify it is not already present in `pyproject.toml` before adding it.
- Make the appropriate database schema/table modifications whenever necessary. All db init stuff needs to happen at db startup. 