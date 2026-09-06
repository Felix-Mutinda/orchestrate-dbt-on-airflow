# ============================================================
# dbt-airflow-cosmos-feast Makefile
# ============================================================
# Usage: make <target>
# Run 'make help' for a list of available targets.
# ============================================================

.PHONY: help data dbt-build dbt-clean docs view-docs \
        airflow-init airflow-up airflow-down airflow-logs airflow-status \
        test test-p1 test-p2 test-p3 test-p4 \
        reset-all clean

# ------------------------------------------------------------
# Default target
# ------------------------------------------------------------
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------
# P0: Setup
# ------------------------------------------------------------
setup: ## Install Python dependencies via uv
	uv sync

# ------------------------------------------------------------
# P1: Data & dbt
# ------------------------------------------------------------
data: ## Fetch NYC TLC dataset
	uv run python scripts/fetch_dataset.py

dbt-build: ## Run dbt build (models + tests)
	uv run dbt build --project-dir dbt_project --profiles-dir dbt_project

dbt-clean: ## Clean dbt artifacts and DuckDB database
	rm -rf dbt_project/target dbt_project/dbt_packages
	rm -f var/duckdb/feature_platform.duckdb
	@echo "dbt artifacts and DuckDB database cleaned"

# ------------------------------------------------------------
# P2: Airflow Orchestration
# ------------------------------------------------------------
airflow-init: ## Initialize Airflow DB and create admin user
	mkdir -p var/airflow var/data var/duckdb var/feast
	docker compose up airflow-init

airflow-up: ## Start the Airflow stack
	docker compose up -d

airflow-down: ## Stop the Airflow stack
	docker compose down

airflow-logs: ## Tail Airflow logs
	docker compose logs -f airflow-scheduler airflow-webserver airflow-dag-processor

airflow-status: ## Show Airflow container status
	docker compose ps

# ------------------------------------------------------------
# P3: Lineage & Docs
# ------------------------------------------------------------
docs: ## Generate dbt docs artifacts
	uv run python scripts/generate_dbt_docs.py

view-docs: docs ## Serve dbt docs in browser
	@echo "Serving dbt docs at http://localhost:8081"
	@echo "Press Ctrl+C to stop the server"
	@cd docs/dbt && python -m http.server 8081

# ------------------------------------------------------------
# P4: Config & Promotion
# ------------------------------------------------------------
config-check: ## Validate config files load correctly
	uv run python -c "import sys; sys.path.insert(0, 'scripts'); from config import get_config; c = get_config(); print(f'✅ Loaded config for: {c.env_name}')"

# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------
test: test-p1 test-p2 test-p3 test-p4 ## Run all tests
	@echo "All tests passed"

test-p1: ## P1: dbt + DuckDB feature engineering tests
	uv run pytest tests/p1 -q

test-p2: ## P2: Docker Compose + DAG structure tests
	uv run pytest tests/p2 -q

test-p3: ## P3: Lineage + manifest tests
	uv run pytest tests/p3 -q

test-p4: ## P4: Config loader + promotion tests
	uv run pytest tests/p4 -q

# ------------------------------------------------------------
# Reset & Maintenance
# ------------------------------------------------------------
reset-all: dbt-clean ## Full reset: clean dbt, rebuild Docker, reinit Airflow
	docker compose down -v
	docker compose build --no-cache
	make airflow-init
	docker compose up -d
	docker compose restart airflow-webserver
	@echo "Full reset complete. Check http://localhost:8080"

clean: dbt-clean ## Clean all generated artifacts
	rm -rf docs/dbt
	rm -rf var/feast/registry.db var/feast/online_store.db
	rm -rf var/feast/data
	@echo "All generated artifacts cleaned"