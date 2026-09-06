import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import get_config

def test_no_env_branches_in_dags():
    """DAG code must not contain `if env == 'prod'` style branches."""
    dags_dir = REPO_ROOT / "dags"
    forbidden_patterns = [
        "env == ", 
        "ENV_NAME ==", 
        "os.getenv('ENV_NAME') ==", 
        'os.environ["ENV_NAME"] ==',
        "if config.env_name =="
    ]
    
    for dag_file in dags_dir.glob("*.py"):
        content = dag_file.read_text()
        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"Found forbidden env branch '{pattern}' in {dag_file.name}. "
                "Use the config loader to handle environment differences."
            )

def test_all_configs_load_successfully():
    """Every environment config must load without errors."""
    for env in ["local", "dev", "prod"]:
        os.environ["ENV_NAME"] = env
        config = get_config()
        assert config.env_name == env
        
def test_promotion_proof_script_runs():
    """Ensure the promotion proof script executes without errors."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_promotion.py")],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Promotion proof failed:\n{result.stderr}"