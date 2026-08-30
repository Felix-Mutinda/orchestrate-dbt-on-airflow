FROM apache/airflow:3.0.0-python3.11

USER root

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /opt/airflow

# 1. Copy ONLY dependency files for optimal Docker layer caching
COPY pyproject.toml uv.lock ./

# 2. Create virtual environment and install dependencies
RUN uv venv /opt/airflow/.venv
ENV VIRTUAL_ENV=/opt/airflow/.venv
ENV PATH="/opt/airflow/.venv/bin:${PATH}"

# Install dependencies (this brings in dbt-core, dbt-duckdb, cosmos, etc.)
RUN uv sync

# 3. Copy ONLY the necessary runtime project files
COPY dags/ ./dags/
COPY dbt_project/ ./dbt_project/
COPY feast_repo/ ./feast_repo/
COPY scripts/ ./scripts/
COPY config/ ./config/

# 4. Create runtime directories and set correct permissions for the airflow user
RUN mkdir -p /opt/airflow/var/airflow /opt/airflow/var/data /opt/airflow/var/duckdb /opt/airflow/var/feast
RUN chown -R airflow:root /opt/airflow/var \
    /opt/airflow/.venv \
    /opt/airflow/dags \
    /opt/airflow/dbt_project \
    /opt/airflow/feast_repo \
    /opt/airflow/scripts \
    /opt/airflow/config

USER airflow
ENV AIRFLOW_HOME=/opt/airflow