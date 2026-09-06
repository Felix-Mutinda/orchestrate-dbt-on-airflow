import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "docs" / "dbt" / "manifest.json"

@pytest.fixture(scope="module")
def manifest():
    if not MANIFEST_PATH.exists():
        pytest.skip("manifest.json not found. Run `make docs` first.")
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_manifest_contains_expected_models(manifest):
    """Proves all expected dbt models were parsed and registered."""
    nodes = manifest.get("nodes", {})
    model_names = [node["name"] for node in nodes.values() if node["resource_type"] == "model"]
    
    expected_models = ["stg_yellow_trips", "stg_taxi_zones", "fct_trips", "feature_pickup_zone_hourly"]
    for model in expected_models:
        assert model in model_names, f"Model {model} not found in manifest"

def test_feature_mart_has_correct_upstream_lineage(manifest):
    """Proves the feature mart depends on the correct upstream fact table."""
    nodes = manifest.get("nodes", {})
    
    # Find the feature mart node
    feature_mart_node = next(
        (node for node in nodes.values() 
         if node.get("name") == "feature_pickup_zone_hourly" and node.get("resource_type") == "model"), 
        None
    )
    assert feature_mart_node is not None, "feature_pickup_zone_hourly not found in manifest"
    
    # Check its upstream dependencies
    depends_on = feature_mart_node.get("depends_on", {}).get("nodes", [])
    
    # It MUST depend on fct_trips
    assert any("fct_trips" in dep for dep in depends_on), (
        "feature_pickup_zone_hourly does not depend on fct_trips. Lineage broken!"
    )

def test_no_orphaned_models(manifest):
    """Proves every model (except staging) has at least one upstream dependency."""
    nodes = manifest.get("nodes", {})
    models = [node for node in nodes.values() if node["resource_type"] == "model"]
    
    for model in models:
        if "stg_" in model["name"]:
            continue # Staging models read from sources/parquet, so they have no upstream dbt nodes
            
        depends_on = model.get("depends_on", {}).get("nodes", [])
        assert len(depends_on) > 0, f"Model {model['name']} has no upstream dependencies. Possible orphan."