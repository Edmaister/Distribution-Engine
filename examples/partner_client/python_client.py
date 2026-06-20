from __future__ import annotations

import os

import requests


BASE_URL = os.getenv("AMPLIFI_API_BASE_URL", "http://localhost:8000")
CLIENT_ID = os.getenv("AMPLIFI_CLIENT_ID")
CLIENT_SECRET = os.getenv("AMPLIFI_CLIENT_SECRET")
SCOPE = os.getenv("AMPLIFI_SCOPE", "events:write referrals:read")


def main() -> None:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SystemExit("AMPLIFI_CLIENT_ID and AMPLIFI_CLIENT_SECRET are required")

    token_response = requests.post(
        f"{BASE_URL}/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
        },
        timeout=10,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()

    identity_response = requests.get(
        f"{BASE_URL}/partner/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
        timeout=10,
    )
    identity_response.raise_for_status()
    print(identity_response.json())


if __name__ == "__main__":
    main()
