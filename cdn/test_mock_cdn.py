import pytest
import asyncio
import os
import time
from pathlib import Path
from .mock_cdn import (
    MockCDN, 
    CacheConfig, 
    CacheArchitecture,
    MockCache,
    CacheEntry,
    app
)
from fastapi.testclient import TestClient
from fastapi import HTTPException

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory with mock splat data"""
    # Create splat directory structure
    splats_dir = tmp_path / "splats"
    splats_dir.mkdir()
    
    # Create a test splat
    splat_dir = splats_dir / "0_0_0"
    splat_dir.mkdir()
    splat_file = splat_dir / "splat.bin"
    splat_file.write_bytes(b"test splat data")
    
    return tmp_path

@pytest.fixture
def single_tier_cdn(temp_data_dir):
    """Create a single-tier CDN instance"""
    config = CacheConfig(architecture=CacheArchitecture.SINGLE_TIER)
    return MockCDN(config, str(temp_data_dir))

@pytest.fixture
def two_tier_cdn(temp_data_dir):
    """Create a two-tier CDN instance"""
    config = CacheConfig(architecture=CacheArchitecture.TWO_TIER)
    return MockCDN(config, str(temp_data_dir))

@pytest.mark.asyncio
async def test_l1_cache_hit(single_tier_cdn):
    """Test that L1 cache hits work correctly"""
    # First request should be a cache miss (origin hit)
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert content == b"test splat data"
    assert status == "origin_hit"
    assert single_tier_cdn.metrics.l1_misses == 1
    assert single_tier_cdn.metrics.origin_hits == 1
    
    # Second request should be an L1 cache hit
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert content == b"test splat data"
    assert status == "l1_hit"
    assert single_tier_cdn.metrics.l1_hits == 1

@pytest.mark.asyncio
async def test_two_tier_caching(two_tier_cdn):
    """Test that two-tier caching works with L1 and L2 caches"""
    # First request - origin hit, populates both caches
    content, status = await two_tier_cdn.get_content("0_0_0")
    assert status == "origin_hit"
    
    # Clear L1 cache by setting expired TTL
    l1_entry = two_tier_cdn.l1_cache._storage["0_0_0"]
    l1_entry.timestamp = time.time() - 7200  # Expired
    
    # Second request should hit L2
    content, status = await two_tier_cdn.get_content("0_0_0")
    assert status == "l2_hit"
    assert two_tier_cdn.metrics.l2_hits == 1

@pytest.mark.asyncio
async def test_missing_content(single_tier_cdn):
    """Test handling of requests for non-existent splats"""
    with pytest.raises(HTTPException) as exc_info:
        await single_tier_cdn.get_content("nonexistent")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_metrics_accuracy(single_tier_cdn):
    """Test that metrics are tracked accurately"""
    # Make several requests to build up metrics
    await single_tier_cdn.get_content("0_0_0")  # origin hit
    await single_tier_cdn.get_content("0_0_0")  # l1 hit
    await single_tier_cdn.get_content("0_0_0")  # l1 hit
    
    try:
        await single_tier_cdn.get_content("nonexistent")
    except HTTPException:
        pass
    
    metrics = single_tier_cdn.get_metrics()
    assert metrics["l1_hits"] == 2
    assert metrics["l1_misses"] == 2  # One for first request, one for nonexistent
    assert metrics["origin_hits"] == 1
    assert metrics["l1_hit_rate"] == 0.5  # 2 hits out of 4 requests

@pytest.mark.asyncio
async def test_cache_ttl(single_tier_cdn):
    """Test that cache entries expire correctly"""
    # Configure short TTL for testing
    single_tier_cdn.l1_cache.ttl = 1  # 1 second TTL
    
    # First request - origin hit
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "origin_hit"
    
    # Immediate second request - should be cache hit
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "l1_hit"
    
    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    
    # Third request - should be origin hit again
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "origin_hit"

def test_cdn_initialization():
    """Test CDN initialization with different configurations"""
    # Test single-tier configuration
    cdn = MockCDN(CacheConfig(architecture=CacheArchitecture.SINGLE_TIER))
    assert cdn.l2_cache is None
    
    # Test two-tier configuration
    cdn = MockCDN(CacheConfig(architecture=CacheArchitecture.TWO_TIER))
    assert cdn.l2_cache is not None
    assert isinstance(cdn.l2_cache, MockCache)

@pytest.mark.asyncio
async def test_concurrent_requests(single_tier_cdn):
    """Test handling of concurrent requests"""
    # Make multiple concurrent requests
    requests = [single_tier_cdn.get_content("0_0_0") for _ in range(5)]
    results = await asyncio.gather(*requests)
    
    # First request should be origin hit, rest should be cache hits
    assert sum(1 for _, status in results if status == "origin_hit") == 1
    assert sum(1 for _, status in results if status == "l1_hit") == 4

# Integration tests with FastAPI
def test_api_endpoints(temp_data_dir):
    """Test the FastAPI endpoints"""
    client = TestClient(app)
    
    # Test single-tier endpoint
    response = client.get("/single-tier/content/0_0_0")
    assert response.status_code == 200
    assert "cache_status" in response.json()
    
    # Test metrics endpoint
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "single_tier" in response.json()
    assert "two_tier" in response.json()

@pytest.mark.asyncio
async def test_origin_hits_counter(single_tier_cdn):
    """Test that origin hits are counted correctly when content is fetched from filesystem"""
    
    # Initially metrics should show 0 origin hits
    initial_metrics = single_tier_cdn.get_metrics()
    assert initial_metrics["origin_hits"] == 0
    
    # First request should be an origin hit
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "origin_hit"
    
    # Verify metrics after first request
    metrics_after_first = single_tier_cdn.get_metrics()
    assert metrics_after_first["origin_hits"] == 1
    
    # Clear L1 cache by setting expired TTL
    l1_entry = single_tier_cdn.l1_cache._storage["0_0_0"]
    l1_entry.timestamp = time.time() - single_tier_cdn.l1_cache.ttl - 1  # Set to expired
    
    # Second request should be another origin hit since cache is expired
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "origin_hit"
    
    # Verify metrics show two origin hits
    final_metrics = single_tier_cdn.get_metrics()
    assert final_metrics["origin_hits"] == 2
    
    # Additional verification: cache hit shouldn't increment origin hits
    content, status = await single_tier_cdn.get_content("0_0_0")
    assert status == "l1_hit"
    assert single_tier_cdn.get_metrics()["origin_hits"] == 2  # Should remain unchanged