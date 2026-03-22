# Branch Review - Branches Needing PRs

## Summary

6 branches have unmerged changes with no associated PRs. All branch off `main` at commit `851495a` ("Fix inconsistent departure direction ordering (#16)").

### Existing PRs
- PR #6 (open): `add-pytest-tests` -> main
- PR #16 (merged): `claude/fix-departure-ordering-yL1dZ` -> main

---

## Branches Needing PRs

### 1. `claude/fill-risk-predictor-yL1dZ`
**Title:** Add fill risk predictor for ferry capacity forecasting
**Files:** 5 changed, +510/-27
- New `backend/fill_predictor.py` (389 lines) - forecasting engine
- Updates to `backend/display_processing.py`, `backend/main.py`
- UI changes in `templates/next_sailings_fragment.html` and `static/style.css`

### 2. `claude/add-tests-ci-yL1dZ`
**Title:** Add test suite and GitHub Actions CI
**Files:** 7 changed, +579/-0
- New `.github/workflows/test.yml` CI pipeline
- New test suite: `tests/test_display_processing.py`, `tests/test_next_sailings.py`, `tests/test_serializers.py`, `tests/test_utils.py`
- Updated `pyproject.toml` with test dependency

### 3. `claude/drive-up-capacity-yL1dZ`
**Title:** Display drive-up vehicle capacity on each sailing
**Files:** 5 changed, +107/-3
- New `backend/sailing_space.py` for capacity data
- Updates to `backend/display_processing.py`, `backend/main.py`
- UI additions in template and CSS

### 4. `claude/remove-mobile-header-yL1dZ`
**Title:** Hide header on mobile to reclaim screen space
**Files:** 1 changed, +31/-18
- CSS-only change in `static/style.css`

### 5. `claude/api-key-to-header-yL1dZ`
**Title:** Move WSDOT API key from query params to request header
**Files:** 1 changed, +13/-7
- Security improvement in `backend/wsdot_client.py`

### 6. `claude/show-departed-sailings-yL1dZ`
**Title:** Show recently departed sailings with en-route status
**Files:** 6 changed, +58/-6
- Backend changes: `display_processing.py`, `next_sailings.py`, `serializers.py`, `utils.py`
- UI changes in template and CSS
