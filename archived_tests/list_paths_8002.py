#!/usr/bin/env python3
import requests

def main():
    r = requests.get("http://localhost:8002/openapi.json")
    print("openapi status:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return
    spec = r.json()
    paths = spec.get("paths", {})
    target = "/api/v1/groups/{group_id}/members"
    print("has members path:", target in paths)
    print("group-related paths:")
    for p in paths:
        if "groups" in p:
            print(" -", p)

if __name__ == "__main__":
    main()