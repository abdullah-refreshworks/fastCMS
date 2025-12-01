"""
DEPRECATED: This file has been split into separate focused test files.

The tests from this file have been reorganized into individual files for better organization
and to allow running specific functionality tests independently.

New test files:
- tests/e2e/test_admin_auth.py - Admin authentication tests (2 tests)
- tests/e2e/test_base_collections.py - Base collection tests (2 tests)
- tests/e2e/test_auth_collections.py - Auth collection tests (3 tests)
- tests/e2e/test_view_collections.py - View collection tests (1 test)
- tests/e2e/test_records_crud.py - Record CRUD tests (5 tests, integration)
- tests/e2e/test_access_control.py - Access control tests (2 tests)

Run individual test files:
    pytest tests/e2e/test_admin_auth.py -v
    pytest tests/e2e/test_base_collections.py -v
    pytest tests/e2e/test_auth_collections.py -v
    pytest tests/e2e/test_view_collections.py -v
    pytest tests/e2e/test_access_control.py -v
    pytest tests/e2e/test_records_crud.py -m integration --run-integration

Or run all E2E tests:
    pytest tests/e2e/ -v -m "not integration"
"""
