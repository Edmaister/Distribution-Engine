# Testing & Coverage

## Quick Start

```bash
pip install -r requirements.txt
pytest
```

- `pytest.ini` sets defaults: quiet output, warnings suppressed, and coverage for `services/`, `apps/`, and `utils/`.
- `.coveragerc` controls the coverage run and report.
- Markers:
  - `@pytest.mark.unit`
  - `@pytest.mark.integration` (deselect via `-m "not integration"`)

## Examples

Run only unit tests:

```bash
pytest -m unit
```

Skip integration tests:

```bash
pytest -m "not integration"
```

Show full coverage report:

```bash
pytest --cov=services --cov=apps --cov=utils --cov-report=term-missing
```

Check migration hygiene:

```bash
python scripts/check_migrations.py
python scripts/check_distribution_migrations.py
```

Check release readiness gates:

```bash
python scripts/readiness_progress.py
python -m pytest test/test_data_quality_service.py test/test_core_role_journey_smoke.py -q
```

Build the frontend:

```bash
cd frontend
npm ci
npm run lint
npm test
npm run smoke
npm run build
```

`npm run lint` is currently calibrated as a managed baseline gate: it fails on
syntax/configuration errors and also fails if the warning count rises above the
documented ceiling. See [frontend lint baseline](FRONTEND_LINT_BASELINE.md).

Review [front-to-back referral coverage](FRONT_TO_BACK_TEST_CASES.md) to decide which tests belong at frontend smoke, API contract, service, integration, or full journey level.

Live operational smoke checks are documented in the
[production runbook](PRODUCTION_RUNBOOK.md). The core role smoke is read-only by
default and covers consumer, producer, distributor, and admin workspace access.

## CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml`. It checks migration hygiene, runs backend tests, exports `coverage.xml`, installs frontend dependencies, and builds the frontend.

Optionally set `CODECOV_TOKEN` in repository variables to upload coverage to Codecov.
