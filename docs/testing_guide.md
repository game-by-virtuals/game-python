# Testing Guide

This guide explains how to test the GAME SDK and verify your setup is working correctly.

## Prerequisites

1. Python 3.8 or higher
2. A GAME API key (get one from [Virtuals.io](https://virtuals.io))
3. Virtual environment (recommended)

## Quick Start

For a quick verification of your SDK setup, see the [test_sdk.py example](../examples/README.md#test-sdk-script).

## Setting Up Your Environment

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install the SDK and development dependencies:
```bash
pip install -e .
pip install -r requirements-dev.txt
```

3. Create a `.env` file in your project root with your API keys:
```env
GAME_API_KEY="your_api_key_here"
ENVIRONMENT=development
DEBUG=False
LOG_LEVEL=INFO
```

## Running the Test Script

We provide a test script (`examples/test_sdk.py`) that verifies your SDK setup is working correctly. The script:
1. Tests authentication with your API key
2. Creates a test agent
3. Verifies the SDK's core functionality

Run the test script:
```bash
python3 examples/test_sdk.py
```

You should see output similar to:
```
Testing GAME SDK connection...
✅ Successfully authenticated with API
✅ Successfully created test agent
🎉 SDK is working correctly!
```

## Writing Tests

When writing tests for the SDK, follow these patterns:

1. Use the provided test fixtures in `tests/conftest.py`
2. Handle API responses appropriately
3. Check for both success and error cases

Example test:
```python
def test_agent_creation(api_key):
    """Test creating a new agent."""
    agent = Agent(
        api_key=api_key,
        name="Test Agent",
        agent_description="Test Description",
        agent_goal="Test Goal",
        get_agent_state_fn=lambda x, y: {"status": "ready"}
    )
    assert agent.agent_id is not None
```

## Common Issues and Solutions

### API Base URL
The SDK uses `https://api.virtuals.io/api` as the base URL. If you need to use a different endpoint, you can:

1. Set it in your environment:
```env
GAME_API_BASE_URL="your_api_endpoint"
```

2. Or configure it in your code:
```python
from game_sdk.game.config import config

config.set("api_base_url", "your_api_endpoint")
```

### Authentication Issues
- Verify your API key is correct
- Check that your `.env` file is in the correct location
- Ensure you've installed `python-dotenv` (`pip install python-dotenv`)

### Response Handling
The SDK handles various API response types:
- 200-202: Success with JSON response
- 204: Success with no content
- Empty responses with success status codes
- Error responses with detailed messages

## Next Steps

1. Review the [Error Handling Guide](error-handling.md) for detailed error handling patterns
2. Check the [Configuration Guide](configuration.md) for advanced configuration options
3. See the [SDK Guide](sdk_guide.md) for complete SDK usage documentation
