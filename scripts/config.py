import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional

class WarehouseConfig(BaseModel):
    type: str
    path: Optional[str] = None
    schema_name: str = Field(alias="schema")

class FeastConfig(BaseModel):
    online_store_type: str
    online_store_path: str
    materialize_start: str
    materialize_end: str

class PipelineConfig(BaseModel):
    env_name: str
    warehouse: WarehouseConfig
    feast: FeastConfig
    max_active_tasks: int

def get_config() -> PipelineConfig:
    """Loads the pipeline configuration based on the ENV_NAME environment variable."""
    env_name = os.getenv("ENV_NAME", "local")
    
    # Resolve path relative to this script (works in Docker and locally)
    config_dir = Path(__file__).resolve().parent.parent / "config"
    config_path = config_dir / f"{env_name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
        
    # Inject env_name into the data for Pydantic validation
    data["env_name"] = env_name
    
    return PipelineConfig(**data)