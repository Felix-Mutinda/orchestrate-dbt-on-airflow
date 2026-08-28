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

test-p1:
	uv run pytest tests/p1 -q