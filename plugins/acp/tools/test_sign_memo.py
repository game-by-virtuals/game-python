import os
from acp_plugin_gamesdk.acp_plugin import AcpToken
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
import json

AGENT_WALLET_ADDRESS = "0x895dab20e8C52cEa7D03F3cEef38536f8edB8e74"
token = os.environ.get("ACP_TOKEN_BUYER")
private_key_hex = token[2:]
acp_token_client = AcpToken(
    token,
    AGENT_WALLET_ADDRESS,
    "https://base-sepolia-rpc.publicnode.com/"
)
web3 = acp_token_client.web3
account = web3.eth.account.from_key(token)
sender = account.address

# Construct unsigned transaction
encoded_data = acp_token_client.contract.encode_abi("memoCounter", args=[])
trx_data = {
    "target": acp_token_client.get_contract_address(),
    "value": "0",
    "data": encoded_data
}
message_json = json.dumps(trx_data, separators=(".", ":"), sort_keys=False)
print(f"JSON string: {message_json}")
message_bytes = message_json.encode()
account = Account.from_key(private_key_hex)

# Sign the transaction
message = encode_defunct(message_bytes)
signature = account.sign_message(message).signature.hex()
payload = {
    "agentWallet": acp_token_client.get_agent_wallet_address(),
    "trxData": trx_data,
    "signature": signature
}

# Submit to custom API
api_url = "https://acpx.virtuals.gg/api/acp-agent-wallets/transactions"
response = requests.post(api_url, json=payload)
print("✅ Payload sent!")
print("Status:", response.status_code)
print("Response:", response.json())