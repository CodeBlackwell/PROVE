# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately — **do not open a public
issue**.

Email **codeblackwell@gmail.com** with:

- a description of the issue and its impact,
- steps to reproduce (or a proof of concept), and
- any suggested remediation.

You can expect an acknowledgement within a few days. Please allow reasonable
time for a fix before any public disclosure.

## Supported versions

PROVE is an actively developed application deployed from `main`. Security fixes
are applied to `main`; there are no separately maintained release branches.

## Scope notes

- Secrets live in `.env` (gitignored) and `.env` on the server — never commit
  them. `scripts/scrub_secrets.py` can help audit for accidental leaks.
- Neo4j is never exposed publicly in the production stack; Caddy terminates TLS
  and only the app port is reachable. See [README.md](README.md#deployment) and
  CLAUDE.md for the deployment model.
