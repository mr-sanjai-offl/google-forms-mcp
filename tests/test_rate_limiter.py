"""Tests for the RateLimiter (token bucket)."""

from google_forms_mcp.infrastructure.rate_limiter import (
    RateLimiter,
    create_default_rate_limiter,
)


def test_acquire_without_configured_bucket():
    """Acquiring from an unconfigured bucket should be a no-op."""
    limiter = RateLimiter()
    # Should not raise or block
    limiter.acquire("nonexistent_bucket")


def test_acquire_consumes_tokens():
    """Verify that tokens are consumed from the bucket."""
    limiter = RateLimiter()
    limiter.configure("test", max_per_minute=60)

    # First acquire should succeed immediately
    limiter.acquire("test", tokens=1.0)


def test_create_default_rate_limiter():
    """Verify default limiter has expected buckets."""
    limiter = create_default_rate_limiter()
    # Should have all expected buckets
    assert "forms_read" in limiter._buckets
    assert "forms_write" in limiter._buckets
    assert "drive_read" in limiter._buckets
    assert "drive_write" in limiter._buckets
    assert "sheets_read" in limiter._buckets
    assert "sheets_write" in limiter._buckets


def test_bucket_refills_over_time():
    """Verify that tokens refill after time passes."""
    limiter = RateLimiter()
    # 60 tokens/min = 1 token/sec
    limiter.configure("test", max_per_minute=60)

    # Consume all tokens
    limiter.acquire("test", tokens=60.0)

    # Tokens should be near zero now
    bucket = limiter._buckets["test"]
    assert bucket.tokens < 1.0

    # Simulate time passing (manually adjust last_refill)
    bucket.last_refill -= 2.0  # Pretend 2 seconds passed

    # After refill, should have ~2 tokens
    limiter._refill(bucket)
    assert bucket.tokens >= 1.5  # Allow some float imprecision
