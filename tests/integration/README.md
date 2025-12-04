# Integration Tests

This directory contains integration tests for FastCMS features.

## Configuration

These tests use environment variables from your `.env` file:
- `BASE_URL` - The base URL of your FastCMS instance (default: http://localhost:8000)
- `ADMIN_EMAIL` - Admin email for authentication
- `ADMIN_PASSWORD` - Admin password for authentication

## Available Tests

### test_api_rules.py
Tests the Advanced API Rules feature, including:
- Collection creation with custom rules
- Rule enforcement on create operations
- Success/failure scenarios

**Run:**
```bash
python tests/integration/test_api_rules.py
```

### test_expansion.py
Tests relation expansion functionality:
- Creating related collections
- Expanding relations in GET operations
- Single record and list expansion

**Run:**
```bash
python tests/integration/test_expansion.py
```

### test_langflow_e2e.py
End-to-end tests for the Langflow plugin:
- Health check endpoint
- Authentication requirements
- Langflow client functionality
- Configuration validation

**Run:**
```bash
python tests/integration/test_langflow_e2e.py
# or with pytest
pytest tests/integration/test_langflow_e2e.py -v
```

## Prerequisites

1. Make sure your FastCMS server is running:
   ```bash
   python cli.py start
   # or
   .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. Configure your `.env` file with the correct BASE_URL if not using localhost:8000

## Notes

- All tests automatically clean up created resources
- Tests require admin authentication
- Make sure your database is properly initialized before running tests
