"""
End-to-end test for LangGraph plugin workflow creation
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

async def test_langgraph_workflow():
    """Test complete workflow creation flow"""

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("=" * 60)
        print("LangGraph Plugin E2E Test")
        print("=" * 60)

        # Step 1: Use fresh authentication token
        print("\n1. Using authentication token...")
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYjg3MGFjZC05MjQ5LTQyYzYtOGQxZS03ODBiNmVjOWQwYzYiLCJlbWFpbCI6InRlc3RAZmFzdGNtcy5kZXYiLCJ0b2tlbl9rZXkiOiIiLCJleHAiOjE3NjQ3NDY1MTksInR5cGUiOiJhY2Nlc3MifQ.XtKevNOYpd2VoxQlagrYXfFABXBCxk3AfopDw2xGKq0"
        print(f"   ✓ Using fresh token from test@fastcms.dev")
        print(f"   Token: {access_token[:50]}...")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Step 2: Create workflow
        print("\n2. Creating workflow...")
        workflow_response = await client.post(
            "/api/v1/plugins/langgraph/workflows",
            headers=headers,
            json={
                "name": "Test Workflow E2E",
                "description": "End-to-end test workflow"
            }
        )
        print(f"   Status: {workflow_response.status_code}")

        if workflow_response.status_code != 201:
            print(f"   ERROR: Workflow creation failed")
            print(f"   Response: {workflow_response.text}")
            return False

        workflow = workflow_response.json()
        workflow_id = workflow["id"]
        print(f"   ✓ Workflow created: {workflow_id}")
        print(f"   Name: {workflow['name']}")

        # Step 3: Create nodes
        print("\n3. Creating nodes...")

        # Create Start node
        start_node_response = await client.post(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/nodes",
            headers=headers,
            json={
                "workflow_id": workflow_id,
                "node_type": "start",
                "label": "Start Node",
                "position_x": 100,
                "position_y": 100,
                "config": {}
            }
        )
        print(f"   Start node status: {start_node_response.status_code}")

        if start_node_response.status_code != 201:
            print(f"   ERROR: Start node creation failed")
            print(f"   Response: {start_node_response.text}")
            return False

        start_node = start_node_response.json()
        start_node_id = start_node["id"]
        print(f"   ✓ Start node created: {start_node_id}")

        # Create LLM node
        llm_node_response = await client.post(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/nodes",
            headers=headers,
            json={
                "workflow_id": workflow_id,
                "node_type": "llm",
                "label": "LLM Node",
                "position_x": 300,
                "position_y": 100,
                "config": {
                    "model": "gpt-4o-mini",
                    "system_prompt": "You are a helpful assistant.",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        )
        print(f"   LLM node status: {llm_node_response.status_code}")

        if llm_node_response.status_code != 201:
            print(f"   ERROR: LLM node creation failed")
            print(f"   Response: {llm_node_response.text}")
            return False

        llm_node = llm_node_response.json()
        llm_node_id = llm_node["id"]
        print(f"   ✓ LLM node created: {llm_node_id}")

        # Create End node
        end_node_response = await client.post(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/nodes",
            headers=headers,
            json={
                "workflow_id": workflow_id,
                "node_type": "end",
                "label": "End Node",
                "position_x": 500,
                "position_y": 100,
                "config": {}
            }
        )
        print(f"   End node status: {end_node_response.status_code}")

        if end_node_response.status_code != 201:
            print(f"   ERROR: End node creation failed")
            print(f"   Response: {end_node_response.text}")
            return False

        end_node = end_node_response.json()
        end_node_id = end_node["id"]
        print(f"   ✓ End node created: {end_node_id}")

        # Step 4: Create edges
        print("\n4. Creating edges...")

        # Create edge from Start to LLM
        edge1_response = await client.post(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/edges",
            headers=headers,
            json={
                "workflow_id": workflow_id,
                "source_node_id": start_node_id,
                "target_node_id": llm_node_id
            }
        )
        print(f"   Edge 1 status: {edge1_response.status_code}")

        if edge1_response.status_code != 201:
            print(f"   ERROR: Edge 1 creation failed")
            print(f"   Response: {edge1_response.text}")
            return False

        edge1 = edge1_response.json()
        print(f"   ✓ Edge created: Start -> LLM ({edge1['id']})")

        # Create edge from LLM to End
        edge2_response = await client.post(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/edges",
            headers=headers,
            json={
                "workflow_id": workflow_id,
                "source_node_id": llm_node_id,
                "target_node_id": end_node_id
            }
        )
        print(f"   Edge 2 status: {edge2_response.status_code}")

        if edge2_response.status_code != 201:
            print(f"   ERROR: Edge 2 creation failed")
            print(f"   Response: {edge2_response.text}")
            return False

        edge2 = edge2_response.json()
        print(f"   ✓ Edge created: LLM -> End ({edge2['id']})")

        # Step 5: Verify workflow
        print("\n5. Verifying workflow...")

        # Get workflow details
        workflow_get_response = await client.get(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}",
            headers=headers
        )
        print(f"   Get workflow status: {workflow_get_response.status_code}")

        if workflow_get_response.status_code != 200:
            print(f"   ERROR: Failed to get workflow")
            return False

        print(f"   ✓ Workflow retrieved successfully")

        # Get nodes
        nodes_response = await client.get(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/nodes",
            headers=headers
        )
        print(f"   Get nodes status: {nodes_response.status_code}")

        if nodes_response.status_code != 200:
            print(f"   ERROR: Failed to get nodes")
            print(f"   Response: {nodes_response.text}")
            return False

        nodes_data = nodes_response.json()
        nodes = nodes_data.get("nodes", [])
        print(f"   ✓ Retrieved {len(nodes)} nodes")

        # Get edges
        edges_response = await client.get(
            f"/api/v1/plugins/langgraph/workflows/{workflow_id}/edges",
            headers=headers
        )
        print(f"   Get edges status: {edges_response.status_code}")

        if edges_response.status_code != 200:
            print(f"   ERROR: Failed to get edges")
            print(f"   Response: {edges_response.text}")
            return False

        edges_data = edges_response.json()
        edges = edges_data.get("edges", [])
        print(f"   ✓ Retrieved {len(edges)} edges")

        # Step 6: Test execution (optional - requires OpenAI API key)
        print("\n6. Testing workflow execution...")
        print("   (Skipping - requires OpenAI API key)")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✓ Workflow created: {workflow_id}")
        print(f"✓ Nodes created: {len(nodes)}")
        print(f"✓ Edges created: {len(edges)}")
        print("\n✅ All tests passed!")
        print("=" * 60)

        return True

if __name__ == "__main__":
    success = asyncio.run(test_langgraph_workflow())
    exit(0 if success else 1)
