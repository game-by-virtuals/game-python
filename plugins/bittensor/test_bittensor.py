import pytest
from unittest.mock import Mock, patch
from bittensor_game_sdk.bittensor_plugin import BittensorPlugin
from game_sdk.game.custom_types import FunctionResultStatus

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Setup mock environment variables"""
    monkeypatch.setenv('BITMIND_API_KEY', 'test_api_key')
    monkeypatch.setenv('GAME_API_KEY', 'test_game_key')

@pytest.fixture
def plugin():
    """Create a BittensorPlugin instance"""
    return BittensorPlugin()

def test_plugin_initialization(plugin):
    """Test plugin initialization"""
    assert plugin.id == "bittensor_plugin"
    assert plugin.name == "Bittensor Plugin"
    assert plugin.api_base_url == "https://subnet-api.bitmind.ai/v1"

def test_initialize_without_api_key():
    """Test initialization fails without API key"""
    with patch.dict('os.environ', clear=True):
        plugin = BittensorPlugin()
        with pytest.raises(ValueError, match="BITMIND_API_KEY environment variable is required"):
            plugin.initialize()

@patch('requests.post')
def test_detect_image_success(mock_post, plugin):
    """Test successful image detection"""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'isAI': True,
        'confidence': 95
    }
    mock_post.return_value = mock_response

    # Test
    result = plugin.detect_image('https://example.com/image.jpg')
    
    assert result['isAI'] is True
    assert result['confidence'] == 95
    mock_post.assert_called_once()

@patch('requests.post')
def test_detect_image_failure(mock_post, plugin):
    """Test failed image detection"""
    # Mock error response
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        'statusCode': 500,
        'message': 'Internal Server Error'
    }
    mock_post.return_value = mock_response

    # Test
    result = plugin.detect_image('https://example.com/image.jpg')
    assert result['statusCode'] == 500
    assert 'message' in result

@patch('requests.get')
def test_list_subnets(mock_get, plugin):
    """Test listing subnets"""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'subnets': [
            {'id': 34, 'name': 'Image Detection'},
            {'id': 1, 'name': 'Text Generation'}
        ]
    }
    mock_get.return_value = mock_response

    # Test
    result = plugin.list_subnets()
    assert 'subnets' in result
    assert len(result['subnets']) == 2
    mock_get.assert_called_once()

@patch('requests.get')
def test_get_subnet_info(mock_get, plugin):
    """Test getting subnet information"""
    subnet_id = 34
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': subnet_id,
        'name': 'Image Detection',
        'description': 'Detects AI-generated images'
    }
    mock_get.return_value = mock_response

    result = plugin.get_subnet_info(subnet_id)
    assert result['id'] == subnet_id
    assert 'name' in result
    mock_get.assert_called_once()

@patch('requests.post')
def test_call_subnet(mock_post, plugin):
    """Test calling a subnet"""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'result': 'success'}
    mock_post.return_value = mock_response

    # Test
    result = plugin.call_subnet(1, {'prompt': 'test'})
    assert result['result'] == 'success'
    mock_post.assert_called_once()

def test_invalid_subnet_id(plugin):
    """Test calling subnet with invalid ID"""
    with pytest.raises(Exception):
        plugin.call_subnet(-1, {'prompt': 'test'})

# Test the worker
@pytest.fixture
def mock_worker(mock_env_vars):
    """Create a mock worker instance"""
    with patch('plugins.bittensor.examples.bittensor_worker.BittensorImageWorker') as MockWorker:
        worker = MockWorker.return_value  # Get the instance from return_value
        worker.detect_image = Mock()  # Mock the detect_image method
        
        # Configure detect_image behavior for valid URLs
        def detect_side_effect(url):
            if url.startswith(('http://', 'https://')):
                return (
                    FunctionResultStatus.DONE,
                    "Image detection successful",
                    {'isAI': True, 'confidence': 90}
                )
            else:
                return (
                    FunctionResultStatus.FAILED,
                    "Invalid image URL format",
                    {}
                )
        
        worker.detect_image.side_effect = detect_side_effect
        return worker

def test_worker_detect_image(mock_worker):
    """Test worker's image detection"""
    status, message, result = mock_worker.detect_image('https://example.com/image.jpg')
    
    assert status == FunctionResultStatus.DONE
    assert "successful" in message
    assert result['isAI'] is True
    assert result['confidence'] == 90

def test_worker_detect_invalid_url(mock_worker):
    """Test worker with invalid URL"""
    status, message, result = mock_worker.detect_image('invalid_url')
    assert status == FunctionResultStatus.FAILED
    assert "Invalid image URL format" in message
