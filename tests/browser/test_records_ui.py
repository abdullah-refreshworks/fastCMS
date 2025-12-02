"""
TRUE End-to-End Browser Tests for Records Management.

These tests use Playwright to test the ACTUAL user interface that users interact with,
not just the API. This catches bugs like incorrect API paths in the frontend JavaScript.

To run these tests:
    pytest tests/browser/test_records_ui.py --headed  # See the browser
    pytest tests/browser/test_records_ui.py           # Headless mode
"""

import pytest
from playwright.sync_api import Page, expect
import time


# This will be set to True if the server is already running
SERVER_RUNNING = False


@pytest.fixture(scope="module", autouse=True)
def setup_server():
    """Start the FastCMS server for browser tests."""
    global SERVER_RUNNING
    import subprocess
    import socket
    import time

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    # Check if server is already running
    if is_port_in_use(8000):
        SERVER_RUNNING = True
        yield
        return

    # Start the server
    process = subprocess.Popen(
        [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="/Users/abdullah/Desktop/projects/fastCMS"
    )

    # Wait for server to start
    for _ in range(30):
        if is_port_in_use(8000):
            break
        time.sleep(0.5)

    yield

    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture
def authenticated_page(page: Page):
    """Setup: Login to admin dashboard and return authenticated page."""
    # First check if we need to do initial setup
    page.goto("http://localhost:8000/admin/")
    page.wait_for_load_state("networkidle")

    # If redirected to setup, create admin
    if "setup" in page.url:
        page.fill('#email', "admin@fastcms.dev")
        page.fill('#password', "SecurePass123!")
        page.fill('#password_confirm', "SecurePass123!")
        page.click('button[type="submit"]')
        # Wait for redirect to dashboard
        page.wait_for_url("**/admin/**", timeout=10000)
        return page

    # If redirected to login, login with credentials
    if "login" in page.url:
        page.fill('#email', "admin@fastcms.dev")
        page.fill('#password', "SecurePass123!")
        page.click('button[type="submit"]')
        # Wait for successful login redirect
        page.wait_for_url("**/admin/**", wait_until="networkidle", timeout=10000)
        return page

    # Already authenticated
    return page


class TestRecordsUIFlow:
    """Test the complete records management flow through the browser UI."""

    def test_create_collection_and_add_record(self, authenticated_page: Page):
        """
        CRITICAL TEST: This would have caught the bug!
        Tests creating a collection and adding a record through the actual UI.
        """
        page = authenticated_page

        # Step 1: Navigate to new collection page
        page.goto("http://localhost:8000/admin/collections/new")
        page.wait_for_load_state("networkidle")

        # Step 3: Fill in collection form
        collection_name = f"test_products_{int(time.time())}"
        page.fill('#name', collection_name)
        page.select_option('#type', "base")

        # Add a field
        page.click('text="Add Field"')
        page.wait_for_timeout(500)  # Wait for field to be added

        # Fill in the first field (use more specific selectors for dynamically added fields)
        page.locator('input[x-model="field.name"]').first.fill("title")
        page.locator('select[x-model="field.type"]').first.select_option("text")

        # Save collection
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Wait to ensure collection is created
        page.wait_for_timeout(1000)

        # Step 4: Navigate directly to create record page
        page.goto(f"http://localhost:8000/admin/collections/{collection_name}/records/new")
        page.wait_for_load_state("networkidle")

        # Wait for the form to load and the schema to be fetched
        # The form should show the title field once the collection schema is loaded
        page.wait_for_selector('#title', timeout=10000)

        # Step 6: Fill in record form
        # The field ID matches the field name we created ("title")
        page.fill('#title', "Test Product Title")

        # Step 7: Save record (THIS IS WHERE THE BUG WAS!)
        # The JavaScript was calling POST /posts/records instead of POST /api/v1/collections/posts/records
        page.click('button[type="submit"]')

        # Step 8: Wait for success and verify
        # If the API path is wrong, this will fail with a 404 error
        page.wait_for_selector('text="Record created successfully"', timeout=5000)

        # Step 9: Verify we're redirected back to records list
        expect(page).to_have_url(f"http://localhost:8000/admin/collections/{collection_name}/records")

        # Step 10: Verify the record appears in the list
        expect(page.locator('text="Test Product Title"')).to_be_visible()

    def test_update_record_through_ui(self, authenticated_page: Page):
        """Test updating a record through the UI."""
        page = authenticated_page

        # Navigate to a collection with records
        # (This assumes the collection from previous test exists)
        page.goto("http://localhost:8000/admin/collections")
        page.wait_for_load_state("networkidle")

        # Click on first collection
        page.click('table tbody tr:first-child a')
        page.wait_for_load_state("networkidle")

        # Click on first record to edit
        page.click('table tbody tr:first-child a')
        page.wait_for_load_state("networkidle")

        # Edit the record
        page.fill('input[type="text"]:first', "Updated Title")

        # Save (tests PATCH request)
        page.click('button[type="submit"]')

        # Verify success
        page.wait_for_selector('text="Record updated successfully"', timeout=5000)

    def test_delete_record_through_ui(self, authenticated_page: Page):
        """Test deleting a record through the UI."""
        page = authenticated_page

        # Navigate to records page
        page.goto("http://localhost:8000/admin/collections")
        page.wait_for_load_state("networkidle")

        # Click on first collection
        page.click('table tbody tr:first-child a')
        page.wait_for_load_state("networkidle")

        # Get initial record count
        initial_rows = page.locator('table tbody tr').count()

        if initial_rows > 0:
            # Click delete button on first record
            # Handle the confirmation dialog
            page.on("dialog", lambda dialog: dialog.accept())
            page.click('button[title="Delete"]:first, button:has-text("Delete"):first')

            # Wait for success message
            page.wait_for_selector('text="Record deleted successfully"', timeout=5000)

            # Verify record count decreased
            page.wait_for_timeout(1000)  # Wait for UI to update
            final_rows = page.locator('table tbody tr').count()
            assert final_rows == initial_rows - 1


class TestCSVImportExportUI:
    """Test CSV import/export through the browser UI."""

    def test_export_csv_through_ui(self, authenticated_page: Page):
        """Test exporting CSV through the UI."""
        page = authenticated_page

        # Navigate to records page
        page.goto("http://localhost:8000/admin/collections")
        page.wait_for_load_state("networkidle")

        # Click on first collection
        page.click('table tbody tr:first-child a')
        page.wait_for_load_state("networkidle")

        # Click Export CSV button
        with page.expect_download() as download_info:
            page.click('text="Export CSV"')
        download = download_info.value

        # Verify download happened
        assert download.suggested_filename.endswith('.csv')

    def test_import_csv_through_ui(self, authenticated_page: Page):
        """Test importing CSV through the UI."""
        page = authenticated_page

        # Navigate to records page
        page.goto("http://localhost:8000/admin/collections")
        page.wait_for_load_state("networkidle")

        # Click on first collection
        page.click('table tbody tr:first-child a')
        page.wait_for_load_state("networkidle")

        # Click Import CSV button
        page.click('text="Import CSV"')

        # Wait for modal to appear
        page.wait_for_selector('input[type="file"]')

        # Create a temporary CSV file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("title\n")
            f.write("Imported Product 1\n")
            f.write("Imported Product 2\n")
            csv_path = f.name

        # Upload the file
        page.set_input_files('input[type="file"]', csv_path)

        # Click Import button
        page.click('button:has-text("Import")')

        # Wait for success message
        page.wait_for_selector('text="imported"', timeout=10000)


class TestNavigationAndUIConsistency:
    """Test that all UI navigation works correctly."""

    def test_dashboard_navigation(self, authenticated_page: Page):
        """Test navigating through the dashboard."""
        page = authenticated_page

        # Test all main navigation links
        page.goto("http://localhost:8000/admin/dashboard")
        page.wait_for_load_state("networkidle")

        # Click Collections
        page.click('a[href="/admin/collections"]')
        expect(page).to_have_url("http://localhost:8000/admin/collections")

        # Click Dashboard
        page.click('a[href="/admin/dashboard"]')
        expect(page).to_have_url("http://localhost:8000/admin/dashboard")
