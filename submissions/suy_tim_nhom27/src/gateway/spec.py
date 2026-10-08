"""Export the runtime API contract as OpenAPI 3.0.3."""
from __future__ import annotations

from fastapi.openapi.utils import get_openapi


def _convert_schema(value):
    if isinstance(value, list):
        return [_convert_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    converted = {key: _convert_schema(item) for key, item in value.items()}
    if "anyOf" in converted:
        alternatives = converted["anyOf"]
        non_null = [
            item for item in alternatives
            if not isinstance(item, dict) or item.get("type") != "null"
        ]
        if len(non_null) < len(alternatives):
            converted["nullable"] = True
            if len(non_null) == 1:
                converted.pop("anyOf")
                if "$ref" in non_null[0]:
                    converted["allOf"] = [non_null[0]]
                else:
                    converted.update(non_null[0])
            else:
                converted["anyOf"] = non_null
    if "const" in converted:
        converted["enum"] = [converted.pop("const")]
    for bound, keyword in (
        ("exclusiveMinimum", "minimum"),
        ("exclusiveMaximum", "maximum"),
    ):
        if bound in converted and not isinstance(converted[bound], bool):
            converted[keyword] = converted[bound]
            converted[bound] = True
    return converted


def contract(app):
    spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.3",
    )
    spec = _convert_schema(spec)
    spec["servers"] = [
        {
            "url": "http://127.0.0.1:8000",
            "description": "Demo local chỉ dùng dữ liệu synthetic",
        }
    ]
    security_scheme = spec.get("components", {}).get("securitySchemes", {}).get("HTTPBearer")
    if security_scheme is not None:
        security_scheme["description"] = (
            "Opaque bearer token from /api/v1/auth/token; SHA-256 hash stored in auth_session; "
            "session expires after 3600 seconds and can be revoked with /api/v1/auth/logout."
        )

    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    schemas.setdefault(
        "Error",
        {
            "title": "Error",
            "type": "object",
            "properties": {"detail": {"type": "string"}},
            "required": ["detail"],
        },
    )
    for path_item in spec["paths"].values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            operation["responses"]["422"] = {
                "description": "Dữ liệu không hợp lệ",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                },
            }
    return spec
