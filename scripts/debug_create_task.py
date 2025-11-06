import requests
import sys

BASE = "http://127.0.0.1:8001/api/v1"


def main():
    s = requests.Session()

    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    print("Login status:", r.status_code)
    if r.status_code != 200:
        print("Login failed:", r.text)
        sys.exit(1)

    payload = {
        "title": "UI verify: checkbox-user",
        "description": "Created by debug script to verify API",
        "task_type": "checkbox",
        "assignment_type": "user",
        "assigned_user_ids": [1],
        "priority": "medium",
        "tags": ["debug", "checkbox"],
    }

    r = s.post(f"{BASE}/tasks", json=payload)
    print("Create status:", r.status_code)
    print("Create resp:", r.text[:500])
    if r.status_code >= 300:
        sys.exit(2)

    r = s.get(f"{BASE}/tasks?page=1&size=5")
    print("List status:", r.status_code)
    print("List resp sample:", r.text[:500])


if __name__ == "__main__":
    main()