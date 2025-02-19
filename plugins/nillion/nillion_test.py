from dotenv import load_dotenv
from nillion_game_sdk.nillion_plugin import NillionPlugin

load_dotenv()

plugin = NillionPlugin()

# Test Create Schema
prompt = {
    "schema_description": "Create me a schema to track how much I spend on my boat collection"
}

schema_id, schema = plugin.create_schema(prompt)

print(schema_id, schema)

# Test Lookup Schema
prompt = {
    "schema_description": "Find me my schema that tracks how much I spend on my boat collection"
}

my_uuid, my_schema = plugin.lookup_schema(prompt)

print(my_uuid, my_schema)

# Test Data Upload
prompt = {
    "schema_uuid": "e868cc72-42f1-488d-ab3a-c8ffdbfba9b1",
    "data_to_store": [
        {
            "_id": "B0AB94E9-CC60-4DC0-9D15-8AD41B09B6C6",
            "boat_name": "Aquatic Escape",
            "purchase_date": "2024-10-12T21:32:49.208Z",
            "purchase_price": {
                "$share": "$342,077"
            },
            "maintenance_costs": {
                "$share": "$394,090"
            },
            "insurance_cost": {
                "$share": "$200,177"
            },
            "storage_fee": {
                "$share": "$254,353"
            }
        },
    ]
}

record_uuids = plugin.data_upload(prompt)

print(f"{record_uuids=}")


# Test Data Download
prompt = {
    "schema_uuid": "e868cc72-42f1-488d-ab3a-c8ffdbfba9b1"
}

data = plugin.data_download(prompt)

print(f"{data=}")