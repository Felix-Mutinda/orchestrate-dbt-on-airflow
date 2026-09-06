import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import get_config


def test_local_config_loads():
    os.environ["ENV_NAME"] = "local"
    config = get_config()
    assert config.env_name == "local"
    assert config.warehouse.type == "duckdb"
    assert config.max_active_tasks == 1


def test_dev_config_loads():
    os.environ["ENV_NAME"] = "dev"
    config = get_config()
    assert config.env_name == "dev"
    assert config.warehouse.type == "snowflake"
    assert config.max_active_tasks == 32


def test_prod_config_loads():
    os.environ["ENV_NAME"] = "prod"
    config = get_config()
    assert config.env_name == "prod"
    assert config.warehouse.type == "snowflake"
    assert config.max_active_tasks == 128


def test_missing_config_fails():
    os.environ["ENV_NAME"] = "nonexistent"
    with pytest.raises(FileNotFoundError):
        get_config()
