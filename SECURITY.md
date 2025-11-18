# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of LiteLLM Proxy with LangFuse Integration seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do NOT:

- Open a public GitHub issue
- Disclose the vulnerability publicly before we've had a chance to address it

### Please DO:

1. **Report privately** using GitHub Security Advisories:
   - Go to: https://github.com/MueMike/llm-scope/security/advisories/new
   - Or email: [Your security contact email]

2. **Include the following information**:
   - Type of vulnerability
   - Full path of source file(s) related to the vulnerability
   - Location of the affected source code (tag/branch/commit or URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability, including how an attacker might exploit it

3. **Wait for our response**:
   - We will acknowledge your report within 48 hours
   - We will provide a more detailed response within 7 days
   - We will work with you to understand and validate the issue

## Security Update Process

1. **Validation**: We will validate the reported vulnerability
2. **Fix Development**: We will develop a fix for the vulnerability
3. **Testing**: The fix will be tested thoroughly
4. **Release**: We will release a patch version
5. **Disclosure**: We will publicly disclose the vulnerability after the patch is released

## Security Measures

This project implements several security measures:

### Automated Security Scanning

- **CodeQL**: Static analysis for code vulnerabilities
- **Trivy**: Container image vulnerability scanning
- **Bandit**: Python security linter
- **Safety**: Known vulnerability database checks
- **pip-audit**: PyPI vulnerability scanner
- **Gitleaks**: Secret scanning
- **Semgrep**: SAST (Static Application Security Testing)

### Dependency Management

- **Dependabot**: Automated dependency updates
- **Weekly scans**: Scheduled security scans every Monday
- **Dependency review**: Automated review for PRs

### Code Quality

- **Type checking**: mypy for type safety
- **Linting**: flake8 for code quality
- **Formatting**: Black and isort for consistent code style

## Security Best Practices for Users

### API Keys and Secrets

1. **Never commit secrets** to the repository
   - Use `.env` files (already in `.gitignore`)
   - Use environment variables
   - Use secret management tools (AWS Secrets Manager, Azure Key Vault, etc.)

2. **Rotate keys regularly**:
   - API keys should be rotated periodically
   - Use different keys for development and production

3. **Principle of least privilege**:
   - Use API keys with minimal required permissions
   - Restrict access to LangFuse and LLM providers

### Deployment Security

1. **Use HTTPS** in production:
   - Configure proper TLS/SSL certificates
   - Use reverse proxy (nginx, Caddy) for TLS termination

2. **Network security**:
   - Use firewall rules
   - Restrict access to necessary IPs only
   - Use VPC/private networks where possible

3. **Container security**:
   - Use official base images
   - Scan images regularly with Trivy
   - Keep images updated

4. **Authentication**:
   - Enable `REQUIRE_AUTH=true` in production
   - Use `LITELLM_MASTER_KEY` for API authentication
   - Implement additional authentication layers as needed

### Monitoring

1. **Enable logging**:
   - Set `ENABLE_REQUEST_LOGGING=true`
   - Monitor logs for suspicious activity

2. **Use LangFuse tracing**:
   - Track all API calls
   - Monitor for unusual patterns
   - Set up alerts for anomalies

3. **Prometheus metrics**:
   - Monitor request patterns
   - Track error rates
   - Set up alerting

## Known Security Considerations

### LiteLLM Proxy

- This proxy forwards requests to external LLM providers
- Ensure your LLM provider API keys are secured
- Monitor usage to detect unauthorized access

### LangFuse Integration

- LangFuse receives metadata about all requests
- Ensure LangFuse API keys are secured
- Review LangFuse's privacy policy and data handling

### Environment Variables

- `.env` files are gitignored by default
- Never commit `.env` files to version control
- Use `.env.example` as a template

## Compliance

This project aims to comply with:

- **OWASP Top 10**: Addressing common web application vulnerabilities
- **CWE Top 25**: Common Weakness Enumeration
- **GDPR**: Minimal data collection, user privacy

## Security Contacts

- **GitHub Security Advisories**: https://github.com/MueMike/llm-scope/security/advisories
- **Security Email**: [Your security contact email]

## Acknowledgments

We appreciate the security research community and will acknowledge security researchers who responsibly disclose vulnerabilities:

- **Hall of Fame**: [Link to acknowledgments]

Thank you for helping keep LiteLLM Proxy with LangFuse Integration and our users safe!

---

**Last Updated**: 2025-11-18
