$ErrorActionPreference = "Stop"

$env:REFERRAL_CODE_SECRET="test-secret-for-local-tests"
$env:ADMIN_API_KEY="test-admin-key"
$env:PARTNER_API_KEY="test-partner-key"
$env:WORKER_SECRET="test-worker-secret"
$env:APP_TENANT_DEFAULT="DEFAULT"
$env:APP_ENV="test"

Write-Host "Running format/lint checks..." -ForegroundColor Cyan
python -m ruff check .

Write-Host "Running non-E2E tests with coverage..." -ForegroundColor Cyan
python -m pytest test -v -m "not e2e" --cov=services --cov=apps --cov-report=term-missing

Write-Host "Running full test suite..." -ForegroundColor Cyan
python -m pytest test -v

Write-Host "All checks completed." -ForegroundColor Green