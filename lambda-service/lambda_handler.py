from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod
import json
import os
from datetime import datetime, timedelta
import httpx
import boto3
from collections import defaultdict
from pydantic import BaseModel, Field, validator, constr
import asyncio
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

# Maximum allowed payload size (1MB)
MAX_PAYLOAD_SIZE = 1_000_000

# --------------------------
# Pydantic Models
# --------------------------

class ExperimentMetrics(BaseModel):
    cache_hits: int = Field(..., ge=0)
    cache_misses: int = Field(..., ge=0)
    average_latency: float = Field(..., ge=0)

class ExperimentResults(BaseModel):
    experiment_type: constr(regex='^(single_tier|two_tier)$')
    scenario: constr(regex='^(teleport|spiral)$')
    metrics: Dict[str, Union[int, float]]

    @validator('metrics')
    def validate_metrics(cls, v):
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Metric '{key}' must be a number")
        return v

# --------------------------
# Storage Backend Interfaces & Implementations
# --------------------------

class StorageBackend(ABC):
    @abstractmethod
    def get_experiment_config(self, experiment_id: str) -> Dict:
        pass

    @abstractmethod
    def get_test_paths(self, experiment_id: str) -> Dict:
        pass

class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str = "./../mock-data-generator"):
        self.base_path = base_path

    def get_experiment_config(self, experiment_id: str) -> Dict:
        with open(f"{self.base_path}/experiments/{experiment_id}/config.json") as f:
            return json.load(f)

    def get_test_paths(self, experiment_id: str) -> Dict:
        with open(f"{self.base_path}/generated/{experiment_id}/test_paths.json") as f:
            return json.load(f)

class S3StorageBackend(StorageBackend):
    def __init__(self, bucket_name: str):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name

    def get_experiment_config(self, experiment_id: str) -> Dict:
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=f"experiments/{experiment_id}/config.json"
            )
            return json.loads(response['Body'].read())
        except self.s3.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Experiment {experiment_id} not found")

    def get_test_paths(self, experiment_id: str) -> Dict:
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=f"experiments/{experiment_id}/test_paths.json"
            )
            return json.loads(response['Body'].read())
        except self.s3.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Experiment {experiment_id} not found")

# --------------------------
# CDN Backend Interfaces & Implementations
# --------------------------

class CDNBackend(ABC):
    @abstractmethod
    async def get_metrics(self) -> Dict:
        pass

    @abstractmethod
    async def upload_content(self, key: str, content: bytes) -> None:
        pass

class MockCDNBackend(CDNBackend):
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_metrics(self) -> Dict:
        response = await self.client.get(f"{self.base_url}/metrics")
        return response.json()

    async def upload_content(self, key: str, content: bytes) -> None:
        await self.client.put(
            f"{self.base_url}/content",
            json={"key": key, "content": content.decode()}
        )

class CloudFrontCDNBackend(CDNBackend):
    def __init__(self, distribution_id: str):
        self.cloudfront = boto3.client('cloudfront')
        self.distribution_id = distribution_id
        self.cloudwatch = boto3.client('cloudwatch')

    async def get_metrics(self) -> Dict:
        # Get CloudFront metrics from CloudWatch
        response = self.cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'hits',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/CloudFront',
                            'MetricName': 'Requests',
                            'Dimensions': [
                                {'Name': 'DistributionId', 'Value': self.distribution_id},
                                {'Name': 'Result', 'Value': 'Hit'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    }
                },
                # Additional metrics can be added here
            ],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow()
        )
        return response['MetricDataResults']

    async def upload_content(self, key: str, content: bytes) -> None:
        # In a real implementation, this would upload to S3 and trigger a CloudFront invalidation.
        # TODO: Implement actual upload logic.
        pass

# --------------------------
# Results Storage
# --------------------------

class ResultsStorage:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.results = defaultdict(list)

    async def add_result(self, experiment_id: str, result: Dict):
        async with self._lock:
            self.results[experiment_id].append({
                "timestamp": datetime.utcnow().isoformat(),
                "data": result
            })

    def get_experiment_results(self, experiment_id: str) -> List[Dict]:
        return self.results[experiment_id]

    def get_all_results(self) -> Dict[str, List[Dict]]:
        return dict(self.results)

# --------------------------
# Application Factory
# --------------------------

def create_app(storage_backend: StorageBackend, cdn_backend: CDNBackend):
    app = FastAPI()
    results_storage = ResultsStorage()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers for uniform error responses
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "detail": str(exc.detail)}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": True, "detail": str(exc)}
        )

    # Middleware to validate content type and payload size
    @app.middleware("http")
    async def validate_content_type(request: Request, call_next):
        if request.method == "POST":
            content_type = request.headers.get("content-type")
            if not content_type or "application/json" not in content_type.lower():
                return JSONResponse(
                    status_code=400,
                    content={"error": True, "detail": "Content-Type must be application/json"}
                )
        if request.method in ["POST", "PUT"]:
            body = await request.body()
            if len(body) > MAX_PAYLOAD_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": True, "detail": "Payload too large"}
                )
        response = await call_next(request)
        return response

    @app.middleware("http")
    async def validate_json(request: Request, call_next):
        if request.method == "POST" and request.headers.get("content-type") == "application/json":
            try:
                await request.json()
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={"error": True, "detail": "Invalid JSON"}
                )
        response = await call_next(request)
        return response

    @app.get("/experiment/{experiment_id}")
    async def get_experiment(experiment_id: str):
        try:
            config = storage_backend.get_experiment_config(experiment_id)
            paths = storage_backend.get_test_paths(experiment_id)

            cdn_config = {
                "single_tier": {
                    "content_endpoint": "http://localhost:8000/single-tier/content",
                    "metrics_endpoint": "http://localhost:8000/metrics"
                },
                "two_tier": {
                    "content_endpoint": "http://localhost:8000/two-tier/content",
                    "metrics_endpoint": "http://localhost:8000/metrics"
                }
            }

            return {
                "cdn": cdn_config,
                "scenarios": paths["scenarios"],
                "config": config
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Experiment not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/results/{experiment_id}")
    async def post_results(experiment_id: str, results: ExperimentResults):
        try:
            # Add a timeout for retrieving CDN metrics
            try:
                async with asyncio.timeout(3.0):  # 3 second timeout
                    cdn_metrics = await cdn_backend.get_metrics()
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="CDN metrics retrieval timed out")

            combined_results = {
                "test_results": results.dict(),
                "cdn_metrics": cdn_metrics
            }

            await results_storage.add_result(experiment_id, combined_results)
            return {"status": "success"}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/results/{experiment_id}")
    async def get_results(experiment_id: str):
        return results_storage.get_experiment_results(experiment_id)

    @app.get("/results")
    async def list_results():
        return results_storage.get_all_results()

    return app

def create_local_app(storage_backend: Optional[StorageBackend] = None, 
                     cdn_backend: Optional[CDNBackend] = None):
    if storage_backend is None:
        storage_backend = LocalStorageBackend()
    if cdn_backend is None:
        cdn_backend = MockCDNBackend()
    return create_app(storage_backend, cdn_backend)

def create_lambda_handler():
    # Retrieve AWS environment variables for S3 and CloudFront
    bucket_name = os.environ['S3_BUCKET']
    distribution_id = os.environ['CLOUDFRONT_DISTRIBUTION_ID']

    storage_backend = S3StorageBackend(bucket_name)
    cdn_backend = CloudFrontCDNBackend(distribution_id)

    app = create_app(storage_backend, cdn_backend)
    return Mangum(app)

# --------------------------
# Handler Selection
# --------------------------

if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    handler = create_lambda_handler()
else:
    app = create_local_app()
