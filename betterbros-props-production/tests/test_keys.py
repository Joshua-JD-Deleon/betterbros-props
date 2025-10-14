"""
Tests for API key management.

Tests key set/get/delete, masking, validation, and security.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import stat

from src.keys.manager import (
    KeyManager,
    keys_set,
    keys_get,
    keys_test,
    keys_list,
    keys_delete,
    mask_api_key,
    read_env_file,
    write_env_file,
    set_file_permissions
)


class TestKeyMasking:
    """Test API key masking functionality."""

    def test_mask_short_key(self):
        """Test masking short keys."""
        key = "abc123"
        masked = mask_api_key(key, show_chars=2)
        # For 6 char key with show_chars=2, result is "ab**23"
        assert masked.startswith("ab")
        assert masked.endswith("23")
        assert "*" in masked

    def test_mask_normal_key(self):
        """Test masking normal length keys."""
        key = "sk_test_1234567890abcdefghijklmnop"
        masked = mask_api_key(key, show_chars=4)
        assert masked.startswith("sk_t")
        assert masked.endswith("mnop")
        assert "*" in masked
        assert len(masked) > 0

    def test_mask_empty_key(self):
        """Test masking empty key."""
        masked = mask_api_key("")
        assert masked == ""

    def test_mask_custom_chars(self):
        """Test masking with custom show_chars."""
        key = "1234567890abcdef"
        masked = mask_api_key(key, show_chars=3)
        assert masked.startswith("123")
        assert masked.endswith("def")


class TestEnvFileOperations:
    """Test .env file read/write operations."""

    def test_read_empty_env_file(self, tmp_path):
        """Test reading non-existent env file."""
        env_path = tmp_path / ".env.test"
        result = read_env_file(str(env_path))
        assert result == {}

    def test_write_and_read_env_file(self, tmp_path):
        """Test writing and reading env file."""
        env_path = tmp_path / ".env.test"

        # Write
        write_env_file(str(env_path), {
            'KEY1': 'value1',
            'KEY2': 'value2'
        })

        # Read
        result = read_env_file(str(env_path))
        assert result['KEY1'] == 'value1'
        assert result['KEY2'] == 'value2'

    def test_update_existing_key(self, tmp_path):
        """Test updating existing key in env file."""
        env_path = tmp_path / ".env.test"

        # Initial write
        write_env_file(str(env_path), {'KEY1': 'value1'})

        # Update
        write_env_file(str(env_path), {'KEY1': 'new_value'})

        # Verify
        result = read_env_file(str(env_path))
        assert result['KEY1'] == 'new_value'

    def test_preserve_comments(self, tmp_path):
        """Test that comments are preserved when updating."""
        env_path = tmp_path / ".env.test"

        # Create file with comments
        with open(env_path, 'w') as f:
            f.write("# This is a comment\n")
            f.write("KEY1=value1\n")
            f.write("# Another comment\n")
            f.write("KEY2=value2\n")

        # Update one key
        env_dict = read_env_file(str(env_path))
        env_dict['KEY1'] = 'updated'
        write_env_file(str(env_path), env_dict)

        # Check comments are preserved
        with open(env_path, 'r') as f:
            content = f.read()
            assert '# This is a comment' in content
            assert '# Another comment' in content

    def test_file_permissions(self, tmp_path):
        """Test setting secure file permissions."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        set_file_permissions(str(test_file), mode=0o600)

        # Check permissions
        file_stat = test_file.stat()
        assert file_stat.st_mode & 0o777 == 0o600


class TestKeyManager:
    """Test KeyManager class."""

    @pytest.fixture
    def temp_env_file(self, tmp_path):
        """Create temporary env file."""
        return tmp_path / ".env.test"

    @pytest.fixture
    def manager(self, temp_env_file):
        """Create KeyManager instance with temp file."""
        return KeyManager(env_file=temp_env_file)

    def test_init_creates_env_file(self, temp_env_file):
        """Test that init creates env file if it doesn't exist."""
        assert not temp_env_file.exists()
        manager = KeyManager(env_file=temp_env_file)
        assert temp_env_file.exists()

    def test_set_valid_key(self, manager):
        """Test setting a valid API key."""
        result = manager.set_key('sleeper', 'test_key_1234567890abcdef')

        assert result['success'] is True
        assert result['provider'] == 'sleeper'
        assert 'successfully' in result['message'].lower()

    def test_set_invalid_provider(self, manager):
        """Test setting key for unknown provider."""
        result = manager.set_key('unknown_provider', 'some_key')

        assert result['success'] is False
        assert 'unknown provider' in result['message'].lower()

    def test_get_key(self, manager):
        """Test getting an API key."""
        # Set a key
        manager.set_key('sleeper', 'test_key_12345')

        # Get it back
        key = manager.get_key('sleeper')
        assert key == 'test_key_12345'

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        # Create fresh manager instance to ensure no key exists
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env.test"
            manager = KeyManager(env_file=env_file)
            key = manager.get_key('sleeper')
            assert key is None

    def test_delete_key(self, manager):
        """Test deleting an API key."""
        # Set a key
        manager.set_key('sleeper', 'test_key_12345')

        # Delete it
        result = manager.delete_key('sleeper')

        assert result['success'] is True
        assert manager.get_key('sleeper') is None or manager.get_key('sleeper') == ''

    def test_delete_nonexistent_key(self, manager):
        """Test deleting a key that doesn't exist."""
        result = manager.delete_key('sleeper')
        # Should still succeed (idempotent)
        assert result['success'] is True

    def test_list_keys(self, manager):
        """Test listing all keys."""
        # Set some keys
        manager.set_key('sleeper', 'key1')
        manager.set_key('openweather', 'key2')

        # List them
        keys = manager.list_keys()

        assert len(keys) == 2
        assert any(k['provider'] == 'sleeper' and k['is_set'] for k in keys)
        assert any(k['provider'] == 'openweather' and k['is_set'] for k in keys)

    def test_list_keys_masks_values(self, manager):
        """Test that list_keys masks API key values."""
        manager.set_key('sleeper', 'very_secret_key_12345')

        keys = manager.list_keys()
        sleeper_key = next(k for k in keys if k['provider'] == 'sleeper')

        assert sleeper_key['masked_value'] is not None
        assert 'very_secret_key_12345' not in sleeper_key['masked_value']
        assert '*' in sleeper_key['masked_value']

    @patch('httpx.Client')
    def test_test_sleeper_key_success(self, mock_client, manager):
        """Test testing Sleeper API key (success)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'season': '2024', 'week': '5'}

        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context

        # Set key and test
        manager.set_key('sleeper', 'test_key')
        result = manager.test_key('sleeper')

        assert result['valid'] is True
        assert result['provider'] == 'sleeper'
        assert 'valid' in result['message'].lower()

    @patch('httpx.Client')
    def test_test_sleeper_key_failure(self, mock_client, manager):
        """Test testing Sleeper API key (failure)."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401

        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context

        # Set key and test
        manager.set_key('sleeper', 'bad_key')
        result = manager.test_key('sleeper')

        assert result['valid'] is False

    @patch('httpx.Client')
    def test_test_openweather_key_success(self, mock_client, manager):
        """Test testing OpenWeather API key (success)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'London',
            'main': {'temp': 15.5}
        }

        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context

        # Set key and test
        manager.set_key('openweather', 'a' * 32)  # 32 char key
        result = manager.test_key('openweather')

        assert result['valid'] is True
        assert result['provider'] == 'openweather'

    @patch('httpx.Client')
    def test_test_openweather_key_unauthorized(self, mock_client, manager):
        """Test testing OpenWeather API key (unauthorized)."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401

        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context

        # Set key and test
        manager.set_key('openweather', 'bad_key_' + 'a' * 24)
        result = manager.test_key('openweather')

        assert result['valid'] is False
        assert 'invalid' in result['message'].lower() or 'unauthorized' in result['message'].lower()

    def test_test_missing_key(self):
        """Test testing API key that hasn't been set."""
        # Create fresh manager to ensure key is not set
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env.test"
            manager = KeyManager(env_file=env_file)
            result = manager.test_key('sleeper')

            assert result['valid'] is False
            assert 'no api key' in result['message'].lower()

    def test_secure_permissions_on_create(self, temp_env_file):
        """Test that env file has secure permissions on creation."""
        manager = KeyManager(env_file=temp_env_file)

        # Check permissions (should be 600)
        file_stat = temp_env_file.stat()
        # On some systems, the exact permissions might vary
        # Just check that it's not world-readable
        mode = file_stat.st_mode
        assert not (mode & stat.S_IROTH)  # Not world-readable
        assert not (mode & stat.S_IWOTH)  # Not world-writable


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.fixture
    def temp_env_file(self, tmp_path):
        """Create temporary env file path."""
        return str(tmp_path / ".env.test")

    def test_keys_set(self, temp_env_file):
        """Test keys_set convenience function."""
        result = keys_set('sleeper', 'test_key', env_file=temp_env_file)

        assert result['success'] is True
        assert result['provider'] == 'sleeper'

    def test_keys_get(self, temp_env_file):
        """Test keys_get convenience function."""
        keys_set('sleeper', 'test_key_123', env_file=temp_env_file)

        key = keys_get('sleeper', env_file=temp_env_file)
        assert key == 'test_key_123'

    def test_keys_list(self, temp_env_file):
        """Test keys_list convenience function."""
        keys_set('sleeper', 'key1', env_file=temp_env_file)

        result = keys_list(env_file=temp_env_file)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_keys_delete(self, temp_env_file):
        """Test keys_delete convenience function."""
        keys_set('sleeper', 'test_key', env_file=temp_env_file)

        result = keys_delete('sleeper', env_file=temp_env_file)

        assert result['success'] is True

    @patch('httpx.Client')
    def test_keys_test(self, mock_client, temp_env_file):
        """Test keys_test convenience function."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'season': '2024', 'week': '5'}

        mock_context = MagicMock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context

        keys_set('sleeper', 'test_key', env_file=temp_env_file)
        result = keys_test('sleeper', env_file=temp_env_file)

        assert 'valid' in result
        assert 'provider' in result


class TestSecurityFeatures:
    """Test security features."""

    def test_never_log_actual_key(self, tmp_path, caplog):
        """Test that actual keys are never logged."""
        import logging
        caplog.set_level(logging.DEBUG)

        env_file = tmp_path / ".env.test"
        manager = KeyManager(env_file=env_file)

        secret_key = "super_secret_key_12345"
        manager.set_key('sleeper', secret_key)

        # Check that secret key doesn't appear in logs
        for record in caplog.records:
            assert secret_key not in record.message

    def test_key_not_in_error_messages(self, tmp_path):
        """Test that keys don't appear in error messages."""
        env_file = tmp_path / ".env.test"
        manager = KeyManager(env_file=env_file)

        secret_key = "super_secret_key_12345"
        manager.set_key('sleeper', secret_key)

        # Even when testing fails, key shouldn't appear
        with patch('httpx.Client') as mock_client:
            mock_client.side_effect = Exception("Network error")

            result = manager.test_key('sleeper')

            # Result message shouldn't contain the actual key
            assert secret_key not in str(result)


class TestIntegration:
    """Integration tests."""

    def test_full_key_lifecycle(self, tmp_path):
        """Test complete key lifecycle: set -> get -> test -> delete."""
        env_file = tmp_path / ".env.test"
        manager = KeyManager(env_file=env_file)

        # 1. Set key
        set_result = manager.set_key('sleeper', 'test_key_123')
        assert set_result['success'] is True

        # 2. Get key
        key = manager.get_key('sleeper')
        assert key == 'test_key_123'

        # 3. List keys (check it appears masked)
        keys = manager.list_keys()
        sleeper = next(k for k in keys if k['provider'] == 'sleeper')
        assert sleeper['is_set'] is True
        assert '*' in sleeper['masked_value']

        # 4. Delete key
        delete_result = manager.delete_key('sleeper')
        assert delete_result['success'] is True

        # 5. Verify deleted
        key_after = manager.get_key('sleeper')
        assert key_after is None or key_after == ''

    def test_multiple_keys(self, tmp_path):
        """Test managing multiple keys simultaneously."""
        env_file = tmp_path / ".env.test"
        manager = KeyManager(env_file=env_file)

        # Set multiple keys
        manager.set_key('sleeper', 'sleeper_key')
        manager.set_key('openweather', 'weather_key_' + 'a' * 20)

        # Verify both are set
        assert manager.get_key('sleeper') == 'sleeper_key'
        assert manager.get_key('openweather').startswith('weather_key')

        # List should show both
        keys = manager.list_keys()
        assert len([k for k in keys if k['is_set']]) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
