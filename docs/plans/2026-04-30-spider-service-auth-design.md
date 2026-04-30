# Spider Service Auth Design

## Goal

Add optional Bearer Token authentication to the standalone Spider API service.

## Design

The Spider service should match the existing NLP service behavior: `/health` remains public, and all other endpoints require `Authorization: Bearer <SPIDER_SERVICE_TOKEN>` only when `SPIDER_SERVICE_TOKEN` is configured. If the token is not configured, local development and existing tests continue to work without authentication.

The main Flask application already sends `SPIDER_SERVICE_TOKEN` when configured, so the change is limited to `spider_service/app/main.py` plus focused tests.

## Error Handling

Unauthorized requests return the existing service response envelope:

```json
{"code": 401, "msg": "unauthorized", "data": {}}
```

## Tests

Add service-level tests that verify:

- requests are accepted when no token is configured;
- protected endpoints reject missing or invalid tokens when the token is configured;
- protected endpoints accept the configured token.
