import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(endpoint):
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"Testing {url}...")
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"Response: List with {len(data)} items")
            elif isinstance(data, dict):
                print(f"Response: Dict keys {list(data.keys())}")
                if "items" in data:
                    print(f"Items count: {len(data['items'])}")
        else:
            print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    print("--- Checking Backend Health ---")
    test_endpoint("/trends?days=7")
    test_endpoint("/trends/universe?limit=100")
