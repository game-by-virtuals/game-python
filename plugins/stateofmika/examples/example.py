"""
State of Mika API Examples
-------------------------
This file demonstrates the usage of each tool available in the State of Mika API.
Each example includes:
- Feature description
- Example API request
- Expected response

All requests are routed through the universal router, which intelligently
directs queries to the appropriate tool.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "4f53316d-d945-4f17-a898-804e0ab5bfc9"


def route_query(query: str) -> Dict:
    """Helper function to route all queries through the universal router"""
    print("\n=== Starting API Request ===")

    # Set up headers for multipart/form-data
    headers = {"X-API-Key": API_KEY, "accept": "application/json"}

    # Set up form data
    form_data = {
        "query": (None, query),
        "tool": (None, ""),
        "parameters_str": (None, ""),
        "file": (None, ""),
    }

    url = f"{BASE_URL}/"
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Form data: {form_data}")

    try:
        print("\nMaking request...")
        response = requests.post(
            url,
            headers=headers,
            files=form_data,  # Use files parameter for multipart/form-data
        )
        print(f"Status code: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print("Request successful!")

        return response.json()
    except Exception as e:
        print(f"Error making request: {str(e)}")
        return {"error": str(e)}


def test_connection():
    """Test basic connectivity with a simple query"""
    print("\nTesting API connection...")
    result = route_query("What is 2 + 2?")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_news():
    """Test news endpoint"""
    print("\nTesting news endpoint...")
    result = route_query("Show me the latest crypto news about Bitcoin and Ethereum")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_math():
    """Test math endpoint"""
    print("\nTesting math endpoint...")
    result = route_query("Calculate 15% of 150 and add 500")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_token_price():
    """Test token price endpoint"""
    print("\nTesting token price endpoint...")
    result = route_query("What is the current price of Solana?")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_scraper():
    """Test scraper endpoint"""
    print("\nTesting scraper endpoint...")
    result = route_query("Summarize the article at https://example.com/crypto-article")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_dex_sales():
    """Test DEX sales endpoint"""
    print("\nTesting DEX sales endpoint...")
    result = route_query(
        "Show me SOL token sales in the last hour for address SOL_TOKEN_MINT_ADDRESS"
    )
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def test_dex_buys():
    """Test DEX buys endpoint"""
    print("\nTesting DEX buys endpoint...")
    result = route_query("Show me all SOL purchases by wallet WALLET_ADDRESS")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    return result


def run_all_tests():
    """Run all test functions"""
    tests = [
        test_connection,
        test_news,
        test_math,
        test_token_price,
        test_scraper,
        test_dex_sales,
        test_dex_buys,
    ]

    for test in tests:
        print(f"\n{'=' * 50}")
        print(f"Running {test.__name__}")
        print("=" * 50)
        test()


if __name__ == "__main__":
    print("Run test_connection() to test basic connectivity")
    print("Run run_all_tests() to test all endpoints")
