import json
import os
from pathlib import Path


def main():
    try:
        from werkzeug.security import generate_password_hash

        password_hash = generate_password_hash("admin")
    except ImportError:
        # Fallback if werkzeug is somehow missing
        password_hash = "admin"

    # Airflow 3 SimpleAuthManager looks for this file directly in AIRFLOW_HOME
    airflow_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
    users_file = Path(airflow_home) / "simple_auth_manager_users.json"

    users = [
        {
            "username": "admin",
            "password": password_hash,
            "role": "admin",
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
        }
    ]

    users_file.parent.mkdir(parents=True, exist_ok=True)
    users_file.write_text(json.dumps(users, indent=2))
    print(f"Created {users_file} for Airflow 3 SimpleAuthManager")


if __name__ == "__main__":
    main()
