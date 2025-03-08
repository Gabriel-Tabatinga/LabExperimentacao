import requests
import json
import csv
from datetime import datetime
import time

GITHUB_TOKEN = ""
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def test_token():
    query = """
    {
      viewer {
        login
      }
    }
    """
    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS,
        json={"query": query},
        verify=False
    )
    if response.status_code == 200:
        print("Token funcionando:", response.json())
    else:
        print(f"Erro no token: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_token()