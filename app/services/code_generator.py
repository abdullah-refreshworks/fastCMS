"""
Code generator service for API documentation.

Generates code examples for different languages and frameworks:
- cURL
- JavaScript (Fetch API)
- TypeScript (with SDK)
- Python (requests)
- React hooks
"""

from typing import Any, Dict, List, Optional

from app.db.models.collection import Collection
from app.utils.field_types import FieldSchema


class CodeGenerator:
    """Generate code examples for API usage."""

    @staticmethod
    def generate_curl_examples(
        collection: Collection,
        base_url: str = "http://localhost:8000",
        token: str = "YOUR_TOKEN",
    ) -> Dict[str, str]:
        """
        Generate cURL examples for all CRUD operations.

        Args:
            collection: Collection model
            base_url: API base URL
            token: Auth token placeholder

        Returns:
            Dictionary of operation -> cURL command
        """
        collection_name = collection.name
        examples = {}

        # List records
        examples["list"] = f"""curl '{base_url}/api/v1/{collection_name}/records?page=1&limit=20' \\
  -H 'Authorization: Bearer {token}'"""

        # Get single record
        examples["get"] = f"""curl '{base_url}/api/v1/{collection_name}/records/RECORD_ID' \\
  -H 'Authorization: Bearer {token}'"""

        # Create record
        example_data = CodeGenerator._generate_example_data(collection.schema)
        examples["create"] = f"""curl -X POST '{base_url}/api/v1/{collection_name}/records' \\
  -H 'Authorization: Bearer {token}' \\
  -H 'Content-Type: application/json' \\
  -d '{example_data}'"""

        # Update record
        examples["update"] = f"""curl -X PATCH '{base_url}/api/v1/{collection_name}/records/RECORD_ID' \\
  -H 'Authorization: Bearer {token}' \\
  -H 'Content-Type: application/json' \\
  -d '{example_data}'"""

        # Delete record
        examples["delete"] = f"""curl -X DELETE '{base_url}/api/v1/{collection_name}/records/RECORD_ID' \\
  -H 'Authorization: Bearer {token}'"""

        # Filter
        examples["filter"] = f"""curl '{base_url}/api/v1/{collection_name}/records?filter=status=active' \\
  -H 'Authorization: Bearer {token}'"""

        # Sort
        examples["sort"] = f"""curl '{base_url}/api/v1/{collection_name}/records?sort=-created' \\
  -H 'Authorization: Bearer {token}'"""

        return examples

    @staticmethod
    def generate_javascript_examples(
        collection: Collection,
        base_url: str = "http://localhost:8000",
    ) -> Dict[str, str]:
        """Generate JavaScript (Fetch API) examples."""
        collection_name = collection.name
        examples = {}

        example_data = CodeGenerator._generate_example_data(collection.schema)

        # List records
        examples["list"] = f"""// List {collection_name} records
const response = await fetch('{base_url}/api/v1/{collection_name}/records?page=1&limit=20', {{
  headers: {{
    'Authorization': `Bearer ${{token}}`
  }}
}});
const data = await response.json();
console.log(data.items);"""

        # Get single record
        examples["get"] = f"""// Get a {collection_name} record
const response = await fetch('{base_url}/api/v1/{collection_name}/records/${{recordId}}', {{
  headers: {{
    'Authorization': `Bearer ${{token}}`
  }}
}});
const record = await response.json();"""

        # Create record
        examples["create"] = f"""// Create a new {collection_name} record
const response = await fetch('{base_url}/api/v1/{collection_name}/records', {{
  method: 'POST',
  headers: {{
    'Authorization': `Bearer ${{token}}`,
    'Content-Type': 'application/json'
  }},
  body: JSON.stringify({example_data})
}});
const record = await response.json();"""

        # Update record
        examples["update"] = f"""// Update a {collection_name} record
const response = await fetch('{base_url}/api/v1/{collection_name}/records/${{recordId}}', {{
  method: 'PATCH',
  headers: {{
    'Authorization': `Bearer ${{token}}`,
    'Content-Type': 'application/json'
  }},
  body: JSON.stringify({example_data})
}});
const updated = await response.json();"""

        # Delete record
        examples["delete"] = f"""// Delete a {collection_name} record
await fetch('{base_url}/api/v1/{collection_name}/records/${{recordId}}', {{
  method: 'DELETE',
  headers: {{
    'Authorization': `Bearer ${{token}}`
  }}
}});"""

        return examples

    @staticmethod
    def generate_typescript_sdk_examples(collection: Collection) -> Dict[str, str]:
        """Generate TypeScript SDK examples."""
        collection_name = collection.name
        examples = {}

        example_data = CodeGenerator._generate_example_data(collection.schema, typescript=True)

        # Setup
        examples["setup"] = f"""import {{ FastCMS }} from 'fastcms-sdk';

const client = new FastCMS('http://localhost:8000');

// Login first
await client.auth.login('user@example.com', 'password');"""

        # List records
        examples["list"] = f"""// List {collection_name} records
const records = await client.collection('{collection_name}').list({{
  page: 1,
  limit: 20,
  filter: 'status=active',
  sort: '-created'
}});

console.log(records.items);"""

        # Get single record
        examples["get"] = f"""// Get a {collection_name} record
const record = await client.collection('{collection_name}').getOne(recordId);"""

        # Create record
        examples["create"] = f"""// Create a new {collection_name} record
const record = await client.collection('{collection_name}').create({example_data});"""

        # Update record
        examples["update"] = f"""// Update a {collection_name} record
const updated = await client.collection('{collection_name}').update(recordId, {example_data});"""

        # Delete record
        examples["delete"] = f"""// Delete a {collection_name} record
await client.collection('{collection_name}').delete(recordId);"""

        # Real-time subscription
        examples["realtime"] = f"""// Subscribe to {collection_name} changes
client.collection('{collection_name}').subscribe((event) => {{
  console.log(event.action); // 'create', 'update', 'delete'
  console.log(event.record);
}});"""

        return examples

    @staticmethod
    def generate_react_examples(collection: Collection) -> Dict[str, str]:
        """Generate React hook examples."""
        collection_name = collection.name
        examples = {}

        # Custom hook
        examples["hook"] = f"""import {{ useState, useEffect }} from 'react';
import {{ client }} from './fastcms';

function use{collection_name.title()}() {{
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {{
    const fetchRecords = async () => {{
      try {{
        const data = await client.collection('{collection_name}').list();
        setRecords(data.items);
      }} catch (err) {{
        setError(err);
      }} finally {{
        setLoading(false);
      }}
    }};

    fetchRecords();
  }}, []);

  return {{ records, loading, error }};
}}"""

        # Component example
        examples["component"] = f"""function {collection_name.title()}List() {{
  const {{ records, loading, error }} = use{collection_name.title()}();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {{error.message}}</div>;

  return (
    <ul>
      {{records.map(record => (
        <li key={{record.id}}>
          {{/* Display record data here */}}
        </li>
      ))}}
    </ul>
  );
}}"""

        # Real-time component
        examples["realtime"] = f"""function {collection_name.title()}LiveList() {{
  const [records, setRecords] = useState([]);

  useEffect(() => {{
    // Initial fetch
    client.collection('{collection_name}').list()
      .then(data => setRecords(data.items));

    // Subscribe to changes
    const unsubscribe = client.collection('{collection_name}').subscribe((event) => {{
      if (event.action === 'create') {{
        setRecords(prev => [...prev, event.record]);
      }} else if (event.action === 'update') {{
        setRecords(prev => prev.map(r =>
          r.id === event.record.id ? event.record : r
        ));
      }} else if (event.action === 'delete') {{
        setRecords(prev => prev.filter(r => r.id !== event.record.id));
      }}
    }});

    return () => unsubscribe();
  }}, []);

  return (
    <ul>
      {{records.map(record => (
        <li key={{record.id}}>{{/* ... */}}</li>
      ))}}
    </ul>
  );
}}"""

        return examples

    @staticmethod
    def generate_python_examples(
        collection: Collection,
        base_url: str = "http://localhost:8000",
    ) -> Dict[str, str]:
        """Generate Python (requests) examples."""
        collection_name = collection.name
        examples = {}

        example_data = CodeGenerator._generate_example_data(collection.schema, python=True)

        # Setup
        examples["setup"] = f"""import requests

BASE_URL = '{base_url}'
TOKEN = 'your_token_here'

headers = {{
    'Authorization': f'Bearer {{TOKEN}}',
    'Content-Type': 'application/json'
}}"""

        # List records
        examples["list"] = f"""# List {collection_name} records
response = requests.get(
    f'{{BASE_URL}}/api/v1/{collection_name}/records',
    headers=headers,
    params={{'page': 1, 'limit': 20}}
)
records = response.json()['items']"""

        # Get single record
        examples["get"] = f"""# Get a {collection_name} record
response = requests.get(
    f'{{BASE_URL}}/api/v1/{collection_name}/records/{{record_id}}',
    headers=headers
)
record = response.json()"""

        # Create record
        examples["create"] = f"""# Create a new {collection_name} record
response = requests.post(
    f'{{BASE_URL}}/api/v1/{collection_name}/records',
    headers=headers,
    json={example_data}
)
record = response.json()"""

        # Update record
        examples["update"] = f"""# Update a {collection_name} record
response = requests.patch(
    f'{{BASE_URL}}/api/v1/{collection_name}/records/{{record_id}}',
    headers=headers,
    json={example_data}
)
updated = response.json()"""

        # Delete record
        examples["delete"] = f"""# Delete a {collection_name} record
response = requests.delete(
    f'{{BASE_URL}}/api/v1/{collection_name}/records/{{record_id}}',
    headers=headers
)"""

        return examples

    @staticmethod
    def _generate_example_data(
        schema: List[FieldSchema],
        typescript: bool = False,
        python: bool = False,
    ) -> str:
        """Generate example data for collection schema."""
        import json

        data = {}

        for field in schema[:5]:  # Limit to first 5 fields for brevity
            field_name = field.name

            # Skip system fields
            if field_name in ("id", "created", "updated", "deleted"):
                continue

            # Generate example value based on type
            if field.type == "text":
                data[field_name] = "Example text"
            elif field.type == "number":
                data[field_name] = 42
            elif field.type == "bool":
                data[field_name] = True if not python else "true" if not typescript else True
            elif field.type == "email":
                data[field_name] = "user@example.com"
            elif field.type == "url":
                data[field_name] = "https://example.com"
            elif field.type == "date":
                data[field_name] = "2025-01-01"
            elif field.type == "datetime":
                data[field_name] = "2025-01-01T12:00:00Z"
            elif field.type == "select":
                options = field.validation.get("options", [])
                data[field_name] = options[0] if options else "option1"
            elif field.type == "json":
                data[field_name] = {"key": "value"}
            elif field.type == "relation":
                data[field_name] = "RELATED_RECORD_ID"
            else:
                data[field_name] = "value"

        if typescript or python:
            return json.dumps(data, indent=2)
        return json.dumps(data)

    @classmethod
    def generate_all_examples(
        cls,
        collection: Collection,
        base_url: str = "http://localhost:8000",
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate all code examples for a collection.

        Returns:
            Dictionary with language -> examples mapping
        """
        return {
            "curl": cls.generate_curl_examples(collection, base_url),
            "javascript": cls.generate_javascript_examples(collection, base_url),
            "typescript": cls.generate_typescript_sdk_examples(collection),
            "react": cls.generate_react_examples(collection),
            "python": cls.generate_python_examples(collection, base_url),
        }
