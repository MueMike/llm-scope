# GitHub Actions Workflows Documentation

This document provides a comprehensive overview of all GitHub Actions workflows configured for this project.

## 📋 Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
  - [CI Pipeline](#ci-pipeline)
  - [Release & Deploy](#release--deploy)
  - [Security Scanning](#security-scanning)
  - [Pull Request Validation](#pull-request-validation)
  - [Auto Merge](#auto-merge)
  - [Performance Benchmarks](#performance-benchmarks)
  - [Nightly Build](#nightly-build)
  - [Stale Management](#stale-management)
  - [Cleanup](#cleanup)
- [Configuration](#configuration)
- [Secrets Required](#secrets-required)
- [Best Practices](#best-practices)

---

## Overview

This project uses a comprehensive CI/CD pipeline built on GitHub Actions to ensure code quality, security, and reliable deployments. The pipeline includes:

- ✅ Automated testing and code quality checks
- 🔒 Security scanning and vulnerability detection
- 🚀 Automated releases and Docker image publishing
- 📊 Performance benchmarking
- 🤖 Automated dependency updates via Dependabot
- 🏷️ Automatic PR labeling and validation

---

## Workflows

### CI Pipeline

**File**: `.github/workflows/ci.yml`

**Triggers**:
- Push to main, master, develop, feature/*, fix/*, claude/* branches
- Pull requests to main, master, develop
- Manual trigger

**Jobs**:

#### 1. Code Quality
- **Black** formatting check
- **isort** import sorting check
- **flake8** linting
- **mypy** type checking

Matrix: Runs across different check types (formatting, linting, type-checking)

#### 2. Security Scanning
- **Bandit** security linter for Python code
- **Safety** check for known vulnerabilities
- **pip-audit** dependency vulnerability scanning

Generates security reports uploaded as artifacts.

#### 3. Unit Tests
- Runs on Python 3.11 and 3.12
- Full test suite with coverage
- Generates coverage reports (XML, HTML, terminal)
- Uploads to Codecov
- Uploads test results as artifacts

#### 4. Integration Tests
- Runs integration test suite
- Depends on code-quality and test jobs

#### 5. Docker Build
- Builds Docker image
- Uses BuildKit cache for faster builds
- Multi-platform support (amd64, arm64)

#### 6. CI Success Check
- Validates all jobs completed successfully
- Provides summary of results

**Artifacts**:
- `bandit-security-report`: Security scan results
- `test-results-{version}`: Test results and JUnit reports
- `coverage-report`: HTML coverage report

---

### Release & Deploy

**File**: `.github/workflows/release.yml`

**Triggers**:
- Push tags matching `v*.*.*`
- Published releases
- Manual trigger with version input

**Jobs**:

#### 1. Build and Test
- Runs full test suite
- Builds Python package
- Extracts version from tag
- Uploads build artifacts

#### 2. Docker Image Build & Push
- Multi-platform build (linux/amd64, linux/arm64)
- Pushes to GitHub Container Registry
- Optional: Pushes to Docker Hub
- Tags: version, major.minor, major, latest, SHA

#### 3. GitHub Release
- Creates GitHub release
- Generates changelog from commits
- Attaches build artifacts
- Marks pre-releases (alpha, beta, rc)

#### 4. PyPI Publishing (Optional)
- Publishes to PyPI for stable releases
- Uses trusted publishing (OIDC)
- Skips alpha/beta releases

**Required Secrets**:
- `GITHUB_TOKEN` (automatically provided)
- `DOCKERHUB_USERNAME` (optional)
- `DOCKERHUB_TOKEN` (optional)
- `PYPI_API_TOKEN` (optional, for PyPI publishing)

**Container Images**:
```bash
# GitHub Container Registry
ghcr.io/{owner}/{repo}:latest
ghcr.io/{owner}/{repo}:{version}
ghcr.io/{owner}/{repo}:{major}.{minor}

# Docker Hub (if configured)
{username}/litellm-proxy-langfuse:latest
```

---

### Security Scanning

**File**: `.github/workflows/security.yml`

**Triggers**:
- Push to main, master, develop
- Pull requests
- Weekly schedule (Monday 9 AM UTC)
- Manual trigger

**Jobs**:

#### 1. CodeQL Analysis
- Runs GitHub's CodeQL security scanner
- Uses security-extended queries
- Uploads results to Security tab

#### 2. Dependency Review
- Reviews dependency changes in PRs
- Fails on moderate+ severity vulnerabilities
- Blocks GPL-3.0 and AGPL-3.0 licenses

#### 3. Semgrep SAST
- Static application security testing
- Auto-configuration for Python
- Generates JSON report

#### 4. Secret Scanning
- Uses Gitleaks to detect secrets
- Scans entire git history
- Prevents accidental secret commits

#### 5. Trivy Container Scan
- Scans Docker images for vulnerabilities
- Reports CRITICAL and HIGH severity issues
- Uploads to GitHub Security tab (SARIF format)

#### 6. Python Security Audit
- **Bandit**: Python code security linter
- **Safety**: Known vulnerability database
- **pip-audit**: PyPI vulnerability scanner

#### 7. License Compliance
- Generates license report for all dependencies
- Outputs markdown and JSON formats

**Artifacts**:
- `semgrep-report`: SAST scan results
- `python-security-reports`: Bandit, Safety, pip-audit results
- `license-report`: Dependency license information

**Security Tab**:
Results are automatically uploaded to GitHub Security tab for:
- CodeQL findings
- Trivy container vulnerabilities
- Gitleaks secret detection

---

### Pull Request Validation

**File**: `.github/workflows/pr.yml`

**Triggers**:
- PR opened, synchronized, reopened, ready_for_review

**Jobs**:

#### 1. PR Validation
- Validates semantic PR title format
- Checks PR description length
- Enforces subject capitalization

**Supported PR Title Formats**:
```
feat: Add new feature
fix: Fix bug in proxy
docs: Update README
style: Format code
refactor: Refactor middleware
perf: Improve performance
test: Add tests
build: Update dependencies
ci: Update workflows
chore: Miscellaneous changes
```

**Scopes**: proxy, langfuse, middleware, config, tests, docker, ci, deps

#### 2. Auto Labeling
- Labels by PR size (xs, s, m, l, xl)
- Labels by files changed (area labels)
- Labels by branch name (type labels)

#### 3. Code Coverage
- Compares coverage with base branch
- Comments on PR with coverage changes
- Highlights coverage increases/decreases

#### 4. PR Summary Comment
- Posts automated summary comment
- Shows validation status
- Lists PR statistics
- Provides next steps

#### 5. Breaking Changes Detection
- Detects breaking changes in title/description
- Adds `breaking-change` label
- Warns reviewers

**Labels Applied**:
- Size: `size/xs`, `size/s`, `size/m`, `size/l`, `size/xl`
- Area: `area/proxy`, `area/tests`, `area/docker`, etc.
- Type: `type/bug`, `type/feature`, `type/refactor`
- Special: `breaking-change`, `dependencies`

---

### Auto Merge

**File**: `.github/workflows/auto-merge.yml`

**Triggers**:
- PR labeled, unlabeled, synchronized, etc.
- PR review submitted
- Check suite completed

**Jobs**:

#### 1. Auto Merge
- Merges PRs with `auto-merge` label
- Uses squash merge method
- Requires all checks to pass
- Retries up to 6 times

**Conditions**:
- Not a draft PR
- Has `auto-merge` label
- Does not have `work-in-progress` or `do-not-merge` labels
- All required checks pass

#### 2. Auto Approve Dependabot
- Automatically approves Dependabot PRs
- Adds `auto-merge` label for patch/minor updates
- Comments warning for major updates

**Usage**:
```bash
# Add label to PR to enable auto-merge
gh pr edit <number> --add-label "auto-merge"
```

---

### Performance Benchmarks

**File**: `.github/workflows/performance.yml`

**Triggers**:
- Push to main/master
- Pull requests
- Manual trigger

**Jobs**:

#### 1. Performance Benchmarks
- Runs pytest-benchmark tests
- Tracks performance over time
- Alerts on 150%+ regression

#### 2. Load Testing
- Starts Docker services
- Runs basic load test (100 concurrent requests)
- Collects and uploads logs

**Artifacts**:
- `load-test-logs`: Service logs from load testing

---

### Nightly Build

**File**: `.github/workflows/nightly.yml`

**Triggers**:
- Daily at 2 AM UTC
- Manual trigger

**Jobs**:

#### 1. Nightly Build & Test
- Runs on Python 3.11, 3.12, 3.13
- Comprehensive test suite
- Curl integration tests

#### 2. Dependency Check
- Lists outdated packages
- Runs pip-check

#### 3. Docker Nightly
- Builds and pushes nightly Docker images
- Tags: `nightly`, `nightly-{sha}`

#### 4. Report
- Generates nightly build report
- Creates issue if build fails

**Container Images**:
```bash
ghcr.io/{owner}/{repo}:nightly
ghcr.io/{owner}/{repo}:nightly-{sha}
```

---

### Stale Management

**File**: `.github/workflows/stale.yml`

**Triggers**:
- Daily at midnight UTC
- Manual trigger

**Configuration**:

**Issues**:
- Stale after 60 days of inactivity
- Closed 7 days after marked stale
- Exempt: `pinned`, `security`, `bug`, `feature-request`

**Pull Requests**:
- Stale after 30 days of inactivity
- Closed 14 days after marked stale
- Exempt: `pinned`, `security`, `work-in-progress`

---

### Cleanup

**File**: `.github/workflows/cleanup.yml`

**Triggers**:
- Weekly on Sunday at 3 AM UTC
- Manual trigger

**Jobs**:

#### 1. Cleanup Artifacts
- Removes artifacts older than 30 days
- Keeps 10 most recent artifacts

#### 2. Cleanup Workflow Runs
- Deletes runs older than 90 days
- Keeps minimum 10 runs

#### 3. Cleanup Caches
- Removes old GitHub Actions caches
- Frees up cache storage

---

## Configuration

### Dependabot

**File**: `.github/dependabot.yml`

Automatically updates:
- **Python dependencies** (weekly on Monday)
- **GitHub Actions** (weekly on Monday)
- **Docker base images** (weekly on Monday)

**Grouping**:
- LiteLLM packages
- FastAPI packages
- LangFuse packages
- Testing packages
- Dev tools

**Limits**:
- 5 PRs for pip dependencies
- 3 PRs for GitHub Actions
- 3 PRs for Docker

### Labeler

**File**: `.github/labeler.yml`

Automatically labels PRs based on:
- Changed files
- Branch name patterns
- File patterns

---

## Secrets Required

### Required (Core Functionality)
- `GITHUB_TOKEN` - Automatically provided by GitHub

### Optional (Enhanced Features)
- `CODECOV_TOKEN` - For code coverage reporting
- `DOCKERHUB_USERNAME` - For Docker Hub publishing
- `DOCKERHUB_TOKEN` - For Docker Hub authentication
- `PYPI_API_TOKEN` - For PyPI package publishing
- `GITLEAKS_LICENSE` - For enhanced Gitleaks scanning

### Configuration

Add secrets in: **Settings → Secrets and variables → Actions → New repository secret**

---

## Best Practices

### For Contributors

1. **PR Titles**: Use semantic commit format
   ```
   feat: Add new feature
   fix: Fix bug
   docs: Update documentation
   ```

2. **PR Descriptions**: Provide meaningful descriptions (>20 characters)

3. **Labels**:
   - Add `auto-merge` for automatic merging
   - Add `work-in-progress` for draft PRs
   - Add `breaking-change` for breaking changes

4. **Testing**: Ensure all CI checks pass before requesting review

### For Maintainers

1. **Releases**: Create tags following semantic versioning
   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   ```

2. **Security**: Review security scan results regularly

3. **Dependencies**: Review and merge Dependabot PRs promptly

4. **Monitoring**: Check nightly build results for issues

---

## Troubleshooting

### CI Failures

**Code Quality Failures**:
```bash
# Fix formatting
make format

# Check linting
make lint
```

**Test Failures**:
```bash
# Run tests locally
make test

# Run specific test
pytest tests/test_proxy.py -v
```

### Security Scan Warnings

- Review findings in Security tab
- Update dependencies if vulnerabilities found
- Use `# nosec` for Bandit false positives

### Docker Build Failures

```bash
# Test Docker build locally
make docker-build

# Check logs
docker-compose logs
```

---

## Monitoring & Dashboards

### GitHub Actions
- **Actions Tab**: View all workflow runs
- **Security Tab**: Security scan results
- **Insights → Dependency Graph**: Dependency information
- **Insights → Code Scanning**: CodeQL results

### Badges

Add to README.md:

```markdown
[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/ci.yml)
[![Security](https://github.com/{owner}/{repo}/actions/workflows/security.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/security.yml)
[![Release](https://github.com/{owner}/{repo}/actions/workflows/release.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/release.yml)
[![codecov](https://codecov.io/gh/{owner}/{repo}/branch/main/graph/badge.svg)](https://codecov.io/gh/{owner}/{repo})
```

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)

---

**Last Updated**: 2025-11-18
