import sys
import os

# Add the app directory to the path so we can import modules
sys.path.append(os.getcwd())

from app.services.auto_discovery import discover_site
import json

def test_discovery():
    # Testing with a sample hospital site (Min Hospital which was mentioned in history)
    url = "http://www.minhospital.or.kr/"
    print(f"Testing Auto-Discovery for: {url}")
    
    result = discover_site(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_discovery()
