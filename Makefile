.PHONY: install run test lint bootstrap train dvc repro

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check .

bootstrap:
	python backend/scripts/bootstrap_data.py

train:
	python backend/pipelines/models/train_project_tracker.py
	python backend/pipelines/models/train_procurement_forecast.py
	python backend/pipelines/models/train_safety_detector.py
	python backend/pipelines/models/train_document_analyzer.py
	python backend/pipelines/models/train_cost_estimator.py
	python backend/pipelines/models/train_maintenance_predictor.py

dvc:
	dvc init --no-scm || true

dvc-repro:
	dvc repro
