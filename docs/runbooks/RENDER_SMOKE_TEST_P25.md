# Render Smoke Test — CareerOS UI + API (P25)

Use this to validate deployed Render API/UI quickly.

## 1) Command

```bash
scripts/render_smoke.sh \
  https://careeros-backend-d9sc.onrender.com \
  https://career-os-final-test.streamlit.app
```

## 2) What this checks

- `GET /health`
- `GET /phases/status`
- `GET /p25/system/health`
- `GET /feedback/list`
- `POST /p25/automation/run` (inline demo resume + job)
- `GET /p25/automation/trace/latest`
- `POST /feedback/submit`
- UI response headers (reachability)

## 3) Pass criteria

- `/health` returns `status: ok`
- `/phases/status` shows P25 available/ready
- `/p25/automation/run` returns `status: ok` with valid artifact paths and metrics
- `/p25/automation/trace/latest` returns trace for `render_smoke_run`
- `/feedback/submit` accepts payload
- UI URL is reachable (200/303 depending on Streamlit auth mode)

## 4) Notes

- If your environment is behind a restricted proxy, direct calls may fail even if Render services are healthy.
- For private Streamlit deployments, HTTP 303 redirect to auth is expected and still indicates reachability.
