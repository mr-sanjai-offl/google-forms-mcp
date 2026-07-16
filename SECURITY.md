# Security Policy

## Supported Versions

Currently, the `main` branch and tagged releases >= `1.0.0` are supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please do not open a public issue for security vulnerabilities.

Instead, please email mr.sanjai.offl@gmail.com with the following details:
- A description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact.

We will acknowledge receipt within 48 hours and work with you to resolve the issue responsibly.

## OAuth Token Security
This application handles sensitive Google API OAuth tokens. By default, it stores tokens locally in `token.json`. When deployed in production environments, ensure the working directory is tightly restricted or use a secure secret manager for environment variables.
