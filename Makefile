.PHONY: bootstrap data lint test unit integration pipeline airflow feast-ui promotion-diff clean

bootstrap:
	uv venv --python 3.11
	uv sync --all-extras --dev
	cp -n .env.example .env || true
	mkdir -p var/airflow var/data var/duckdb var/feast
	
data:
	uv run python scripts/fetch_open_dataset.py

dbt-build:
	uv run dbt build --project-dir dbt_project --profiles-dir dbt_project

dbt-clean:
	uv run dbt clean --project-dir dbt_project --profiles-dir dbt_project

airflow-init:
	mkdir -p var/airflow var/data var/duckdb var/feast
	docker compose up airflow-init

airflow-up:
	docker compose up -d

airflow-down:
	docker compose down

airflow-logs:
	docker compose logs -f airflow-webserver airflow-scheduler

test-p1:
	uv run pytest tests/p1 -q

test-p2:
	uv run pytest tests/p2 -q