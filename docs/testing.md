# Testing Guide

The GAME SDK includes a comprehensive testing framework to ensure reliability and maintainability. This guide explains how to write and run tests for the SDK.

## Test Structure

Tests are organized in the `tests/` directory:
```
tests/
├── conftest.py         # Shared test fixtures
├── test_config.py      # Configuration tests
├── test_utils.py       # Utility function tests
└── ...
```

## Setting Up Test Environment

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run tests with coverage:
   ```bash
   pytest --cov=game_sdk
   ```

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def mock_config():
    """Fixture providing a test configuration."""
    return SDKConfig(
        api_base_url="https://test.virtuals.io",
        api_version="test",
        request_timeout=5
    )

@pytest.fixture
def mock_response():
    """Fixture providing a mock HTTP response."""
    def _mock_response(status_code=200, json_data=None):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        return mock
    return _mock_response
```

## Writing Tests

### Test Organization

1. **Group Related Tests**:
   ```python
   class TestAgent:
       def test_creation(self):
           pass

       def test_execution(self):
           pass
   ```

2. **Use Descriptive Names**:
   ```python
   def test_get_access_token_with_invalid_key():
       pass

   def test_create_agent_with_missing_fields():
       pass
   ```

### Testing API Calls

1. **Mock HTTP Responses**:
   ```python
   def test_api_call(mock_response):
       mock = mock_response(200, {"data": {"result": "success"}})
       
       with patch('requests.post', return_value=mock):
           result = api_call()
           assert result == {"result": "success"}
   ```

2. **Test Error Cases**:
   ```python
   def test_api_error(mock_response):
       mock = mock_response(500, {"error": "Server Error"})
       
       with patch('requests.post', return_value=mock):
           with pytest.raises(APIError) as exc:
               api_call()
           assert exc.value.status_code == 500
   ```

### Testing Configuration

```python
def test_config_override():
    """Test that configuration can be overridden."""
    config = SDKConfig(api_base_url="https://test.example.com")
    assert config.get("api_base_url") == "https://test.example.com"
    # Other values should remain default
    assert config.get("api_version") == "v1"
```

### Testing Validation

```python
def test_validation():
    """Test input validation."""
    with pytest.raises(ValidationError) as exc:
        create_agent("", "desc", "goal")
    assert "required" in str(exc.value)
```

## Test Categories

1. **Unit Tests**:
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on edge cases

2. **Integration Tests**:
   - Test component interactions
   - Use minimal mocking
   - Focus on common workflows

3. **Validation Tests**:
   - Test input validation
   - Test error handling
   - Test edge cases

## Best Practices

1. **Test Independence**:
   ```python
   def test_independent(mock_config):
       """Each test should be independent."""
       config = mock_config
       config.set("timeout", 30)
       assert config.get("timeout") == 30
   ```

2. **Clear Setup and Teardown**:
   ```python
   class TestWithSetup:
       @pytest.fixture(autouse=True)
       def setup(self):
           self.config = SDKConfig()
           yield
           # Cleanup code here
   ```

3. **Meaningful Assertions**:
   ```python
   def test_with_context():
       """Include context in assertions."""
       result = process_data([1, 2, 3])
       assert result == 6, "Sum should be 6 for input [1, 2, 3]"
   ```

## Running Tests

1. **Run All Tests**:
   ```bash
   pytest
   ```

2. **Run Specific Tests**:
   ```bash
   pytest tests/test_utils.py
   pytest tests/test_utils.py::test_get_access_token
   ```

3. **Run with Coverage**:
   ```bash
   pytest --cov=game_sdk --cov-report=html
   ```

## Continuous Integration

The SDK uses GitHub Actions for CI:

1. **Run Tests on Push**:
   ```yaml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
         - name: Install dependencies
           run: pip install -r requirements-dev.txt
         - name: Run tests
           run: pytest
   ```

2. **Coverage Reports**:
   ```bash
   pytest --cov=game_sdk --cov-report=xml
   ```

## Debugging Tests

1. **Print Debug Info**:
   ```python
   def test_with_debug(caplog):
       caplog.set_level(logging.DEBUG)
       result = complex_operation()
       print(caplog.text)  # View logs
   ```

2. **Use PDB**:
   ```bash
   pytest --pdb
   ```

## Adding New Tests

When adding new functionality:

1. Create a new test file if needed
2. Add tests for success cases
3. Add tests for error cases
4. Add tests for edge cases
5. Update documentation if needed
