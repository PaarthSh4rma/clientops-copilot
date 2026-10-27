# v1.6 Portfolio Release Checklist

- [ ] Confirm only intended product changes are present.
- [ ] Scan tracked files and the diff for secrets/client documents.
- [ ] Upgrade a clean disposable database to Alembic `head` and run `alembic check`.
- [ ] Run backend Ruff lint, Ruff format check, and the full Pytest suite.
- [ ] Run frontend `npm ci`, Prettier, ESLint, Vitest, and the production build.
- [ ] Run `npm audit` and review dependency changes.
- [ ] Validate Docker Compose configuration and run containers when Docker is available.
- [ ] Smoke-test empty state, upload/duplicate/select, prompt action, all three answer outcomes, evidence interaction, and deletion.
- [ ] Verify desktop, tablet, and mobile layouts with no horizontal overflow.
- [ ] Verify demo mode blocks mutation routes and uses only bundled synthetic documents.
- [ ] Review README, architecture, audit, roadmap, deployment guidance, environment example, and API version.
- [ ] Confirm CI is green without provider credentials.
- [ ] Verify the live demo URL, provider configuration, free-tier limits, and public mutation restrictions for the selected deployment topology.
