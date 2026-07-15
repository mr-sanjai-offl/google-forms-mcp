"""Tests for the TokenManager (token persistence layer)."""

import json
from pathlib import Path

from google_forms_mcp.auth.token_manager import TokenManager


def test_save_and_load_token(tmp_path: Path):
    """Test round-trip save and load of a token."""
    token_path = tmp_path / "token.json"
    manager = TokenManager(token_path)

    token_data = {
        "token": "ya29.test-access-token",
        "refresh_token": "1//test-refresh-token",
        "client_id": "test-client-id.apps.googleusercontent.com",
        "client_secret": "test-secret",
    }

    manager.save_token(token_data, profile="default")

    loaded = manager.load_token(profile="default")
    assert loaded is not None
    assert loaded["token"] == "ya29.test-access-token"
    assert loaded["refresh_token"] == "1//test-refresh-token"


def test_load_nonexistent_token(tmp_path: Path):
    """Test loading a token that doesn't exist returns None."""
    token_path = tmp_path / "nonexistent.json"
    manager = TokenManager(token_path)
    assert manager.load_token() is None


def test_delete_token(tmp_path: Path):
    """Test deleting a token profile."""
    token_path = tmp_path / "token.json"
    manager = TokenManager(token_path)

    manager.save_token({"token": "abc"}, profile="test_profile")
    assert manager.load_token(profile="test_profile") is not None

    manager.delete_token(profile="test_profile")
    assert manager.load_token(profile="test_profile") is None


def test_list_profiles(tmp_path: Path):
    """Test listing all profiles."""
    token_path = tmp_path / "token.json"
    manager = TokenManager(token_path)

    manager.save_token({"token": "a"}, profile="alpha")
    manager.save_token({"token": "b"}, profile="beta")

    profiles = manager.list_profiles()
    assert "alpha" in profiles
    assert "beta" in profiles
    assert len(profiles) == 2


def test_multiple_profiles_isolated(tmp_path: Path):
    """Test that multiple profiles don't overwrite each other."""
    token_path = tmp_path / "token.json"
    manager = TokenManager(token_path)

    manager.save_token({"token": "token_a"}, profile="a")
    manager.save_token({"token": "token_b"}, profile="b")

    assert manager.load_token("a")["token"] == "token_a"  # type: ignore[index]
    assert manager.load_token("b")["token"] == "token_b"  # type: ignore[index]


def test_corrupt_token_file(tmp_path: Path):
    """Test graceful handling of a corrupted token file."""
    token_path = tmp_path / "token.json"
    token_path.write_text("THIS IS NOT JSON!!!", encoding="utf-8")

    manager = TokenManager(token_path)
    result = manager.load_token()
    assert result is None


def test_old_format_migration(tmp_path: Path):
    """Test migration from old single-token format."""
    token_path = tmp_path / "token.json"
    old_format = {"token": "old-token", "refresh_token": "old-refresh"}
    token_path.write_text(json.dumps(old_format), encoding="utf-8")

    manager = TokenManager(token_path)
    loaded = manager.load_token(profile="default")
    assert loaded is not None
    assert loaded["token"] == "old-token"
