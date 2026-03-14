# Nigeria Construction AI Platform (Backend MVP)

AI-powered construction management backend for Nigerian projects, focused on delay risk, procurement intelligence, safety/compliance analysis, cost forecasting, workforce optimization, maintenance prediction, progress deviation, and tender risk extraction.

## Scope
- Backend-only MVP (no frontend)
- FastAPI API gateway with RBAC and token issuance
- 10 modular AI service domains
- Synthetic-data pipelines to bootstrap training/evaluation
- MLflow experiment logging and DVC pipeline stages
- Dockerized deployment and GitHub Actions CI

## Repository Structure
- `backend/app/main.py`: FastAPI entrypoint
- `backend/app/api/v1/router.py`: API gateway routing
- `backend/app/modules/*`: Module-specific schemas/services/routes
- `backend/pipelines/models/*`: Training scripts for key modules
- `backend/pipelines/rag/build_indexes.py`: RAG reference corpus build step
- `backend/scripts/bootstrap_data.py`: Synthetic data generator for local MVP runs
- `dvc.yaml`: Data/model pipeline orchestration
- `.github/workflows/ci.yml`: CI checks and test run

## Module Coverage
1. Project Tracker: ensemble-inspired delay scoring endpoint (`LSTM + DT + RF` stack contract).
2. Procurement Assistant: supplier quote intelligence + ARIMA forecast training script.
3. Safety Dashboard: log analysis endpoint + recall-oriented hazard detector training script.
4. Document Analyzer: clause extraction + compliance scoring endpoint and classifier script.
5. Cost Estimator: Naira-focused estimator endpoint + ensemble regression training script.
6. Workforce Scheduler: shift allocation and idle-rate optimizer.
7. Maintenance Predictor: equipment risk inference + time-series pipeline script.
8. Progress Visualizer: completion deviation analysis with threshold trigger.
9. Tender Analyzer: risk phrase extraction and LLM-style summary output.
10. Integration Suite: API key gated token issuance and RBAC foundation.

## Quickstart
1. Create env file:
```bash
cp .env.example .env
```
2. Install:
```bash
pip install -r requirements.txt
```
3. Bootstrap synthetic data:
```bash
python backend/scripts/bootstrap_data.py
```
4. Run API:
```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```
5. Open docs:
- `http://localhost:8000/docs`

## Single Port Policy
- API for all 10 modules runs on one port: `8000`
- Modules are separated by URL paths, not separate ports
- Optional infra ports:
  - `80` (Nginx reverse proxy)
  - `4040` (Ngrok inspect UI)

## Auth Flow
1. Request token:
```bash
curl -X POST http://localhost:8000/api/v1/integration/token \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","role":"project_manager"}'
```
2. Use token as `Bearer` for module routes.

## DVC + MLflow
1. Ensure tracking URI in `.env` (`MLFLOW_TRACKING_URI=./artifacts/mlruns`).
2. Reproduce pipeline:
```bash
dvc repro
```
3. Run MLflow UI (optional):
```bash
mlflow ui --backend-store-uri ./artifacts/mlruns
```

## Deployment (Render Example)
- Render blueprint in `render.yaml`
- Dockerized image in `Dockerfile`
- Provide runtime secrets via platform env vars (`API_KEY`, `JWT_SECRET`, DB credentials, model/API keys)

## Endpoint Payload Testing
- Individual request bodies are stored in:
  - `backend/scripts/payloads/*.json`
- Run full validation against a running API:
  - `powershell -ExecutionPolicy Bypass -File backend/scripts/run_endpoint_validation.ps1`
- JSON report:
  - `artifacts/reports/api_validation_report.json`

## Metrics Targets (MVP Contract)
- Delay Prediction F1 target: `> 0.70`
- Safety Recall target: `> 0.80`
- Document Accuracy target: `> 0.85`
- Cost: RMSE ratio `< 0.25` and MAPE `< 0.10`

## Important Implementation Note
This repository includes production-style architecture and runnable pipelines, but external data ingestion from live Nigerian supplier/weather/tender sources and cloud deployment require valid credentials and network access in your environment. Replace synthetic bootstrap datasets with approved real datasets to validate final KPI claims.

## Compliance and Ethics
See:
- `docs/ETHICS_AND_COMPLIANCE.md`
- `docs/ARCHITECTURE.md`
- `docs/PORTFOLIO_SHOWCASE.md`
- `docs/MODULE_IMPLEMENTATION_STATUS.md`
- `docs/API_ENDPOINTS.md`
- `docs/RUNBOOK.md`
