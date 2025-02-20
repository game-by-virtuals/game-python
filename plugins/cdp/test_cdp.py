import pytest
from unittest.mock import Mock, patch
from cdp_game_sdk.cdp_plugin import CDPPlugin
from cdp.client.models.webhook import WebhookEventType

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Setup mock environment variables"""
    monkeypatch.setenv('CDP_API_KEY_NAME', 'test_key_name')
    monkeypatch.setenv('CDP_API_KEY_PRIVATE_KEY', 'test_private_key')
    monkeypatch.setenv('GAME_API_KEY', 'test_game_key')

@pytest.fixture
def plugin(mock_env_vars):
    """Create a CDP plugin instance"""
    return CDPPlugin()

@pytest.fixture
def mock_wallet():
    """Create a mock wallet"""
    wallet = Mock()
    wallet.id = "test_wallet_id"
    wallet.default_address = Mock()
    wallet.default_address.address_id = "0x123..."
    return wallet

def test_plugin_initialization(plugin):
    """Test plugin initialization"""
    assert plugin.id == "cdp_plugin"
    assert plugin.name == "CDP Plugin"
    assert plugin.network == "base-sepolia"

def test_initialize_without_api_key():
    """Test initialization fails without API keys"""
    with patch.dict('os.environ', clear=True):
        plugin = CDPPlugin()
        with pytest.raises(ValueError, match="CDP_API_KEY_NAME environment variable is required"):
            plugin.initialize()

@patch('cdp.Cdp.configure')
def test_initialize_with_server_signer(mock_configure, plugin):
    """Test initialization with server signer"""
    plugin.initialize(use_server_signer=True)
    mock_configure.assert_called_once_with(plugin.api_key_name, plugin.api_key_private_key)

@patch('cdp.Wallet.create')
def test_create_wallet(mock_create, plugin, mock_wallet):
    """Test wallet creation"""
    mock_create.return_value = mock_wallet
    
    result = plugin.create_wallet()
    
    assert result["wallet_id"] == "test_wallet_id"
    assert result["address"] == "0x123..."
    mock_create.assert_called_once_with("base-sepolia")

@patch('cdp.Wallet.fetch')
def test_import_wallet(mock_fetch, plugin, mock_wallet):
    """Test wallet import"""
    mock_fetch.return_value = mock_wallet
    
    plugin.import_wallet("test_wallet_id")
    assert plugin.wallet == mock_wallet
    mock_fetch.assert_called_once_with("test_wallet_id")

def test_wallet_operations_without_wallet(plugin):
    """Test operations fail when no wallet is initialized"""
    with pytest.raises(ValueError, match="No wallet initialized"):
        plugin.get_wallet_balance()

@patch('cdp.Wallet.create')
def test_get_wallet_balance(mock_create, plugin, mock_wallet):
    """Test getting wallet balance"""
    mock_wallet.default_address.balance.side_effect = lambda currency: "1.5" if currency == "eth" else "100"
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    balances = plugin.get_wallet_balance()
    
    assert balances["eth"] == 1.5
    assert balances["usdc"] == 100.0

@patch('cdp.Wallet.create')
def test_request_testnet_funds(mock_create, plugin, mock_wallet):
    """Test requesting testnet funds"""
    mock_tx = Mock()
    mock_tx.id = "tx_123"
    mock_tx.status = "completed"
    
    mock_wallet.faucet.return_value = mock_tx
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    result = plugin.request_testnet_funds("eth")
    
    assert result["transaction_id"] == "tx_123"
    assert result["status"] == "completed"
    mock_wallet.faucet.assert_called_once_with("eth")

@patch('cdp.Wallet.create')
def test_transfer(mock_create, plugin, mock_wallet):
    """Test fund transfer"""
    mock_tx = Mock()
    mock_tx.id = "tx_123"
    mock_tx.status = "completed"
    mock_tx.wait.return_value = mock_tx
    
    mock_wallet.transfer.return_value = mock_tx
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    result = plugin.transfer(0.1, "USDC", "0x456...", gasless=True)
    
    assert result["transaction_id"] == "tx_123"
    assert result["status"] == "completed"
    mock_wallet.transfer.assert_called_once_with(
        0.1, "usdc", "0x456...", gasless=True, skip_batching=False
    )

@patch('cdp.Wallet.create')
def test_trade(mock_create, plugin, mock_wallet):
    """Test trading between currencies"""
    mock_trade = Mock()
    mock_trade.id = "trade_123"
    mock_trade.status = "completed"
    mock_trade.wait.return_value = mock_trade
    
    mock_wallet.trade.return_value = mock_trade
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    result = plugin.trade(0.1, "ETH", "USDC")
    
    assert result["trade_id"] == "trade_123"
    assert result["status"] == "completed"
    mock_wallet.trade.assert_called_once_with(0.1, "eth", "usdc")

@patch('cdp.Wallet.create')
def test_get_transfer_history(mock_create, plugin, mock_wallet):
    """Test getting transfer history"""
    mock_transfers = [{"id": "tx_1"}, {"id": "tx_2"}]
    mock_wallet.default_address.transfers.return_value = mock_transfers
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    history = plugin.get_transfer_history()
    
    assert len(history) == 2
    assert history[0]["id"] == "tx_1"

@patch('cdp.Wallet.create')
def test_create_webhook(mock_create, plugin, mock_wallet):
    """Test creating webhook"""
    mock_webhook = Mock()
    mock_webhook.id = "webhook_123"
    mock_webhook.status = "active"
    
    mock_wallet.create_webhook.return_value = mock_webhook
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    result = plugin.create_webhook(
        "https://example.com/webhook",
        event_type=WebhookEventType.ERC20_TRANSFER
    )
    
    assert result["webhook_id"] == "webhook_123"
    assert result["status"] == "active"
    mock_wallet.create_webhook.assert_called_once()

@patch('cdp.Wallet.create')
def test_export_wallet(mock_create, plugin, mock_wallet):
    """Test wallet export"""
    mock_create.return_value = mock_wallet
    
    plugin.create_wallet()
    plugin.export_wallet("test_wallet.json", encrypt=True)
    
    mock_wallet.save_seed.assert_called_once_with("test_wallet.json", encrypt=True)
