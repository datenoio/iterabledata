# Security Policy

## Supported Versions

Security fixes are applied to the latest 1.0.x release line. Older releases do not
receive backports; upgrade to the most recent version on PyPI (`iterabledata`).

| Version | Supported |
| ------- | --------- |
| 1.0.x (latest) | Yes |
| < 1.0 | No |

## Reporting a Vulnerability

Please report vulnerabilities privately through **GitHub Security Advisories**:
open the repository's *Security* tab and choose *Report a vulnerability*.
Do not open public issues for unpatched vulnerabilities.

You can expect an acknowledgement within 7 days. We will coordinate a fix and a
release before public disclosure, and credit reporters in the release notes
unless you ask otherwise.

## Scope Notes

This library intentionally reads and writes files in many formats, including
files from untrusted sources. Relevant attack surface includes:

- Format parsers and compression codecs handling malformed or hostile input
  (see the `input-security` capability spec under `openspec/specs/` for the
  hardening requirements already adopted).
- SQL identifier handling in the database ingest backends
  (`iterable/ingest/`), which routes all identifiers through
  `iterable/ingest/identifiers.py` and binds row values as parameters.
- Optional AI/LLM integrations (`iterable/ai/`) — never send untrusted file
  contents to a cloud provider without review; use the built-in redaction
  helpers where offered.

Bugs in these areas are in scope for this policy. Vulnerabilities in optional
third-party dependencies should also be reported upstream to the dependency.
