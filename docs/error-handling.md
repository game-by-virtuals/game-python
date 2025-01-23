# Error Handling Guide

The GAME SDK provides a comprehensive error handling system to help you handle errors gracefully and provide meaningful feedback to users.

## Exception Hierarchy

```
GameSDKError
├── APIError
│   └── AuthenticationError
├── ConfigurationError
├── ValidationError
├── FunctionExecutionError
├── WorkerError
└── AgentError
```

## Exception Types

### GameSDKError
Base exception class for all GAME SDK errors. All other SDK exceptions inherit from this class.

### APIError
Raised when there's an error communicating with the GAME API.

```python
try:
    result = post(base_url, api_key, "endpoint", data)
except APIError as e:
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")
```

### AuthenticationError
Raised when there's an authentication error with the API.

```python
try:
    token = get_access_token(api_key)
except AuthenticationError as e:
    print("Invalid API key or authentication failed")
```

### ConfigurationError
Raised when there's an error in the SDK configuration.

```python
try:
    config.set("invalid_key", "value")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### ValidationError
Raised when there's an error validating input data.

```python
try:
    create_agent(base_url, api_key, "", "description", "goal")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### FunctionExecutionError
Raised when there's an error executing a function.

```python
try:
    result = function.execute()
except FunctionExecutionError as e:
    print(f"Function '{e.function_name}' failed: {e}")
    if e.original_error:
        print(f"Original error: {e.original_error}")
```

### WorkerError
Raised when there's an error with worker operations.

```python
try:
    workers = create_workers(base_url, api_key, worker_list)
except WorkerError as e:
    print(f"Worker error: {e}")
```

### AgentError
Raised when there's an error with agent operations.

```python
try:
    agent = create_agent(base_url, api_key, name, description, goal)
except AgentError as e:
    print(f"Agent error: {e}")
```

## Best Practices

1. **Always Catch Specific Exceptions**:
   ```python
   try:
       # SDK operation
   except AuthenticationError:
       # Handle authentication errors
   except ValidationError:
       # Handle validation errors
   except APIError:
       # Handle other API errors
   except GameSDKError:
       # Handle any other SDK errors
   ```

2. **Provide Meaningful Error Messages**:
   ```python
   try:
       result = create_agent(...)
   except ValidationError as e:
       logger.error(f"Failed to create agent: {e}")
       raise UserFriendlyError("Please check the agent configuration")
   ```

3. **Log Errors Appropriately**:
   ```python
   import logging

   logger = logging.getLogger(__name__)

   try:
       result = api_call()
   except APIError as e:
       logger.error(f"API call failed: {e.status_code} - {e.response}")
       # Handle error
   ```

4. **Use Error Context**:
   ```python
   try:
       token = get_access_token(api_key)
   except AuthenticationError as e:
       print(f"Status code: {e.status_code}")
       print(f"Error details: {e.response}")
   ```

## Error Recovery

Some errors can be recovered from automatically:

1. **Retry on Temporary Failures**:
   ```python
   from game_sdk.game.config import config

   # Configure retry settings
   config.set("max_retries", 3)
   config.set("retry_delay", 1)
   ```

2. **Handle Rate Limiting**:
   ```python
   try:
       result = api_call()
   except APIError as e:
       if e.status_code == 429:  # Too Many Requests
           time.sleep(int(e.response.get("retry_after", 60)))
           result = api_call()  # Retry
   ```

## Testing Error Handling

The SDK provides tools for testing error handling:

```python
def test_error_handling(mock_response):
    # Mock an API error
    mock = mock_response(500, {"error": "Server Error"})
    
    with patch('requests.post', return_value=mock):
        with pytest.raises(APIError) as exc:
            result = api_call()
        assert exc.value.status_code == 500
```

## Common Error Scenarios

1. **Invalid API Key**:
   ```python
   try:
       token = get_access_token(api_key)
   except AuthenticationError:
       print("Please check your API key")
   ```

2. **Invalid Input Data**:
   ```python
   try:
       worker = create_worker(invalid_data)
   except ValidationError as e:
       print(f"Invalid worker configuration: {e}")
   ```

3. **Network Issues**:
   ```python
   try:
       result = api_call()
   except APIError as e:
       if "timed out" in str(e):
           print("Network connection is slow or unavailable")
   ```
