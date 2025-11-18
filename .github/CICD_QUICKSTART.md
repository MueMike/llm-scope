# CI/CD Quick Start Guide

This guide will help you get started with the GitHub Actions CI/CD pipeline for the LiteLLM Proxy with LangFuse Integration project.

## 🎯 Quick Overview

The CI/CD pipeline automatically:
- ✅ Runs tests and quality checks on every push/PR
- 🔒 Scans for security vulnerabilities
- 🚀 Builds and publishes Docker images on releases
- 🤖 Auto-updates dependencies via Dependabot
- 📊 Tracks code coverage
- 🏷️ Auto-labels PRs

## 🚦 Getting Started

### 1. Enable GitHub Actions

GitHub Actions should be enabled by default. Verify at:
```
Settings → Actions → General → Actions permissions
```

Select: **Allow all actions and reusable workflows**

### 2. Required Secrets (Optional)

The pipeline works without secrets, but you can enhance it:

| Secret | Purpose | Required |
|--------|---------|----------|
| `CODECOV_TOKEN` | Code coverage reporting | Optional |
| `DOCKERHUB_USERNAME` | Docker Hub publishing | Optional |
| `DOCKERHUB_TOKEN` | Docker Hub authentication | Optional |
| `PYPI_API_TOKEN` | PyPI package publishing | Optional |

**Add secrets**: `Settings → Secrets and variables → Actions → New repository secret`

### 3. First Workflow Run

The workflows will run automatically on:
- Push to main branches
- Pull request creation
- Tag creation (for releases)

**Manual trigger**: Go to `Actions` tab → Select workflow → `Run workflow`

## 📋 Workflow Overview

### CI Pipeline (`ci.yml`)
**Triggers**: Every push and PR
**Purpose**: Code quality, testing, Docker build validation

**What it does**:
1. Code quality checks (Black, isort, flake8, mypy)
2. Security scanning (Bandit, Safety, pip-audit)
3. Unit tests with coverage (Python 3.11 & 3.12)
4. Integration tests
5. Docker build test

**First time setup**: None required - works out of the box!

### Security Scanning (`security.yml`)
**Triggers**: Push, PR, weekly schedule
**Purpose**: Detect vulnerabilities and security issues

**What it does**:
1. CodeQL analysis (uploaded to Security tab)
2. Dependency review (for PRs)
3. Semgrep SAST scanning
4. Secret scanning (Gitleaks)
5. Container scanning (Trivy)
6. Python security audit
7. License compliance check

**View results**: `Security → Code scanning alerts`

### Pull Request (`pr.yml`)
**Triggers**: PR opened/synchronized
**Purpose**: Validate and auto-label PRs

**What it does**:
1. Validates PR title (semantic format)
2. Auto-labels by size and area
3. Compares code coverage
4. Posts summary comment
5. Detects breaking changes

**PR Title Format**:
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
```

### Release & Deploy (`release.yml`)
**Triggers**: Tag push (v*.*.*), manual
**Purpose**: Build and publish releases

**What it does**:
1. Runs full test suite
2. Builds Python package
3. Builds & pushes Docker images (multi-platform)
4. Creates GitHub release
5. (Optional) Publishes to PyPI

**Create a release**:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Auto Merge (`auto-merge.yml`)
**Triggers**: PR updates, reviews
**Purpose**: Auto-merge approved PRs

**How to use**:
```bash
# Add label to enable auto-merge
gh pr edit <number> --add-label "auto-merge"
```

**Auto-approves**: Dependabot patch/minor updates

### Performance (`performance.yml`)
**Triggers**: Push to main, PRs
**Purpose**: Track performance metrics

**What it does**:
1. Runs pytest benchmarks
2. Load testing
3. Performance tracking

### Nightly Build (`nightly.yml`)
**Triggers**: Daily at 2 AM UTC
**Purpose**: Comprehensive testing and maintenance

**What it does**:
1. Tests on Python 3.11, 3.12, 3.13
2. Checks for outdated dependencies
3. Builds and pushes nightly Docker images
4. Creates issue if failures occur

**View results**: `Actions → Nightly Build`

### Stale Management (`stale.yml`)
**Triggers**: Daily
**Purpose**: Close inactive issues/PRs

**Configuration**:
- Issues: Stale after 60 days, closed after 7 more
- PRs: Stale after 30 days, closed after 14 more

**Exempt labels**: `pinned`, `security`, `bug`

### Cleanup (`cleanup.yml`)
**Triggers**: Weekly
**Purpose**: Clean up old artifacts and workflow runs

**What it removes**:
- Artifacts older than 30 days
- Workflow runs older than 90 days
- Old GitHub Actions caches

## 🎓 Common Workflows

### Making a Contribution

1. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test locally**:
   ```bash
   make format  # Format code
   make lint    # Check linting
   make test    # Run tests
   ```

3. **Commit with semantic message**:
   ```bash
   git commit -m "feat: add new feature"
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   gh pr create --fill
   ```

5. **CI runs automatically** - Wait for checks to pass

6. **Request review** - Add reviewers

7. **(Optional) Enable auto-merge**:
   ```bash
   gh pr edit <number> --add-label "auto-merge"
   ```

### Creating a Release

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.0"
   ```

2. **Commit version bump**:
   ```bash
   git commit -am "chore: bump version to 1.0.0"
   git push
   ```

3. **Create and push tag**:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

4. **Release workflow runs** - Builds and publishes

5. **View release**: `Releases` tab on GitHub

### Reviewing Security Alerts

1. Go to `Security` tab
2. Check `Code scanning` for issues
3. Review `Dependabot alerts`
4. Check `Secret scanning` results

### Monitoring Build Health

1. **Actions tab**: Overview of all workflows
2. **Insights → Actions**: Usage statistics
3. **Nightly build results**: Check for failures
4. **Security tab**: Review alerts

## 🔧 Troubleshooting

### Workflow Not Running

**Check**:
1. Actions enabled? (`Settings → Actions`)
2. Branch protection rules not blocking?
3. Workflow file syntax correct?

**Test**: Trigger manually from Actions tab

### Tests Failing in CI

**Debug locally**:
```bash
# Run exact CI test command
pytest tests/ -v --cov=src --cov-report=term -m "not integration"

# Check formatting
make format

# Check linting
make lint
```

### Docker Build Failing

**Test locally**:
```bash
docker build -f docker/Dockerfile -t test .
```

**Check**:
- Dockerfile syntax
- Required files present
- No uncommitted changes

### Coverage Not Uploading

**Required**: Add `CODECOV_TOKEN` secret
1. Sign up at [codecov.io](https://codecov.io)
2. Get token for repo
3. Add as secret: `Settings → Secrets → CODECOV_TOKEN`

### Release Not Publishing

**Check**:
1. Tag format correct? (must be `v*.*.*`)
2. Tests passing?
3. Secrets configured? (for PyPI/Docker Hub)

**Debug**: Check workflow logs in Actions tab

## 📊 Monitoring & Metrics

### Code Coverage

- **Codecov**: https://codecov.io/gh/MueMike/llm-scope
- **View in PR**: Automated comment with coverage diff
- **View locally**: `make test` → open `htmlcov/index.html`

### Security Scanning

- **CodeQL**: `Security → Code scanning → CodeQL`
- **Trivy**: `Security → Code scanning → Trivy`
- **Dependabot**: `Security → Dependabot alerts`

### Workflow Success Rate

- **Actions tab**: View all workflow runs
- **Insights → Actions**: Success/failure metrics

## 🎯 Best Practices

### For Contributors

1. **Use semantic commits**:
   ```
   feat: new feature
   fix: bug fix
   docs: documentation
   test: tests
   refactor: code refactoring
   ```

2. **Run tests before pushing**:
   ```bash
   make format && make lint && make test
   ```

3. **Keep PRs focused** - One feature/fix per PR

4. **Write meaningful descriptions** - Help reviewers understand

5. **Respond to CI failures** - Don't ignore failing checks

### For Maintainers

1. **Review Dependabot PRs** - Don't let them accumulate

2. **Monitor security alerts** - Address promptly

3. **Check nightly builds** - Catch issues early

4. **Use auto-merge wisely** - For trusted contributors/bots

5. **Tag releases regularly** - Use semantic versioning

## 🔗 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)

## 🆘 Getting Help

- **Workflow Issues**: Check `.github/WORKFLOWS.md`
- **PR Problems**: See `.github/PULL_REQUEST_TEMPLATE.md`
- **Security**: See `SECURITY.md`
- **General**: Open an issue or discussion

---

**Pro Tip**: Add the workflow status badges to your README.md! See `.github/CI_CD_BADGES.md` for ready-to-use badges.

**Last Updated**: 2025-11-18
