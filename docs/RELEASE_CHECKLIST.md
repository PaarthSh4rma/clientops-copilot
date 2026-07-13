# v1.5 Release Checklist

- [ ] Confirm `git status` contains only intended release changes.
- [ ] Scan tracked files and staged diff for secrets; keep `.env` and client documents untracked.
- [ ] Upgrade a clean database to `head`, downgrade to `base`, then upgrade again.
- [ ] Run `cd backend && ruff check . && ruff format --check .`.
- [ ] Run `cd backend && pytest -q`.
- [ ] Run `cd frontend && npm ci && npm run format:check && npm run lint && npm run build`.
- [ ] Validate `docker compose config`, build, startup, persistence, and shutdown when Docker is available.
- [ ] Smoke-test TXT/PDF/DOCX upload, scoped chat, insufficient evidence, provider failure, and deletion.
- [ ] Review README, audit, architecture, roadmap, environment example, and API version for accuracy.
- [ ] Confirm the GitHub Actions run is green without provider credentials.
- [ ] Refresh portfolio screenshots if the visible release UI changed.
- [ ] Create the release commit(s), then create the `v0.1.5` tag only after approval.
