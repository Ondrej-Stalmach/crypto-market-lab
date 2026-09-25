# Repository Instructions for AI Assistants

- Read [docs/architecture.md](docs/architecture.md) before changing the workspace layout, package boundaries, or dependency model.
- Use `uv` for dependency management and project execution. Do not use raw `pip` or manual virtual-environment activation.
- Keep exchange-specific source in its matching `packages/<exchange>/src/` package and tests in that package's `tests/` directory.
- Declare internal package dependencies as `uv` workspace dependencies, including a `[tool.uv.sources]` entry with `workspace = true`.
- Keep the `.python-version` pin at Python 3.12 and preserve the root and connector `requires-python` constraints at `>=3.12` unless the compatibility target is intentionally changed.
- Treat `docs/architecture.md` as the current structure; do not add planned packages or technologies to it until they exist in the repository.