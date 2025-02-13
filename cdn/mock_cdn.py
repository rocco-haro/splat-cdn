# cdn/mock_cdn.py
# used for local experiments.
import os
from dataclasses import dataclass
from enum import Enum
import time
from typing import Dict, Optional, Tuple
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class CacheArchitecture(str, Enum):
    SINGLE_TIER = "single_tier"  # L1 only
    TWO_TIER = "two_tier"       # L1 + L2

@dataclass
class CacheConfig:
    architecture: CacheArchitecture
    l1_latency_ms: int = 10
    l2_latency_ms: int = 50
    origin_latency_ms: int = 500
    l1_ttl: int = 3600
    l2_ttl: int = 7200

@dataclass
class CacheEntry:
    content: bytes
    timestamp: float
    ttl: int  # seconds
    
    def is_valid(self) -> bool:
        return time.time() - self.timestamp < self.ttl

class CacheMetrics:
    def __init__(self):
        self.l1_hits = 0
        self.l1_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.origin_hits = 0
    
    def to_dict(self):
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "origin_hits": self.origin_hits,
            "l1_hit_rate": self.l1_hits / (self.l1_hits + self.l1_misses) if (self.l1_hits + self.l1_misses) > 0 else 0,
            "l2_hit_rate": self.l2_hits / (self.l2_hits + self.l2_misses) if (self.l2_hits + self.l2_misses) > 0 else 0
        }

class MockCache:
    def __init__(self, name: str, latency_ms: int, ttl: int):
        self.name = name
        self.latency_ms = latency_ms
        self.ttl = ttl
        self._storage: Dict[str, CacheEntry] = {}
    
    async def get(self, key: str) -> Optional[bytes]:
        await asyncio.sleep(self.latency_ms / 1000)  # Simulate network latency
        
        if key in self._storage:
            entry = self._storage[key]
            if entry.is_valid():
                return entry.content
            else:
                del self._storage[key]
        return None
    
    async def put(self, key: str, content: bytes) -> None:
        await asyncio.sleep(self.latency_ms / 1000)
        self._storage[key] = CacheEntry(
            content=content,
            timestamp=time.time(),
            ttl=self.ttl
        )

class MockCDN:
    def __init__(self, config: CacheConfig, base_path: str = "./../mock-data-generator/generated/experiment_A"):
        self.config = config
        self.metrics = CacheMetrics()
        self.base_path = base_path

        self._cache_lock = asyncio.Lock()
        
        # L1 cache (edge)
        self.l1_cache = MockCache("edge", config.l1_latency_ms, config.l1_ttl)
        
        # L2 cache (regional) - only created for two-tier architecture
        self.l2_cache = (
            MockCache("regional", config.l2_latency_ms, config.l2_ttl)
            if config.architecture == CacheArchitecture.TWO_TIER
            else None
        )

    async def get_content(self, key: str) -> Tuple[bytes, str]:
        async with self._cache_lock:
            # Try L1 cache first
            content = await self.l1_cache.get(key)
            if content:
                self.metrics.l1_hits += 1
                return content, "l1_hit"
            
            self.metrics.l1_misses += 1
                
            # Try L2 cache if we're using two-tier architecture
            if self.config.architecture == CacheArchitecture.TWO_TIER:
                content = await self.l2_cache.get(key)
                if content:
                    self.metrics.l2_hits += 1
                    # Actually await the L1 cache population
                    await self.l1_cache.put(key, content)
                    return content, "l2_hit"
                self.metrics.l2_misses += 1
                
            # Fallback to "origin" (filesystem)
            await asyncio.sleep(self.config.origin_latency_ms / 1000)
            try:
                # Load from filesystem
                splat_path = os.path.join(self.base_path, "splats", key, "splat.bin")
                if not os.path.exists(splat_path):
                    raise HTTPException(status_code=404, detail="Content not found")
                    
                with open(splat_path, 'rb') as f:
                    content = f.read()
                    
                self.metrics.origin_hits += 1
                
                # Populate caches and await completion
                await self.l1_cache.put(key, content)
                if self.config.architecture == CacheArchitecture.TWO_TIER:
                    await self.l2_cache.put(key, content)
                    
                return content, "origin_hit"
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Content not found: {str(e)}")

    async def put_content(self, key: str, content: bytes) -> None:
        """Store content to origin and update caches"""
        # Instead of async create_task, wait for the puts to complete
        await self.l1_cache.put(key, content)
        if self.config.architecture == CacheArchitecture.TWO_TIER:
            await self.l2_cache.put(key, content)

    def get_metrics(self) -> dict:
        return self.metrics.to_dict()

# FastAPI app for mock CDN
app = FastAPI()

@app.get("/status")
async def get_status(request: Request):
    return {
        "protocol": request.scope.get("http_version", "unknown"),
        "transport": request.scope.get("type", "unknown"),
        "client": request.scope.get("client", "unknown"),
        "server": request.scope.get("server", "unknown"),
        "scheme": request.scope.get("scheme", "unknown"),
        "headers": dict(request.headers)
    }

@app.middleware("http")
async def add_http3_headers(request: Request, call_next):
    response = await call_next(request)
    # Advertise HTTP/3 on the same port
    alt_svc_header = 'h3=":8000"; ma=3600'
    response.headers.update({
        "Alt-Svc": alt_svc_header,
        "Server": "hypercorn-h3",
        "Upgrade": "h3",
        "X-HTTP3-Available": "true",
        "X-Available-Protocols": "h3,h2,http/1.1"
    })
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create two CDN instances with different configurations
single_tier_cdn = MockCDN(CacheConfig(architecture=CacheArchitecture.SINGLE_TIER))
two_tier_cdn = MockCDN(CacheConfig(architecture=CacheArchitecture.TWO_TIER))

class ContentUpload(BaseModel):
    key: str
    content: str  # Base64 encoded content

@app.get("/single-tier/content/{key}")
async def get_content_single_tier(key: str, request: Request):
    content, cache_status = await single_tier_cdn.get_content(key)
    return {
        "content": content.hex(),
        "cache_status": cache_status,
        "protocol": request.scope.get("http_version", "unknown"),
        "headers": dict(request.headers),
        "client": request.scope.get("client", None),
        "scheme": request.scope.get("scheme", None),
        "transport": request.scope.get("type", None)
    }

@app.get("/two-tier/content/{key}")
async def get_content_two_tier(key: str, request: Request):
    content, cache_status = await two_tier_cdn.get_content(key)
    return {
        "content": content.hex(),
        "cache_status": cache_status,
        "protocol": request.scope.get("http_version", "unknown"),
        "headers": dict(request.headers),
        "client": request.scope.get("client", None),
        "scheme": request.scope.get("scheme", None),
        "transport": request.scope.get("type", None)
    }

@app.put("/content")
async def upload_content(upload: ContentUpload):
    # Upload to both CDNs
    await single_tier_cdn.put_content(upload.key, upload.content.encode())
    await two_tier_cdn.put_content(upload.key, upload.content.encode())
    return {"status": "success"}

@app.get("/metrics")
async def get_metrics():
    return {
        "single_tier": single_tier_cdn.get_metrics(),
        "two_tier": two_tier_cdn.get_metrics()
    }

if __name__ == "__main__":
    import hypercorn.asyncio
    import hypercorn.config
    import logging
    import socket
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    def test_port(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return True
        except:
            logger.error(f"Port {port} is not available")
            return False
    
    for port in [8000, 4433]:
        if not test_port(port):
            raise RuntimeError(f"Port {port} is not available")
    
    config = hypercorn.config.Config()
    
    # QUIC transport settings
    config.quic_bind = ["0.0.0.0:8000"]
    config.bind = ["0.0.0.0:8000"]
    
    # QUIC parameters
    config.max_incomplete_connection_attempts = 5
    config.h3_max_concurrent_streams = 100
    config.h3_initial_max_data = 1048576  # 1MB
    config.h3_initial_max_stream_data_bidi_local = 262144  # 256KB
    config.h3_initial_max_stream_data_bidi_remote = 262144  # 256KB
    config.h3_initial_max_stream_data_uni = 262144  # 256KB
    
    config.alpn_protocols = ["h3", "h2", "http/1.1"]
    # mkcert
    config.certfile = "cert.pem"
    config.keyfile = "key.pem"
    config.verify_mode = None
    config.debug = True
    config.use_reloader = True
    
    asyncio.run(hypercorn.asyncio.serve(app, config))