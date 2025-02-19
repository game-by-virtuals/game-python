import jwt
import requests
import nilql
import os
import time
import uuid

from jsonschema import Draft7Validator, validators
from ecdsa import SECP256k1, SigningKey
from langchain_openai import ChatOpenAI
from typing import Any, Generator

# from collections import deque, defaultdict
# import json
# import re

class NillionPlugin:
    """
    Nillion Plugin for interacting with Nillion subnets via Nillion API
    """
    
    def __init__(self) -> None:
        """Initialize the Nillion plugin"""
        self.id: str = "nillion_plugin"
        self.name: str = "Nillion Plugin"
        self.secret_key = os.getenv("NILLION_SECRET_KEY")
        self.org_did = os.getenv("NILLION_ORG_ID")
        self.key = None
        self.nodes = None
        
    def initialize(self):
        """Initialize the plugin"""
        if not self.secret_key:
            raise ValueError("NILLION_SECRET_KEY is not configured.")
        if not self.org_did:
            raise ValueError("NILLION_ORG_ID is not configured.")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured.")

        """Initialize config with JWTs signed with ES256K for multiple node_ids; Add cluster key."""
        response = requests.post(
            "https://sv-sda-registration.replit.app/api/config",
            headers={
                "Content-Type": "application/json",
            },
            json={"org_did": self.org_did},
        )
        self.nodes = response.json()["nodes"]

        # Convert the secret key from hex to bytes
        private_key = bytes.fromhex(self.secret_key)
        signer = SigningKey.from_string(private_key, curve=SECP256k1)

        for node in self.nodes:
            # Create payload for each node_id
            payload = {
                "iss": self.org_did,
                "aud": node["did"],
                "exp": int(time.time()) + 3600,
            }

            # Create and sign the JWT
            node["bearer"] = jwt.encode(payload, signer.to_pem(), algorithm="ES256K")

        self.key = nilql.ClusterKey.generate(
            {"nodes": [{}] * len(self.nodes)}, {"store": True}
        )

    def _post(
        self, nodes: list, endpoint: str, payload: dict
    ) -> Generator[requests.Response, Any, Any]:
        """Post payload to nildb nodes."""
        for node in nodes:
            headers = {
                "Authorization": f'Bearer {node["bearer"]}',
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{node['url']}/api/v1/{endpoint}",
                headers=headers,
                json=payload,
            )

            assert (
                response.status_code == 200 and response.json().get("errors", []) == []
            ), response.content.decode("utf8")

            yield response

    def fetch_schemas(self) -> list:
        """Get all my schemas from the first server."""
        headers = {
            "Authorization": f'Bearer {self.nodes[0]["bearer"]}',
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{self.nodes[0]['url']}/api/v1/schemas", headers=headers
        )

        assert (
            response.status_code == 200 and response.json().get("errors", []) == []
        ), response.content.decode("utf8")

        schema_list = response.json()["data"]
        assert len(schema_list) > 0, "failed to fetch schemas from nildb"
        return schema_list

    def find_schema(self, schema_uuid: str, schema_list: list | None = None) -> dict:
        """Filter a list of schemas by single desired schema id."""
        if not schema_list:
            schema_list = self.fetch_schemas()

        my_schema = None
        for this_schema in schema_list:
            if this_schema["_id"] == schema_uuid:
                my_schema = this_schema["schema"]
                break
        assert my_schema is not None, "failed to lookup schema"
        return my_schema

    def _mutate_secret_attributes(self, entry: dict) -> None:
        """Apply encryption or secret sharing to all fields in schema that are indicated w/ $share keyname."""
        keys = list(entry.keys())
        for key in keys:
            value = entry[key]
            if key == "_id":
                entry[key] = str(uuid.uuid4())
            elif key == "$share":
                del entry["$share"]
                entry["$allot"] = nilql.encrypt(self.key, value)
            elif isinstance(value, dict):
                self._mutate_secret_attributes(value)

    def _validator_builder(self):
        """Build a validator to validate the candidate document against loaded schema."""
        return validators.extend(Draft7Validator)

    def lookup_schema(self, args: dict[str, Any]) -> tuple:
        """Lookup a JSON schema based on input description and return it's UUID.
        Args:
            args (dict[str, Any]): Arguments containing schema_description
        Returns:
            tuple[str, dict]: The schema_uuid and the corresponding schema definition
        """
        try:
            validated_args = NillionLookupSchemaInput(**args)
            schema_list = self.fetch_schemas()

            schema_prompt = f"""
            1. I'll provide you with a description of the schema I want to use
            2. I'll provide you with a list of available schemas
            3. You will select the best match and return the associated UUID from the outermost `_id` field
            4. Do not include explanation or comments. Only a valid UUID string
            5. Based on the provided description, select a schema from the provided schemas.
            DESIRED SCHEMA DESCRIPTION:
            {validated_args.schema_description}
            AVAILABLE SCHEMAS:
            {json.dumps(schema_list)}
            """

            llm = ChatOpenAI(model="gpt-4o-mini")
            response = llm.invoke(schema_prompt)

            my_uuid = str(response.content)
            my_uuid = re.sub(r"[^0-9a-fA-F-]", "", my_uuid)

            my_schema = self.find_schema(my_uuid, schema_list)
            return my_uuid, my_schema

        except Exception as e:
            print(f"Error looking up schema: {e!r}")
            return None, None

    def create_schema(self, args: dict[str, Any]) -> tuple:
        """Create a schema in your privacy preserving database, called the Nillion SecretVault
        (or nildb), based on a natural language description. Do not use this tool for any other
        purpose.
        Args:
            args (dict[str, Any]): Arguments containing a complete description of the desired schema
        Returns:
            tuple[str, dict]: The schema_uuid and the corresponding schema definition
        """
        try:

            validated_args = NillionCreateSchemaInput(**args)
            print(f"fn:create_schema [{validated_args.schema_description}]")

            # ruff: noqa
            schema_prompt = f"""
            1. I'll provide you with a description of the schema I want to implement
            3. For any fields that could be considered financial, secret, currency, value holding, political, family values, sexual, criminal, risky, personal, private or personally
               identifying (PII), I want you to replace that type and value, instead, with an object that has a key named `$share` and the value of string as shown in this example:
                ORIGINAL ATTRIBUTE:
                "password": {{
                  "type": "string"
                }}
                REPLACED WITH UPDATED ATTRIBUTE PRESERVING NAME:
                "password": {{
                    "type": "object",
                    "properties": {{
                        "$share": {{
                          "type": "string",
                         }}
                     }}
                }}
            4. The JSON document should follow the patterns shown in these examples contained herein where the final result is ready to be included in the POST JSON payload
            5. Do not include explanation or comments. Only a valid JSON payload document.
            START OF JSON SCHEMA DESECRIPTION
            a JSON Schema following these requirements:
            - Use JSON Schema draft-07, type "array"
            - Each record needs a unique _id (UUID format, coerce: true)
            - Use "date-time" format for dates (coerce: true)
            - Mark required fields (_id is always required)
            - Set additionalProperties to false
            - Avoid "$" prefix in field names to prevent query conflicts
            - The schema to create is embedded in the "schema" attribute
            - "_id" should be the only "keys"
            - Note: System adds _created and _updated fields automatically
            Example `POST /schema` Payload
            {{
              "name": "My services",
              "keys": ["_id"],
              "schema": {{
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "array",
                "items": {{
                  "type": "object",
                  "properties": {{
                    "_id": {{
                      "type": "string",
                      "format": "uuid",
                      "coerce": true
                    }},
                    "username": {{
                      "type": "string"
                    }},
                    "password": {{
                      "type": "string"
                    }},
                  }},
                  "required": ["_id", "username", "password"],
                  "additionalProperties": false
                }}
              }}
            }}
            Based on this description, create a JSON schema:
            {validated_args.schema_description}
            """

            llm = ChatOpenAI(model="gpt-4o-mini")
            response = llm.invoke(schema_prompt)

            schema = json.loads(str(response.content))

            schema["_id"] = str(uuid.uuid4())
            schema["owner"] = self.org_did

            deque(
                self._post(self.nodes, "schemas", schema), maxlen=0
            )  # discard results since we throw on err
            print(f'fn:create_schema [{schema["_id"]}]')
            return schema["_id"], schema
        except Exception as e:
            print(f"Error creating schema: {str(e)}")
            return None, None

    def data_upload(self, args: dict[str, Any]) -> list[str]:
        """Create a schema in your privacy preserving database, called the Nillion SecretVault
        (or nildb), based on a natural language description. Do not use this tool for any other
        purpose.
        Args:
            args (dict[str, Any]): Arguments containing a UUID and the data to upload.
        Returns:
            list[str]: A list of the uploaded record's UUIDs
        """
        try:
            validated_args = NillionDataUploadInput(**args)
            print(
                f"fn:data_upload [{validated_args.schema_uuid}] [{validated_args.data_to_store}]"
            )

            schema_definition = self.find_schema(validated_args.schema_uuid)

            builder = self._validator_builder()
            validator = builder(schema_definition)

            for entry in validated_args.data_to_store:
                self._mutate_secret_attributes(entry)

            record_uuids = [x["_id"] for x in validated_args.data_to_store]
            payloads = nilql.allot(validated_args.data_to_store)

            for idx, shard in enumerate(payloads):

                validator.validate(shard)

                node = self.nodes[idx]
                headers = {
                    "Authorization": f'Bearer {node["bearer"]}',
                    "Content-Type": "application/json",
                }

                body = {"schema": validated_args.schema_uuid, "data": shard}

                response = requests.post(
                    f"{node['url']}/api/v1/data/create",
                    headers=headers,
                    json=body,
                )

                assert (
                    response.status_code == 200
                    and response.json().get("errors", []) == []
                ), f"upload (host-{idx}) failed: " + response.content.decode("utf8")
            print(f"fn:data_upload COMPLETED: {record_uuids}")
            return record_uuids

        except Exception as e:
            print(f"Error creating records in node: {str(e)}")
            return []

    def data_download(self, args: dict[str, Any]) -> list[dict]:
        """Create a schema in your privacy preserving database, called the Nillion SecretVault
        (or nildb), based on a natural language description. Do not use this tool for any other
        purpose.
        Args:
            args (dict[str, Any]): Arguments containing a target schema UUID
        Returns:
            list[dict]: A list of the downloaded records
        """
        try:
            validated_args = NillionDataDownloadInput(**args)
            print(f"fn:data_download [{validated_args.schema_uuid}]")

            shares = defaultdict(list)
            for node in self.nodes:
                headers = {
                    "Authorization": f'Bearer {node["bearer"]}',
                    "Content-Type": "application/json",
                }

                body = {
                    "schema": validated_args.schema_uuid,
                    "filter": {},
                }

                response = requests.post(
                    f"{node['url']}/api/v1/data/read",
                    headers=headers,
                    json=body,
                )
                assert (
                    response.status_code == 200
                ), "upload failed: " + response.content.decode("utf8")
                data = response.json().get("data")
                for d in data:
                    shares[d["_id"]].append(d)
            decrypted = []
            for k in shares:
                decrypted.append(nilql.unify(self.key, shares[k]))
            return decrypted
        except Exception as e:
            print(f"Error retrieving records in node: {e!r}")
            return []