# OpenClaw Real Setup Status

Generated: 2026-05-03 15:00:52 KST

## Goal

Set up the local `materials-lab` OpenClaw plugin for a real end-to-end materials workflow, using OpenAI Codex OAuth and `openai-codex/gpt-5.5` as the target model. Materials Project live search and gateway writable agent transport are now both verified.

## Completed

- Installed the local plugin into the real OpenClaw config:
  - Plugin id: `materials-lab`
  - Source: `/Users/haksunlee/gitpublish/openclaw-materials-lab/dist/index.js`
  - Install source: `/Users/haksunlee/gitpublish/openclaw-materials-lab`
- Created and configured the Python runtime:
  - Virtualenv: `/Users/haksunlee/.openclaw/materials-lab/.venv`
  - Python: `/Users/haksunlee/.openclaw/materials-lab/.venv/bin/python`
  - Python version: `3.14.3`
  - Verified imports: `mp_api`, `pymatgen`, `ase`, `matplotlib`
- Configured plugin runtime path:
  - `plugins.entries.materials-lab.config.pythonPath`
  - Value: `/Users/haksunlee/.openclaw/materials-lab/.venv/bin/python`
- Updated OpenClaw from `2026.4.2` to `2026.5.2`.
- Set the default model to:
  - `openai-codex/gpt-5.5`
- Confirmed model catalog after update:
  - `openai-codex/gpt-5.5`: available, OAuth authenticated, default/configured
  - `openai-codex/gpt-5.5-pro`: available, OAuth authenticated
- Restarted the gateway service.
- Confirmed gateway probe:
  - Reachable: `yes`
  - App version: `2026.5.2`
  - Capability: `write-capable`
- Confirmed Materials Lab doctor:
  - Python available: OK
  - Workspace writable: OK
  - Worker health: OK
  - Materials Project API key: OK, configured
- Confirmed `gpt-5.5` model execution through OpenAI Codex OAuth using a gateway-routed agent smoke test.
- Confirmed gateway writable agent behavior by asking the agent to create:
  - `/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/gateway-writable-agent-smoke.md`
- Ran a live Materials Project perovskite-family E2E workflow with offline fallback disabled:
  - Final report: `/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/live-perovskite-solar-e2e-report.md`
  - Process report: `/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/live-openclaw-e2e-process.md`
  - Summary JSON: `/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/live-perovskite-solar-e2e-summary.json`

## Important Caveats

The OpenClaw update command installed `2026.5.2`, but its own verification step reported missing bundled runtime sidecar files for several built-in extensions. The CLI is currently usable, the gateway is running as `2026.5.2`, and `gpt-5.5` is available. Still, this verification warning should be treated as a follow-up OpenClaw package health issue.

The original local CLI device token was stuck with a pairing-only token. The pairing state was reset using official `openclaw devices clear --pending --yes`, the stale local `device-auth.json` was moved to a timestamped backup, and the gateway reissued a token with `operator.read` and `operator.write`.

The `gpt-5.5` smoke test now succeeds through the gateway without fallback. Result:

```text
OpenClaw gpt-5.5 게이트웨이 스모크 테스트, 쓰기 권한 확인, 재페어링 요청, 쓰기 가능 에이전트 E2E 모두 OK입니다.
```

Metadata confirmed:

- Provider: `openai-codex`
- Model: `gpt-5.5`
- Result: `success`
- Gateway result status: `ok`
- Gateway capability: `write-capable`
- Writable tool smoke test: `write` tool created `gateway-writable-agent-smoke.md`

## Materials Project API Key

The key is configured in the real OpenClaw config at:

```text
plugins.entries.materials-lab.config.mpApiKey
```

Recommended command for future key rotation:

```bash
openclaw config set plugins.entries.materials-lab.config.mpApiKey '"YOUR_32_CHARACTER_KEY_HERE"' --strict-json
openclaw gateway restart
openclaw materials doctor --json
```

Expected doctor change after setting the key:

```json
{
  "id": "mp-api-key",
  "status": "ok"
}
```

## Commands Used

```bash
openclaw plugins install -l /Users/haksunlee/gitpublish/openclaw-materials-lab
openclaw materials setup-python --python-path /Users/haksunlee/.pyenv/versions/3.14.3/bin/python3 --json
openclaw config set plugins.entries.materials-lab.config.pythonPath '"/Users/haksunlee/.openclaw/materials-lab/.venv/bin/python"' --strict-json
openclaw materials doctor --json
openclaw models set openai-codex/gpt-5.5
openclaw update status --json
openclaw update --yes --json
openclaw gateway restart
openclaw gateway probe
openclaw health
openclaw models list --provider openai-codex
openclaw agent --agent main --message "한국어 한 문장으로만 답하세요: OpenClaw gpt-5.5 gateway smoke test OK." --model openai-codex/gpt-5.5 --thinking minimal --json --timeout 120
openclaw devices clear --pending --yes --json
mv /Users/haksunlee/.openclaw/identity/device-auth.json /Users/haksunlee/.openclaw/identity/device-auth.json.bak-<timestamp>
openclaw agent --agent main --message "한국어 한 문장으로만 답하세요: gateway write-capable agent E2E OK." --thinking minimal --json --timeout 120
openclaw gateway probe
```

## Remaining Steps

No blocking setup steps remain for the current local workflow.

Optional follow-ups:

1. Report the OpenClaw `devices approve`/`devices reject` repair-loop behavior upstream.
2. Install a system Node 22 LTS or Node 24 outside version managers, then run `openclaw gateway install --force` if you want to remove the service config warning.
3. Convert the ad hoc live E2E runner into a first-class `openclaw materials` CLI command.
