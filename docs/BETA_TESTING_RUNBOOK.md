# CareerOS Beta Testing Runbook

## URLs
- Frontend (Streamlit): `http://localhost:8501`
- Backend (FastAPI): `http://localhost:8000`

Set backend URL inside Streamlit sidebar (`API URL`).

## Local Run Commands
```bash
# 1) Start API
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# 2) Start UI (new terminal)
streamlit run apps/ui/Home.py --server.address 0.0.0.0 --server.port 8501
```

## Layer-by-layer beta flow
1. L1 Intake -> create intake/bootstrap.
2. L2 Resume -> build evidence profile.
3. L3 Jobs -> auto-discover + ingest (set recent-hours filter).
4. L4-L10 Layer Runner tab:
   - L4 Match
   - L5 Rank
   - L6 Generate Package
   - L7 Guardrails
   - L10 HITL Decision
   - P10 Followups
   - P11 Notifications
5. One-Click Automation tab -> run full P25 automation.
6. Outputs tab -> inspect architecture map, latest layer report, and open/share artifacts.

## Optional ephemeral cloud sharing (for temporary review)
Set:
```bash
export ENABLE_TRANSFER_SH=true
```
Then click **Share Latest Artifacts to transfer.sh** in Outputs tab,
or call:
```bash
curl -X POST http://localhost:8000/artifacts/share/latest -H 'content-type: application/json' -d '{}'
```

## Notes for cloud storage migration
- Current temp share: transfer.sh (ephemeral/public links).
- Recommended production target: Azure Blob Storage with SAS + lifecycle policy.
