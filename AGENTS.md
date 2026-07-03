# Agent Coding Rules and Workflow

## 1. Goal-Driven Execution

Define success criteria before starting. Loop until verified.

Transform tasks into verifiable goals:

"Add validation" → "Write tests for invalid inputs, then make them pass"
"Fix the bug" → "Write a test that reproduces it, then make it pass"
"Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

No features beyond what was asked.
No abstractions for single-use code.
No "flexibility" or "configurability" that wasn't requested.
No error handling for impossible scenarios.
If you write 200 lines and it could be 50, rewrite it.
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. No Speculative Refactoring

Don't touch code that isn't directly related to the task.
Don't rename things "for consistency" unless the task asks for it.
Don't add type annotations unless asked.
Don't rewrite modules to match patterns — match the existing pattern.
If old code is messy, keep it messy. Only change what's needed for the current task.

## 4. Agent Workflow: End-to-End Cycle

This project uses an agent-led development workflow. Follow this cycle for every task:

### 4.1 Request → Plan

1. Understand the request
2. State a brief plan with steps and verification criteria
3. Confirm the plan is correct before starting implementation

### 4.2 Create Worktree

```bash
git checkout -b feat/short-description
git worktree add /tmp/nextferry-feat-short-description feat/short-description
```

Work inside the worktree: `/tmp/nextferry-feat-short-description`. This keeps the main repo clean and allows parallel sessions.

### 4.3 Prototype Frontend (if UI changes)

Write HTML to `prototypes/` directory first. This lets changes be reviewed before touching templates.

```bash
prototypes/my-feature.html   # Full HTML draft
prototypes/my-feature.css    # CSS additions (if any)
```

Once approved, move to `templates/` or `static/`.

### 4.4 Implement Code

- Write minimal code that solves the problem
- Follow existing patterns in the codebase (check similar files)
- Use `uv` for all package management — never pip

### 4.5 Run Local Verification

```bash
# From the worktree:
uv run ruff format . && uv run ruff check . && uv run mypy backend/ && uv run pytest tests/ -v
```

Or use the convenience script:
```bash
./scripts/agent-check.sh
```

For frontend changes, start the app and test in a browser:
```bash
# With replay mode (no live API needed):
NEXTFERRY_SCENARIO=scenarios/test.json uvicorn backend.main:app --reload

# With live API:
uvicorn backend.main:app --reload
```

### 4.6 Review Changes

Before creating a PR:
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Lint passes (`uv run ruff check .`)
- [ ] Format is correct (`uv run ruff format --check .`)
- [ ] Types check (`uv run mypy backend/`)
- [ ] No unintended changes to unrelated files
- [ ] Frontend changes look correct in browser (if applicable)

### 4.7 Commit and PR

```bash
git add . && git commit -m "feat: brief description"
git push origin feat/short-description
gh pr create --base main --title "feat: brief description" --body ""
```

---

## Commands Reference

```bash
# Install dependencies
uv sync

# Run dev server (auto-reload)
uvicorn backend.main:app --reload

# Run with replay mode (no live API)
NEXTFERRY_SCENARIO=scenarios/test.json uvicorn backend.main:app --reload

# Run all tests
uv run pytest tests/ -v

# Run a single test
uv run pytest tests/test_next_sailings.py::test_function_name -v

# Run delay integration tests (replay mode, no API key needed)
uv run pytest tests/test_delay_integration.py -v

# Lint and format
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy backend/

# Full pre-commit check
./scripts/agent-check.sh
```
