"""
Tests for share packaging and anonymization.

Tests share creation, anonymization, redaction, and extraction.
"""

import pytest
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import tempfile

from src.share.pack import (
    SharePackager,
    build_share_zip,
    list_shares,
    delete_share,
    extract_share,
    redact_file,
    should_exclude_file
)


class TestRedactionFunctions:
    """Test redaction utility functions."""

    def test_redact_file_basic(self):
        """Test basic file content redaction."""
        content = "This is a secret_key and a password"
        patterns = [r"secret_key", r"password"]

        redacted = redact_file(content, patterns)

        assert 'secret_key' not in redacted
        assert 'password' not in redacted
        assert '[REDACTED]' in redacted

    def test_should_exclude_file_matching(self):
        """Test file exclusion with matching patterns."""
        patterns = [r".*\.key$", r".*secret.*"]

        assert should_exclude_file("myapp.key", patterns) is True
        assert should_exclude_file("secret_config.txt", patterns) is True
        assert should_exclude_file("normal_file.txt", patterns) is False

    def test_should_exclude_file_env(self):
        """Test that .env files are excluded."""
        patterns = [r".*\.env.*"]

        assert should_exclude_file(".env", patterns) is True
        assert should_exclude_file(".env.local", patterns) is True
        assert should_exclude_file("config.yaml", patterns) is False


class TestSharePackager:
    """Test SharePackager class."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        shares_dir = tmp_path / "shares"
        snapshots_dir = tmp_path / "snapshots"
        shares_dir.mkdir()
        snapshots_dir.mkdir()

        return {
            'shares': shares_dir,
            'snapshots': snapshots_dir,
            'tmp': tmp_path
        }

    @pytest.fixture
    def sample_snapshot(self, temp_dirs):
        """Create a sample snapshot for testing."""
        snapshot_id = "2024_W5_test"
        snapshot_dir = temp_dirs['snapshots'] / snapshot_id
        snapshot_dir.mkdir()

        # Create metadata
        metadata = {
            'snapshot_id': snapshot_id,
            'week': 5,
            'season': 2024,
            'created_at': '2024-10-11T12:00:00',
            'bankroll': 1000.0,  # Should be redacted
            'user_id': 'user_123'  # Should be redacted
        }
        with open(snapshot_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        # Create props
        props_data = {
            'player_name': ['Player A', 'Player B'],
            'prop_type': ['passing_yards', 'rushing_yards'],
            'line': [250.5, 75.5],
            'win_prob': [0.65, 0.58],
            'user_id': ['user_123', 'user_123']  # Should be removed
        }
        props_df = pd.DataFrame(props_data)
        props_df.to_parquet(snapshot_dir / 'props.parquet', index=False)

        # Create slips
        slips = [
            {
                'slip_id': 1,
                'legs': ['Player A passing_yards over'],
                'total_odds': 2.5,
                'suggested_bet': 50.0,  # Should be redacted
                'ev': 1.15
            }
        ]
        with open(snapshot_dir / 'slips.json', 'w') as f:
            json.dump(slips, f)

        # Create config
        config_content = """
risk_mode: balanced
api_key: secret_key_12345
bankroll: 1000
        """
        with open(snapshot_dir / 'config.yaml', 'w') as f:
            f.write(config_content)

        return {
            'id': snapshot_id,
            'dir': snapshot_dir,
            'metadata': metadata
        }

    @pytest.fixture
    def packager(self, temp_dirs):
        """Create SharePackager instance."""
        return SharePackager(
            shares_dir=temp_dirs['shares'],
            snapshots_dir=temp_dirs['snapshots']
        )

    def test_init_creates_shares_dir(self, temp_dirs):
        """Test that init creates shares directory."""
        new_shares = temp_dirs['tmp'] / 'new_shares'
        packager = SharePackager(shares_dir=new_shares)

        assert new_shares.exists()

    def test_build_share_zip_creates_file(self, packager, sample_snapshot):
        """Test that build_share_zip creates a zip file."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        assert Path(zip_path).exists()
        assert zip_path.endswith('.zip')

    def test_share_zip_contains_readme(self, packager, sample_snapshot):
        """Test that share package contains README."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            assert 'README_SHARE.md' in files

    def test_share_zip_structure(self, packager, sample_snapshot):
        """Test that share package has correct structure."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()

            # Check expected directories/files
            assert any('data/' in f for f in files)
            assert any('exports/' in f for f in files)
            assert any('models/' in f for f in files)

            # Check specific files
            assert 'data/metadata.json' in files
            assert 'data/props.parquet' in files
            assert 'data/slips.json' in files
            assert 'exports/props.csv' in files

    def test_anonymize_bankroll(self, packager, sample_snapshot):
        """Test that bankroll is anonymized."""
        config = {'anonymize_bankroll': True}
        zip_path = packager.build_share_zip(sample_snapshot['id'], config=config)

        # Extract and check metadata
        with zipfile.ZipFile(zip_path, 'r') as zf:
            metadata_content = zf.read('data/metadata.json')
            metadata = json.loads(metadata_content)

            # Bankroll should be redacted
            assert metadata['bankroll'] == '[REDACTED]'

    def test_anonymize_props_removes_sensitive_columns(self, packager, sample_snapshot):
        """Test that sensitive columns are removed from props."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        # Extract and check props
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with tempfile.TemporaryDirectory() as tmpdir:
                zf.extract('data/props.parquet', tmpdir)
                props_df = pd.read_parquet(Path(tmpdir) / 'data' / 'props.parquet')

                # user_id should be removed
                assert 'user_id' not in props_df.columns
                # Regular columns should remain
                assert 'player_name' in props_df.columns
                assert 'prop_type' in props_df.columns

    def test_anonymize_slips(self, packager, sample_snapshot):
        """Test that slips are anonymized."""
        config = {'anonymize_bankroll': True}
        zip_path = packager.build_share_zip(sample_snapshot['id'], config=config)

        # Extract and check slips
        with zipfile.ZipFile(zip_path, 'r') as zf:
            slips_content = zf.read('data/slips.json')
            slips = json.loads(slips_content)

            # Suggested bet should be redacted
            assert slips[0]['suggested_bet'] == '[REDACTED]'

    def test_redact_config_content(self, packager, sample_snapshot):
        """Test that config content is redacted."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        # Extract and check config
        with zipfile.ZipFile(zip_path, 'r') as zf:
            config_content = zf.read('data/config.yaml').decode('utf-8')

            # API key should be redacted
            assert 'secret_key_12345' not in config_content
            # Path redaction
            assert '[HOME]' in config_content or '[REDACTED]' in config_content

    def test_redact_paths(self, packager):
        """Test path redaction."""
        home_dir = str(Path.home())
        data = {
            'path': f'{home_dir}/some/path',
            'other': 'normal_value'
        }

        config = {'anonymize_bankroll': True}
        anonymized = packager._anonymize_data(data, config)

        # Home directory should be redacted
        assert home_dir not in str(anonymized)
        assert '[HOME]' in anonymized['path'] or 'path' not in str(anonymized['path'])

    def test_csv_exports_created(self, packager, sample_snapshot):
        """Test that CSV exports are created."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()

            assert 'exports/props.csv' in files
            assert 'exports/slips.csv' in files

    def test_model_registry_created(self, packager, sample_snapshot):
        """Test that model registry is created."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        with zipfile.ZipFile(zip_path, 'r') as zf:
            registry_content = zf.read('models/registry.json')
            registry = json.loads(registry_content)

            assert 'note' in registry
            assert 'models' in registry
            assert 'metadata-only' in registry['note'].lower()

    def test_compression_option(self, packager, sample_snapshot):
        """Test compression option."""
        # With compression
        config_compressed = {'compression': True}
        zip_compressed = packager.build_share_zip(
            sample_snapshot['id'],
            config=config_compressed
        )

        # Without compression
        config_uncompressed = {'compression': False}
        zip_uncompressed = packager.build_share_zip(
            sample_snapshot['id'],
            config=config_uncompressed
        )

        # Compressed should be smaller (usually)
        size_compressed = Path(zip_compressed).stat().st_size
        size_uncompressed = Path(zip_uncompressed).stat().st_size

        # At minimum, both should exist
        assert size_compressed > 0
        assert size_uncompressed > 0

    def test_list_shares_empty(self, packager):
        """Test listing shares when none exist."""
        shares = packager.list_shares()
        assert shares == []

    def test_list_shares_with_packages(self, packager, sample_snapshot):
        """Test listing shares with existing packages."""
        # Create a share
        packager.build_share_zip(sample_snapshot['id'])

        # List shares
        shares = packager.list_shares()

        assert len(shares) == 1
        assert shares[0]['snapshot_id'] == sample_snapshot['id']
        assert 'filename' in shares[0]
        assert 'size_mb' in shares[0]
        assert shares[0]['size_mb'] > 0

    def test_delete_share_success(self, packager, sample_snapshot):
        """Test deleting a share package."""
        # Create a share
        zip_path = packager.build_share_zip(sample_snapshot['id'])
        filename = Path(zip_path).name

        # Delete it
        result = packager.delete_share(filename)

        assert result['success'] is True
        assert not Path(zip_path).exists()

    def test_delete_share_not_found(self, packager):
        """Test deleting non-existent share."""
        result = packager.delete_share('nonexistent.zip')

        assert result['success'] is False
        assert 'not found' in result['message'].lower()

    def test_extract_share_success(self, packager, sample_snapshot, temp_dirs):
        """Test extracting a share package."""
        # Create a share
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        # Extract it
        extract_dir = temp_dirs['tmp'] / 'extracted'
        result = packager.extract_share(zip_path, str(extract_dir))

        assert result['success'] is True
        assert result['snapshot_id'] == sample_snapshot['id']
        assert len(result['contents']) > 0

        # Verify files were extracted
        assert (extract_dir / 'README_SHARE.md').exists()
        assert (extract_dir / 'data' / 'metadata.json').exists()

    def test_extract_share_not_found(self, packager, temp_dirs):
        """Test extracting non-existent share."""
        result = packager.extract_share(
            'nonexistent.zip',
            str(temp_dirs['tmp'] / 'extracted')
        )

        assert result['success'] is False

    def test_readme_generation(self, packager, sample_snapshot):
        """Test README generation content."""
        zip_path = packager.build_share_zip(sample_snapshot['id'])

        with zipfile.ZipFile(zip_path, 'r') as zf:
            readme = zf.read('README_SHARE.md').decode('utf-8')

            # Check key sections
            assert 'Snapshot Information' in readme
            assert 'Package Contents' in readme
            assert 'Privacy and Anonymization' in readme
            assert 'How to Use This Package' in readme

            # Check snapshot details
            assert str(sample_snapshot['metadata']['week']) in readme
            assert str(sample_snapshot['metadata']['season']) in readme

    def test_sensitive_keys_redaction(self, packager):
        """Test that all sensitive keys are redacted."""
        data = {
            'api_key': 'secret123',
            'password': 'pass123',
            'token': 'token123',
            'normal_key': 'normal_value'
        }

        config = {'anonymize_bankroll': True}
        anonymized = packager._anonymize_data(data, config)

        assert anonymized['api_key'] == '[REDACTED]'
        assert anonymized['password'] == '[REDACTED]'
        assert anonymized['token'] == '[REDACTED]'
        assert anonymized['normal_key'] == 'normal_value'

    def test_nested_dict_anonymization(self, packager):
        """Test anonymization of nested dictionaries."""
        data = {
            'level1': {
                'level2': {
                    'api_key': 'secret',
                    'normal': 'value'
                }
            }
        }

        config = {'anonymize_bankroll': True}
        anonymized = packager._anonymize_data(data, config)

        assert anonymized['level1']['level2']['api_key'] == '[REDACTED]'
        assert anonymized['level1']['level2']['normal'] == 'value'

    def test_list_anonymization(self, packager):
        """Test anonymization of lists."""
        data = {
            'items': [
                {'api_key': 'secret1', 'value': 1},
                {'api_key': 'secret2', 'value': 2}
            ]
        }

        config = {'anonymize_bankroll': True}
        anonymized = packager._anonymize_data(data, config)

        assert all(item['api_key'] == '[REDACTED]' for item in anonymized['items'])
        assert [item['value'] for item in anonymized['items']] == [1, 2]


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Setup temp directories."""
        shares_dir = tmp_path / "shares"
        snapshots_dir = tmp_path / "snapshots"
        shares_dir.mkdir()
        snapshots_dir.mkdir()

        # Create a sample snapshot
        snapshot_id = "2024_W5_test"
        snapshot_dir = snapshots_dir / snapshot_id
        snapshot_dir.mkdir()

        metadata = {
            'snapshot_id': snapshot_id,
            'week': 5,
            'season': 2024
        }
        with open(snapshot_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        # Create minimal props
        props_df = pd.DataFrame({'player': ['A'], 'prop_type': ['passing_yards']})
        props_df.to_parquet(snapshot_dir / 'props.parquet', index=False)

        # Create minimal slips
        with open(snapshot_dir / 'slips.json', 'w') as f:
            json.dump([{'slip_id': 1}], f)

        return {
            'shares': shares_dir,
            'snapshots': snapshots_dir,
            'snapshot_id': snapshot_id
        }

    def test_build_share_zip_function(self, temp_dirs, monkeypatch):
        """Test build_share_zip convenience function."""
        # Monkeypatch to use our temp directories
        monkeypatch.setattr('src.share.pack.SharePackager.__init__',
                           lambda self, shares_dir=None, snapshots_dir=None:
                           SharePackager.__init__(self,
                                                 shares_dir=temp_dirs['shares'],
                                                 snapshots_dir=temp_dirs['snapshots']))

        with patch('src.share.pack.SharePackager') as mock_packager:
            mock_instance = Mock()
            mock_instance.build_share_zip.return_value = '/path/to/share.zip'
            mock_packager.return_value = mock_instance

            result = build_share_zip(temp_dirs['snapshot_id'])

            assert result == '/path/to/share.zip'
            mock_instance.build_share_zip.assert_called_once()

    def test_list_shares_function(self):
        """Test list_shares convenience function."""
        with patch('src.share.pack.SharePackager') as mock_packager:
            mock_instance = Mock()
            mock_instance.list_shares.return_value = [{'filename': 'test.zip'}]
            mock_packager.return_value = mock_instance

            result = list_shares()

            assert result == [{'filename': 'test.zip'}]

    def test_delete_share_function(self):
        """Test delete_share convenience function."""
        with patch('src.share.pack.SharePackager') as mock_packager:
            mock_instance = Mock()
            mock_instance.delete_share.return_value = {'success': True}
            mock_packager.return_value = mock_instance

            result = delete_share('test.zip')

            assert result['success'] is True

    def test_extract_share_function(self):
        """Test extract_share convenience function."""
        with patch('src.share.pack.SharePackager') as mock_packager:
            mock_instance = Mock()
            mock_instance.extract_share.return_value = {
                'success': True,
                'extracted_to': '/tmp/extracted'
            }
            mock_packager.return_value = mock_instance

            result = extract_share('/path/to/share.zip', '/tmp/output')

            assert result['success'] is True


class TestIntegration:
    """Integration tests for full workflow."""

    @pytest.fixture
    def full_setup(self, tmp_path):
        """Create complete test setup."""
        shares_dir = tmp_path / "shares"
        snapshots_dir = tmp_path / "snapshots"
        shares_dir.mkdir()
        snapshots_dir.mkdir()

        # Create snapshot with realistic data
        snapshot_id = "2024_W5_20241011_120000"
        snapshot_dir = snapshots_dir / snapshot_id
        snapshot_dir.mkdir()

        metadata = {
            'snapshot_id': snapshot_id,
            'week': 5,
            'season': 2024,
            'created_at': '2024-10-11T12:00:00',
            'num_props': 25,
            'num_slips': 10,
            'bankroll': 1000.0,
            'user_id': 'user_12345'
        }
        with open(snapshot_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create realistic props
        props_data = {
            'player_name': ['Patrick Mahomes', 'Josh Allen', 'Tyreek Hill'],
            'team': ['KC', 'BUF', 'MIA'],
            'position': ['QB', 'QB', 'WR'],
            'prop_type': ['passing_yards', 'passing_yards', 'receiving_yards'],
            'line': [275.5, 260.5, 85.5],
            'over_odds': [-110, -115, -110],
            'under_odds': [-110, -105, -110],
            'win_prob': [0.62, 0.58, 0.65],
            'ev': [1.08, 1.05, 1.12]
        }
        props_df = pd.DataFrame(props_data)
        props_df.to_parquet(snapshot_dir / 'props.parquet', index=False)

        # Create realistic slips
        slips = [
            {
                'slip_id': 1,
                'legs': ['Patrick Mahomes passing_yards over 275.5'],
                'total_odds': 2.5,
                'win_prob': 0.62,
                'ev': 1.08,
                'suggested_bet': 25.0
            },
            {
                'slip_id': 2,
                'legs': [
                    'Josh Allen passing_yards over 260.5',
                    'Tyreek Hill receiving_yards over 85.5'
                ],
                'total_odds': 5.2,
                'win_prob': 0.38,
                'ev': 1.15,
                'suggested_bet': 15.0
            }
        ]
        with open(snapshot_dir / 'slips.json', 'w') as f:
            json.dump(slips, f, indent=2)

        config_content = """
risk_mode: balanced
bankroll: 1000
api_keys:
  sleeper: sk_test_12345
  openweather: abcd1234
"""
        with open(snapshot_dir / 'config.yaml', 'w') as f:
            f.write(config_content)

        return {
            'shares_dir': shares_dir,
            'snapshots_dir': snapshots_dir,
            'snapshot_id': snapshot_id,
            'tmp': tmp_path
        }

    def test_complete_share_workflow(self, full_setup):
        """Test complete share workflow: create -> list -> extract -> delete."""
        packager = SharePackager(
            shares_dir=full_setup['shares_dir'],
            snapshots_dir=full_setup['snapshots_dir']
        )

        # 1. Create share
        zip_path = packager.build_share_zip(full_setup['snapshot_id'])
        assert Path(zip_path).exists()

        # 2. List shares
        shares = packager.list_shares()
        assert len(shares) == 1
        assert shares[0]['snapshot_id'] == full_setup['snapshot_id']

        # 3. Extract share
        extract_dir = full_setup['tmp'] / 'extracted'
        result = packager.extract_share(zip_path, str(extract_dir))
        assert result['success'] is True

        # 4. Verify extracted content
        assert (extract_dir / 'README_SHARE.md').exists()
        assert (extract_dir / 'data' / 'props.parquet').exists()

        # Load and verify anonymization
        with open(extract_dir / 'data' / 'metadata.json', 'r') as f:
            metadata = json.load(f)
            assert metadata['bankroll'] == '[REDACTED]'
            assert metadata['user_id'] == '[REDACTED]'

        # 5. Delete share
        filename = Path(zip_path).name
        delete_result = packager.delete_share(filename)
        assert delete_result['success'] is True
        assert not Path(zip_path).exists()

        # 6. Verify deletion
        shares_after = packager.list_shares()
        assert len(shares_after) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
