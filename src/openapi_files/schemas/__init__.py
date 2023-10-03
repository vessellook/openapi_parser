import json
from pathlib import Path

from jsonschema.exceptions import SchemaError
from jsonschema.validators import Draft4Validator
import yaml

JSON_SCHEMA_30_SPEC_PATH = Path(__file__).parent / "openapi.3.0.json"
JSON_SCHEMA_20_SPEC_PATH = Path(__file__).parent / "swagger.2.0.json"

with open(JSON_SCHEMA_30_SPEC_PATH) as fh:
    openapi_30_validator = Draft4Validator(schema=json.load(fh))
with open(JSON_SCHEMA_20_SPEC_PATH) as fh:
    openapi_20_validator = Draft4Validator(schema=json.load(fh))

def validate_openapi(api_schema):
    return any((
        openapi_30_validator.is_valid(instance=api_schema),
        openapi_20_validator.is_valid(instance=api_schema),
    ))
