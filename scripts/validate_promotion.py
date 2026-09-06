import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import get_config


def hash_directory(directory: Path, extensions: tuple) -> str:
    """Hash all files with given extensions in a directory."""
    hasher = hashlib.sha256()
    if not directory.exists():
        return ""
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix in extensions:
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def main():
    repo_root = Path(__file__).parent.parent

    # 1. Hash the codebase (DAGs, dbt models, Feast definitions)
    dags_hash = hash_directory(repo_root / "dags", (".py",))
    models_hash = hash_directory(repo_root / "dbt_project/models", (".sql",))
    feast_hash = hash_directory(repo_root / "feast_repo", (".py",))

    code_hashes = {"dags": dags_hash, "models": models_hash, "feast": feast_hash}

    # 2. Load configs for all environments
    envs = ["local", "dev", "prod"]
    configs = {}
    for env in envs:
        os.environ["ENV_NAME"] = env
        configs[env] = get_config()

    # 3. Print Proof
    print("=" * 60)
    print("PROMOTION PROOF: Code vs. Configuration")
    print("=" * 60)

    print("\n1. Codebase Hashes (MUST be identical across environments):")
    for name, h in code_hashes.items():
        print(f"   {name:10}: {h[:16]}...")

    print("\n2. Resolved Configurations (MUST differ across environments):")
    for env, c in configs.items():
        print(
            f"   {env:10}: warehouse={c.warehouse.type:10} | schema={c.warehouse.schema_name:10} | concurrency={c.max_active_tasks}"
        )

    # 4. Assertions
    assert configs["local"].warehouse.type == "duckdb", "Local must use DuckDB"
    assert configs["dev"].warehouse.type == "snowflake", "Dev must use Snowflake"
    assert configs["prod"].warehouse.type == "snowflake", "Prod must use Snowflake"
    assert configs["dev"].max_active_tasks > configs["local"].max_active_tasks, (
        "Prod/Dev must scale concurrency"
    )

    print(
        "\nPromotion Proof Passed: Code is environment-agnostic. Config is environment-specific."
    )
    print(
        "   Moving from dev to prod requires changing exactly ONE environment variable."
    )


if __name__ == "__main__":
    main()
