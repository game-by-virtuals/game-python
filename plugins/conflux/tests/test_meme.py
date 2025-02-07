import pytest
from conflux_plugin_gamesdk.conflux_plugin_gamesdk import ConfluxPlugin

@pytest.fixture
def options():
    return {
        "id": "test_conflux_worker",
        "name": "Test Conflux Worker",
        "description": "An example Conflux Plugin for testing.",
        "credentials": {
            "rpc_url": "https://evmtest.confluxrpc.com",
            "private_key": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "contract_address": "0xA016695B5E633399027Ec36941ECa4D5601aBEac",
            "confi_pump_helper_url": "https://eliza-helper.vercel.app",
        },
    }

@pytest.fixture
def conflux_plugin(options):
    return ConfluxPlugin(options)

def test_create_meme(conflux_plugin):
    print("Creating meme...")
    create_meme_func = conflux_plugin.get_function("create_meme")
    token = create_meme_func(name="test_meme", symbol="TEST", description="test_meme", image_url="https://upload.wikimedia.org/wikipedia/zh/3/34/Lenna.jpg")
    assert token.startswith("0x")
    
def test_get_meme_list(conflux_plugin):
    get_meme_list_func = conflux_plugin.get_function("get_meme_list")
    memes = get_meme_list_func()
    assert len(memes) > 0

