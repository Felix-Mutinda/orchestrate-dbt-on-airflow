import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT_DIR = REPO_ROOT / "dbt_project"
DOCS_OUTPUT_DIR = REPO_ROOT / "docs" / "dbt"

def main():
    print("Generating dbt docs...")
    
    # Run dbt docs generate
    # Because we used env_var() in P2, running this locally without the Docker 
    # env vars will safely fall back to the relative paths in profiles.yml.
    result = subprocess.run(
        [
            "uv", "run", "dbt", "docs", "generate",
            "--project-dir", str(DBT_PROJECT_DIR),
            "--profiles-dir", str(DBT_PROJECT_DIR),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("dbt docs generate failed:")
        print(result.stderr)
        raise RuntimeError("Failed to generate dbt docs")
        
    # Move artifacts to the docs directory
    DOCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    target_dir = DBT_PROJECT_DIR / "target"
    artifacts = ["index.html", "manifest.json", "catalog.json", "run_results.json"]
    
    for artifact in artifacts:
        src = target_dir / artifact
        if src.exists():
            shutil.copy(src, DOCS_OUTPUT_DIR / artifact)
            print(f"Copied {artifact} to {DOCS_OUTPUT_DIR}")
            
    print("dbt docs generation complete.")

if __name__ == "__main__":
    main()