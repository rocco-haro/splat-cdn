import pytest
import asyncio
from fastapi.testclient import TestClient
import json
from datetime import datetime
import httpx
import pytest_asyncio
from typing import Dict, List
import uvicorn
import multiprocessing
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lambda_handler import create_local_app, StorageBackend, CDNBackend
from cdn.mock_cdn import app as cdn_app

# Mock data
MOCK_EXPERIMENT_CONFIG = {
    "scenarios": {
        "teleport": {
            "dwell_duration": 15.0,
            "teleport_duration": 0.2,
            "post_teleport_duration": 5.0
        },
        "spiral": {
            "duration": 30.0
        }
    }
}

MOCK_TEST_PATHS = {
    "scenarios": {
        "teleport": {
            "points": [
                {
                    "position": {"x": 2.5, "y": 0, "z": 2.5},
                    "timestamp": 0.0,
                    "expected_splats": ["0_0_0"]
                }
            ]
        },
        "spiral": {
            "points": [
                {
                    "position": {"x": 5.0, "y": 0, "z": 5.0},
                    "timestamp": 0.0,
                    "expected_splats": ["1_0_1"]
                }
            ]
        }
    }
}



class MockStorageBackend(StorageBackend):
    def __init__(self, configs=None, paths=None):
        self.configs = configs or {"test-experiment": MOCK_EXPERIMENT_CONFIG}
        self.paths = paths or {"test-experiment": MOCK_TEST_PATHS}

    def get_experiment_config(self, experiment_id: str) -> Dict:
        if experiment_id not in self.configs:
            raise FileNotFoundError(f"Experiment {experiment_id} not found")
        return self.configs[experiment_id]

    def get_test_paths(self, experiment_id: str) -> Dict:
        if experiment_id not in self.paths:
            raise FileNotFoundError(f"Experiment {experiment_id} not found")
        return self.paths[experiment_id]

def run_mock_cdn():
    uvicorn.run(cdn_app, host="127.0.0.1", port=8000, log_level="error")

@pytest.fixture(scope="session", autouse=True)
def mock_cdn_server():
    process = multiprocessing.Process(target=run_mock_cdn)
    process.start()
    time.sleep(1)  # Give the server time to start
    yield
    process.terminate()
    process.join()

@pytest_asyncio.fixture
async def async_client():
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def storage():
    return MockStorageBackend()

@pytest.fixture
def client(storage):
    app = create_local_app(storage_backend=storage)  # Pass the storage backend explicitly
    return TestClient(app)

@pytest.fixture
def sample_result():
    return {
        "experiment_type": "single_tier",
        "scenario": "teleport",
        "metrics": {
            "cache_hits": 150,
            "cache_misses": 5,
            "average_latency": 45.2
        }
    }

class TestExperimentEndpoint:
    def test_get_existing_experiment(self, client):
        response = client.get("/experiment/test-experiment")
        assert response.status_code == 200
        data = response.json()
        
        # Verify CDN endpoints
        assert "cdn" in data
        assert "single_tier" in data["cdn"]
        assert "two_tier" in data["cdn"]
        assert "content_endpoint" in data["cdn"]["single_tier"]
        assert "content_endpoint" in data["cdn"]["two_tier"]

    def test_get_nonexistent_experiment(self, client):
        response = client.get("/experiment/nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
class TestCDNIntegration:
    async def test_cdn_metrics_integration(self, async_client):
        response = await async_client.get("http://localhost:8000/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "single_tier" in metrics
        assert "two_tier" in metrics

    async def test_content_upload_and_retrieval(self, async_client):
        # Upload test content
        test_content = "test_content"
        response = await async_client.put(
            "http://localhost:8000/content",
            json={"key": "test_key", "content": test_content}
        )
        assert response.status_code == 200

        # Try retrieving from single-tier
        response = await async_client.get("http://localhost:8000/single-tier/content/test_key")
        assert response.status_code == 200
        # Fix: No need to decode as it's already a string
        assert response.json()["content"] == test_content

        # Try retrieving from two-tier
        response = await async_client.get("http://localhost:8000/two-tier/content/test_key")
        assert response.status_code == 200
        assert response.json()["content"] == test_content

@pytest.mark.asyncio
class TestResultsEndpoints:
    # @pytest.fixture
    # def sample_result(self):
    #     return {
    #         "experiment_type": "single_tier",
    #         "scenario": "teleport",
    #         "metrics": {
    #             "cache_hits": 150,
    #             "cache_misses": 5,
    #             "average_latency": 45.2
    #         }
    #     }

    async def test_post_results_with_cdn_metrics(self, client, sample_result, async_client):
        # First ensure mock CDN has some metrics
        await async_client.put(
            "http://localhost:8000/content",
            json={"key": "test_key", "content": "test_content"}
        )
        await async_client.get("http://localhost:8000/single-tier/content/test_key")
        
        # Post results
        response = client.post(
            "/results/test-experiment",
            json=sample_result
        )
        assert response.status_code == 200

        # Verify results include CDN metrics
        response = client.get("/results/test-experiment")
        assert response.status_code == 200
        results = response.json()
        
        assert len(results) > 0
        assert "cdn_metrics" in results[0]["data"]
        assert "test_results" in results[0]["data"]

@pytest.mark.asyncio
class TestEndToEndScenario:
    async def test_complete_experiment_flow(self, client, async_client):
        # 1. Get experiment configuration
        response = client.get("/experiment/test-experiment")
        assert response.status_code == 200
        experiment_config = response.json()

        # 2. Upload some test content to mock CDN
        content_key = "test_splat_1"
        await async_client.put(
            "http://localhost:8000/content",
            json={"key": content_key, "content": "test_splat_data"}
        )

        # 3. Retrieve content through both CDN configurations
        response = await async_client.get(f"http://localhost:8000/single-tier/content/{content_key}")
        assert response.status_code == 200
        
        response = await async_client.get(f"http://localhost:8000/two-tier/content/{content_key}")
        assert response.status_code == 200

        # 4. Post test results
        test_results = {
            "experiment_type": "single_tier",
            "scenario": "teleport",
            "metrics": {
                "cache_hits": 1,
                "cache_misses": 0
            }
        }
        response = client.post("/results/test-experiment", json=test_results)
        assert response.status_code == 200

        # 5. Verify final results include both test results and CDN metrics
        response = client.get("/results/test-experiment")
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        final_result = results[-1]["data"]
        assert "test_results" in final_result
        assert "cdn_metrics" in final_result

class TestErrorHandling:
    @pytest.fixture
    def failing_storage(self):
        class FailingStorageBackend(StorageBackend):
            def get_experiment_config(self, experiment_id: str) -> Dict:
                raise Exception("Simulated storage error")
            
            def get_test_paths(self, experiment_id: str) -> Dict:
                raise Exception("Simulated storage error")
        return FailingStorageBackend()

    @pytest.fixture
    def client_with_failing_storage(self, failing_storage):
        app = create_local_app(storage_backend=failing_storage)
        return TestClient(app)

    @pytest.fixture
    def failing_cdn(self):
        class FailingCDNBackend(CDNBackend):
            async def get_metrics(self) -> Dict:
                raise Exception("Simulated CDN metrics error")

            async def upload_content(self, key: str, content: bytes) -> None:
                raise Exception("Simulated CDN upload error")
        return FailingCDNBackend()

    @pytest.fixture
    def client_with_failing_cdn(self, storage, failing_cdn):
        app = create_local_app(storage_backend=storage, cdn_backend=failing_cdn)
        return TestClient(app)

    def test_storage_backend_generic_error(self, client_with_failing_storage):
        """Test handling of unexpected storage backend errors"""
        response = client_with_failing_storage.get("/experiment/test-experiment")
        assert response.status_code == 500
        assert "error" in response.json()
        assert "Simulated storage error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cdn_metrics_failure(self, client_with_failing_cdn, sample_result):
        """Test handling of CDN metrics retrieval failure"""
        response = client_with_failing_cdn.post(
            "/results/test-experiment",
            json=sample_result
        )
        assert response.status_code == 500
        assert "error" in response.json()
        assert "CDN metrics error" in response.json()["detail"]

class TestMalformedInputs:
    @pytest.mark.parametrize("invalid_result", [
        {},  # Empty payload
        {"experiment_type": "invalid_type"},  # Missing required fields
        {"experiment_type": "single_tier", "metrics": "not_a_dict"},  # Wrong type
        {"experiment_type": None, "metrics": {}},  # Null value
        {"experiment_type": "single_tier", "metrics": {"hits": "not_a_number"}}  # Invalid metric type
    ])
    def test_invalid_results_payload(self, client, invalid_result):
        """Test handling of various invalid results payloads"""
        response = client.post("/results/test-experiment", json=invalid_result)
        assert response.status_code in [400, 422]  # 422 for validation errors, 400 for malformed

    def test_invalid_json_payload(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/results/test-experiment",
            content=b"not valid json",  # Changed from data to content and made it bytes
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Invalid JSON" in response.json()["detail"]

    def test_missing_content_type(self, client, sample_result):
        """Test handling of missing Content-Type header"""
        # Use content parameter instead of json to avoid automatic header addition
        response = client.post(
            "/results/test-experiment",
            content=json.dumps(sample_result).encode(),
            headers={"Content-Length": str(len(json.dumps(sample_result)))}
        )
        assert response.status_code == 400
        assert "Content-Type" in response.json()["detail"]

class TestEdgeCases:
    @pytest.fixture
    def slow_cdn(self):
        class SlowCDNBackend(CDNBackend):
            async def get_metrics(self) -> Dict:
                await asyncio.sleep(5)  # Simulate slow response
                return {"metrics": "data"}

            async def upload_content(self, key: str, content: bytes) -> None:
                await asyncio.sleep(5)  # Simulate slow upload
                return
        return SlowCDNBackend()

    @pytest.fixture
    def client_with_slow_cdn(self, storage, slow_cdn):
        app = create_local_app(storage_backend=storage, cdn_backend=slow_cdn)
        return TestClient(app)

    def test_extremely_large_results_payload(self, client):
        """Test handling of unusually large payload"""
        large_payload = {
            "experiment_type": "single_tier",
            "metrics": {
                "large_field": "x" * 1000000  # 1MB of data
            }
        }
        response = client.post("/results/test-experiment", json=large_payload)
        assert response.status_code in [400, 413]  # 413 Payload Too Large

    @pytest.mark.asyncio
    async def test_cdn_timeout(self, client_with_slow_cdn, sample_result):
        """Test handling of CDN timeout"""
        response = client_with_slow_cdn.post(
            "/results/test-experiment",
            json=sample_result
        )
        assert response.status_code == 504  # Gateway Timeout

if __name__ == "__main__":
    pytest.main([__file__])