Run the Serifu shipping loop for the current changes (see
serifu/CONTRIBUTING.md): verify locally (typecheck → unit tests → build →
E2E), commit on the working branch with a feat(serifu)/fix(serifu)
message, push, open a non-draft PR against main using the PR template,
post a substantive review comment as Claude's half of the two-review
process, then report the PR URL and CI status. Do NOT merge — Oscar
merges. If CI fails, follow .claude/agents/release-captain.md:
drive-to-green before reporting back.
