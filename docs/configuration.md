# Configuration Guide

The GAME SDK provides a flexible configuration system that allows you to customize its behavior. This guide explains how to configure the SDK for your needs.

## Default Configuration

The SDK comes with sensible defaults:

```python
DEFAULT_CONFIG = {
    "api_base_url": "https://game.virtuals.io",
    "api_version": "v1",
    "request_timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,
}
```

## Configuration Methods

There are three ways to configure the SDK:

1. **Environment Variables**:
   ```bash
   export GAME_API_BASE_URL="https://custom.api.url"
   export GAME_API_VERSION="v2"
   export GAME_REQUEST_TIMEOUT="60"
   export GAME_MAX_RETRIES="5"
   export GAME_RETRY_DELAY="2"
   ```

2. **Runtime Configuration**:
   ```python
   from game_sdk.game.config import config

   # Set individual values
   config.set("request_timeout", 60)
   config.set("max_retries", 5)

   # Get configuration values
   timeout = config.get("request_timeout")
   ```

3. **Initialization Configuration**:
   ```python
   from game_sdk.game.config import SDKConfig

   custom_config = SDKConfig(
       api_base_url="https://custom.api.url",
       request_timeout=60
   )
   ```

## Configuration Priority

The configuration values are applied in the following order (highest priority first):
1. Runtime configuration (`config.set()`)
2. Environment variables
3. Initialization values
4. Default values

## Available Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `api_base_url` | str | "https://game.virtuals.io" | Base URL for API calls |
| `api_version` | str | "v1" | API version to use |
| `request_timeout` | int | 30 | Request timeout in seconds |
| `max_retries` | int | 3 | Maximum number of retries |
| `retry_delay` | int | 1 | Delay between retries in seconds |

## Best Practices

1. **Environment-Specific Configuration**:
   - Use environment variables for environment-specific settings
   - Use different configurations for development and production

2. **Timeouts**:
   - Set appropriate timeouts based on your use case
   - Consider network latency when setting timeouts

3. **Retries**:
   - Adjust retry settings based on your reliability needs
   - Consider exponential backoff for production use

## Example Usage

```python
from game_sdk.game.config import config

# Check current configuration
print(config.as_dict())

# Update configuration
config.set("request_timeout", 60)

# Use in API calls
from game_sdk.game.utils import create_agent

# The API calls will use the updated configuration
agent = create_agent(
    base_url="https://api.example.com",
    api_key="your-key",
    name="Test Agent",
    description="Test Description",
    goal="Test Goal"
)
```

## Error Handling

The configuration system will raise `ConfigurationError` if:
- An invalid configuration key is used
- An invalid value type is provided
- Environment variables have invalid values

Example:
```python
from game_sdk.game.config import config
from game_sdk.game.exceptions import ConfigurationError

try:
    config.set("invalid_key", "value")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```
