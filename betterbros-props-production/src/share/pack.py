"""
Share packaging for anonymized analysis sharing.

Creates zip packages of snapshots with:
- Anonymization of sensitive data
- Redaction of secrets and personal info
- Compression and organization
- README generation
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import zipfile
import shutil
import re
import logging
import os

logger = logging.getLogger(__name__)


class SharePackager:
    """
    Packages analysis for anonymized sharing.
    """

    # Patterns to exclude from share packages
    DEFAULT_EXCLUDE_PATTERNS = [
        r".*secret.*",
        r".*\.key$",
        r".*\.pem$",
        r".*\.env.*",
        r".*credentials.*",
        r".*password.*",
        r".*token.*"
    ]

    # Sensitive keys to redact from JSON/YAML
    SENSITIVE_KEYS = [
        "api_key",
        "api_keys",
        "credentials",
        "password",
        "token",
        "secret",
        "bankroll",
        "balance",
        "user_id",
        "account_id"
    ]

    def __init__(self, shares_dir: Optional[Path] = None, snapshots_dir: Optional[Path] = None):
        """
        Initialize share packager.

        Args:
            shares_dir: Directory to store share packages
            snapshots_dir: Directory containing snapshots
        """
        self.shares_dir = shares_dir or Path("./shares")
        self.snapshots_dir = snapshots_dir or Path("./data/snapshots")
        self.shares_dir.mkdir(parents=True, exist_ok=True)

    def build_share_zip(
        self,
        snapshot_id: str,
        config: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Create anonymized share package from snapshot.

        Args:
            snapshot_id: ID of snapshot to share
            config: Share configuration (from user_prefs.yaml)
            output_dir: Where to save zip file (defaults to shares_dir)

        Returns:
            Path to created zip file

        Package Contents:
        - data/props.parquet (anonymized props)
        - data/slips.json (anonymized slips)
        - data/metadata.json (snapshot metadata)
        - data/config.yaml (snapshot config)
        - exports/props.csv (props as CSV)
        - exports/slips.csv (slips as CSV)
        - reports/summary.md (if exists)
        - models/registry.json (model metadata, not model files)
        - README_SHARE.md (generated - explains contents)
        """
        # Default config
        if config is None:
            config = {
                'anonymize_bankroll': True,
                'include_diagnostics': True,
                'include_trends': True,
                'compression': True,
                'redact_patterns': self.DEFAULT_EXCLUDE_PATTERNS
            }

        # Find snapshot directory
        snapshot_dir = self.snapshots_dir / snapshot_id
        if not snapshot_dir.exists():
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # Create output directory
        output_path = Path(output_dir) if output_dir else self.shares_dir
        output_path.mkdir(parents=True, exist_ok=True)

        # Create temporary directory for package contents
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create package structure
            (tmpdir / "data").mkdir()
            (tmpdir / "exports").mkdir()
            (tmpdir / "reports").mkdir(exist_ok=True)
            (tmpdir / "models").mkdir(exist_ok=True)

            # Load and anonymize metadata
            metadata = self._load_metadata(snapshot_dir)
            anonymized_metadata = self._anonymize_data(metadata, config)
            with open(tmpdir / "data" / "metadata.json", 'w') as f:
                json.dump(anonymized_metadata, f, indent=2, default=str)

            # Copy and anonymize props
            props_file = snapshot_dir / "props.parquet"
            if props_file.exists():
                # Load, anonymize, and save props
                import pandas as pd
                props_df = pd.read_parquet(props_file)
                props_df = self._anonymize_props_df(props_df, config)
                props_df.to_parquet(tmpdir / "data" / "props.parquet", index=False)
                props_df.to_csv(tmpdir / "exports" / "props.csv", index=False)

            # Copy and anonymize slips
            slips_file = snapshot_dir / "slips.json"
            if slips_file.exists():
                with open(slips_file, 'r') as f:
                    slips = json.load(f)
                slips = self._anonymize_slips(slips, config)
                with open(tmpdir / "data" / "slips.json", 'w') as f:
                    json.dump(slips, f, indent=2, default=str)

                # Convert slips to CSV
                self._slips_to_csv(slips, tmpdir / "exports" / "slips.csv")

            # Copy config (redacted)
            config_file = snapshot_dir / "config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_content = f.read()
                config_content = self._redact_content(config_content, config)
                with open(tmpdir / "data" / "config.yaml", 'w') as f:
                    f.write(config_content)

            # Create model registry (metadata only, no actual models)
            self._create_model_registry(tmpdir / "models" / "registry.json")

            # Generate README
            readme_content = self._generate_readme(snapshot_id, anonymized_metadata)
            with open(tmpdir / "README_SHARE.md", 'w') as f:
                f.write(readme_content)

            # Create ZIP file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"share_{snapshot_id}.zip"
            zip_path = output_path / zip_filename

            # Determine compression
            compression = zipfile.ZIP_DEFLATED if config.get('compression', True) else zipfile.ZIP_STORED

            with zipfile.ZipFile(zip_path, 'w', compression) as zipf:
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(tmpdir)

                        # Check if file should be excluded
                        if not self._should_exclude_file(str(arcname), config.get('redact_patterns', [])):
                            zipf.write(file_path, arcname)

            logger.info(f"Created share package: {zip_path}")
            return str(zip_path)

    def _load_metadata(self, snapshot_dir: Path) -> Dict[str, Any]:
        """Load metadata from snapshot."""
        metadata_file = snapshot_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _anonymize_data(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively anonymize sensitive data in a dictionary.

        Args:
            data: Data to anonymize
            config: Configuration with anonymization settings

        Returns:
            Anonymized data
        """
        if not isinstance(data, dict):
            return data

        anonymized = {}

        for key, value in data.items():
            key_lower = key.lower()

            # Check if key is sensitive
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                if config.get('anonymize_bankroll', True):
                    anonymized[key] = "[REDACTED]"
                else:
                    anonymized[key] = value
            elif isinstance(value, dict):
                # Recursively anonymize nested dicts
                anonymized[key] = self._anonymize_data(value, config)
            elif isinstance(value, list):
                # Handle lists
                anonymized[key] = [
                    self._anonymize_data(item, config) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str) and self._is_path(value):
                # Redact absolute paths
                anonymized[key] = self._redact_path(value)
            else:
                anonymized[key] = value

        return anonymized

    def _anonymize_props_df(self, df, config: Dict[str, Any]):
        """Anonymize props DataFrame."""
        import pandas as pd

        # Remove sensitive columns if they exist
        sensitive_cols = ['user_id', 'account_id', 'bet_history', 'bankroll']
        df = df.drop(columns=[c for c in sensitive_cols if c in df.columns], errors='ignore')

        # Redact paths in columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: self._redact_path(str(x)) if isinstance(x, str) and self._is_path(str(x)) else x)

        return df

    def _anonymize_slips(self, slips: List[Dict], config: Dict[str, Any]) -> List[Dict]:
        """Anonymize slips data."""
        anonymized_slips = []

        for slip in slips:
            anonymized_slip = {}

            for key, value in slip.items():
                key_lower = key.lower()

                if any(sensitive in key_lower for sensitive in ['bankroll', 'bet', 'wager', 'stake']):
                    if config.get('anonymize_bankroll', True):
                        anonymized_slip[key] = "[REDACTED]"
                    else:
                        anonymized_slip[key] = value
                elif isinstance(value, dict):
                    anonymized_slip[key] = self._anonymize_data(value, config)
                elif isinstance(value, list):
                    anonymized_slip[key] = [
                        self._anonymize_data(item, config) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    anonymized_slip[key] = value

            anonymized_slips.append(anonymized_slip)

        return anonymized_slips

    def _slips_to_csv(self, slips: List[Dict], output_path: Path) -> None:
        """Convert slips to CSV format."""
        if not slips:
            return

        import pandas as pd

        # Flatten slips for CSV
        flattened = []
        for idx, slip in enumerate(slips):
            flat_slip = {
                'slip_id': idx + 1,
                'legs': len(slip.get('legs', [])),
                'total_odds': slip.get('total_odds', 'N/A'),
                'ev': slip.get('ev', 'N/A'),
                'win_prob': slip.get('win_prob', 'N/A'),
            }
            flattened.append(flat_slip)

        df = pd.DataFrame(flattened)
        df.to_csv(output_path, index=False)

    def _redact_content(self, content: str, config: Dict[str, Any]) -> str:
        """
        Redact sensitive patterns from file content.

        Args:
            content: File content as string
            config: Configuration with redaction patterns

        Returns:
            Content with sensitive data replaced by [REDACTED]
        """
        patterns = config.get('redact_patterns', self.DEFAULT_EXCLUDE_PATTERNS)

        for pattern in patterns:
            # Redact any matches
            content = re.sub(pattern, '[REDACTED]', content, flags=re.IGNORECASE)

        # Redact common secret formats
        # API keys (common formats)
        content = re.sub(r'[A-Za-z0-9_-]{32,}', lambda m: '[REDACTED_KEY]' if 'key' in content.lower() else m.group(0), content)

        # Paths containing user home directory
        home_dir = str(Path.home())
        content = content.replace(home_dir, '[HOME]')

        return content

    def _is_path(self, value: str) -> bool:
        """Check if string looks like a file path."""
        return ('/' in value or '\\' in value) and len(value) > 10

    def _redact_path(self, path: str) -> str:
        """Redact absolute paths to relative paths."""
        home_dir = str(Path.home())
        if home_dir in path:
            path = path.replace(home_dir, '[HOME]')

        # Convert to relative if it's absolute
        if path.startswith('/'):
            parts = path.split('/')
            if len(parts) > 3:
                return './' + '/'.join(parts[-3:])

        return path

    def _should_exclude_file(self, filename: str, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded from share package."""
        for pattern in exclude_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False

    def _create_model_registry(self, output_path: Path) -> None:
        """Create model registry with metadata (no actual models)."""
        registry = {
            "note": "This is a metadata-only registry. Actual model files are not included in share packages.",
            "models": [
                {
                    "name": "xgboost_classifier",
                    "type": "XGBoost",
                    "version": "1.0",
                    "features": "[Feature metadata available in full system]"
                }
            ],
            "last_updated": datetime.now().isoformat()
        }

        with open(output_path, 'w') as f:
            json.dump(registry, f, indent=2)

    def _generate_readme(self, snapshot_id: str, metadata: Dict[str, Any]) -> str:
        """
        Generate README_SHARE.md explaining package contents.

        Args:
            snapshot_id: Snapshot identifier
            metadata: Snapshot metadata

        Returns:
            README content as string
        """
        week = metadata.get('week', 'Unknown')
        season = metadata.get('season', 'Unknown')
        created_at = metadata.get('created_at', 'Unknown')

        readme = f"""# NFL Props Analyzer - Shared Analysis Package

## Snapshot Information

- **Snapshot ID**: {snapshot_id}
- **Week**: {week}
- **Season**: {season}
- **Created**: {created_at}
- **Package Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Package Contents

### Data Files

- **data/props.parquet**: Player props with predictions and analysis
- **data/slips.json**: Generated slip recommendations (JSON format)
- **data/metadata.json**: Snapshot metadata and configuration
- **data/config.yaml**: Analysis configuration (redacted)

### Exports (CSV Format)

- **exports/props.csv**: Props data in CSV format for easy viewing
- **exports/slips.csv**: Slips summary in CSV format

### Reports

- **reports/**: Analysis reports and summaries (if available)

### Models

- **models/registry.json**: Model metadata (actual model files not included)

## Privacy and Anonymization

This package has been anonymized for sharing:

- All bankroll and bet amount information has been redacted
- API keys and credentials have been removed
- Absolute file paths have been converted to relative paths
- User identifiers and account information have been redacted
- Personal information has been scrubbed

## How to Use This Package

### Loading Props Data

```python
import pandas as pd

# Load props from parquet (recommended)
props_df = pd.read_parquet('data/props.parquet')

# Or from CSV
props_df = pd.read_csv('exports/props.csv')

# View props
print(props_df.head())
print(f"Total props: {{len(props_df)}}")
```

### Loading Slips Data

```python
import json

# Load slips
with open('data/slips.json', 'r') as f:
    slips = json.load(f)

# View slips
for i, slip in enumerate(slips[:5]):
    print(f"Slip {{i+1}}:")
    print(f"  Legs: {{slip.get('legs', [])}}")
    print(f"  Total Odds: {{slip.get('total_odds', 'N/A')}}")
    print(f"  EV: {{slip.get('ev', 'N/A')}}")
    print()
```

### Analyzing the Data

```python
# Analyze prop types
prop_types = props_df['prop_type'].value_counts()
print("Prop Type Distribution:")
print(prop_types)

# View top predictions by confidence
top_props = props_df.nlargest(10, 'win_prob')
print("\\nTop 10 Props by Win Probability:")
print(top_props[['player_name', 'prop_type', 'line', 'win_prob']])

# Analyze by position
by_position = props_df.groupby('position').agg({{
    'win_prob': 'mean',
    'player_name': 'count'
}})
print("\\nAnalysis by Position:")
print(by_position)
```

## Package Structure

```
share_{snapshot_id}.zip
├── README_SHARE.md           (this file)
├── data/
│   ├── props.parquet         (main props data)
│   ├── slips.json            (generated slips)
│   ├── metadata.json         (snapshot info)
│   └── config.yaml           (configuration)
├── exports/
│   ├── props.csv             (props as CSV)
│   └── slips.csv             (slips summary)
├── reports/
│   └── (analysis reports if available)
└── models/
    └── registry.json         (model metadata)
```

## Technical Details

- **Props Format**: Parquet (efficient binary format) and CSV
- **Slips Format**: JSON with nested structure
- **Anonymization**: Automatic redaction of sensitive data
- **Compression**: ZIP with DEFLATE compression

## Questions or Issues?

This package was generated by the NFL Props Analyzer system.
For more information about the analysis methodology, refer to the
system documentation or contact the package creator.

## License

This data package is provided for analysis and educational purposes.
Please respect any applicable terms of service for the underlying data sources.

---

Generated by NFL Props Analyzer
{datetime.now().strftime('%Y-%m-%d')}
"""

        return readme

    def list_shares(self) -> List[Dict[str, Any]]:
        """
        List all created share packages.

        Returns:
            List of dicts with:
                - filename: str
                - snapshot_id: str
                - created_at: str
                - size_mb: float
                - path: str
        """
        if not self.shares_dir.exists():
            return []

        shares = []

        for zip_file in self.shares_dir.glob("share_*.zip"):
            stat = zip_file.stat()

            # Extract snapshot_id from filename
            filename = zip_file.name
            snapshot_id = filename.replace('share_', '').replace('.zip', '')

            shares.append({
                'filename': filename,
                'snapshot_id': snapshot_id,
                'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'path': str(zip_file)
            })

        # Sort by creation time (newest first)
        shares.sort(key=lambda x: x['created_at'], reverse=True)

        return shares

    def delete_share(self, filename: str) -> Dict[str, Any]:
        """
        Delete a share package.

        Args:
            filename: Name of share file to delete

        Returns:
            Dict with:
                - success: bool
                - message: str
        """
        zip_path = self.shares_dir / filename

        if not zip_path.exists():
            return {
                'success': False,
                'message': f"Share package not found: {filename}"
            }

        try:
            zip_path.unlink()
            logger.info(f"Deleted share package: {filename}")

            return {
                'success': True,
                'message': f"Share package deleted: {filename}"
            }
        except Exception as e:
            logger.error(f"Failed to delete share package: {e}")
            return {
                'success': False,
                'message': f"Failed to delete: {str(e)}"
            }

    def extract_share(self, zip_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Extract a share package for analysis.

        Args:
            zip_path: Path to share zip file
            output_dir: Directory to extract to

        Returns:
            Dict with:
                - success: bool
                - extracted_to: str
                - snapshot_id: str
                - contents: List[str]
        """
        zip_path_obj = Path(zip_path)

        if not zip_path_obj.exists():
            return {
                'success': False,
                'message': f"Share package not found: {zip_path}",
                'extracted_to': None,
                'snapshot_id': None,
                'contents': []
            }

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path_obj, 'r') as zipf:
                # Get list of files
                contents = zipf.namelist()

                # Extract all files
                zipf.extractall(output_path)

                # Extract snapshot_id from filename
                filename = zip_path_obj.name
                snapshot_id = filename.replace('share_', '').replace('.zip', '')

                logger.info(f"Extracted share package to: {output_path}")

                return {
                    'success': True,
                    'message': f"Extracted {len(contents)} files",
                    'extracted_to': str(output_path),
                    'snapshot_id': snapshot_id,
                    'contents': contents
                }

        except Exception as e:
            logger.error(f"Failed to extract share package: {e}")
            return {
                'success': False,
                'message': f"Failed to extract: {str(e)}",
                'extracted_to': None,
                'snapshot_id': None,
                'contents': []
            }


# Convenience functions

def build_share_zip(
    snapshot_id: str,
    config: Optional[Dict[str, Any]] = None,
    output_dir: str = "shares"
) -> str:
    """
    Create anonymized share package from snapshot.

    Args:
        snapshot_id: ID of snapshot to share
        config: Share configuration (from user_prefs.yaml)
        output_dir: Where to save zip file

    Returns:
        Path to created zip file
    """
    packager = SharePackager()
    return packager.build_share_zip(snapshot_id, config, output_dir)


def list_shares() -> List[Dict[str, Any]]:
    """
    List all created share packages.

    Returns:
        List of dicts with filename, snapshot_id, created_at, size_mb, path
    """
    packager = SharePackager()
    return packager.list_shares()


def delete_share(filename: str) -> Dict[str, Any]:
    """
    Delete a share package.

    Args:
        filename: Share filename to delete

    Returns:
        Dict with success and message
    """
    packager = SharePackager()
    return packager.delete_share(filename)


def extract_share(zip_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Extract a share package for analysis.

    Args:
        zip_path: Path to share zip file
        output_dir: Directory to extract to

    Returns:
        Dict with success, extracted_to, snapshot_id, contents
    """
    packager = SharePackager()
    return packager.extract_share(zip_path, output_dir)


def redact_file(content: str, patterns: List[str]) -> str:
    """
    Redact sensitive patterns from file content.

    Args:
        content: File content as string
        patterns: List of regex patterns to redact

    Returns:
        Content with sensitive data replaced by [REDACTED]
    """
    for pattern in patterns:
        content = re.sub(pattern, '[REDACTED]', content, flags=re.IGNORECASE)
    return content


def should_exclude_file(filename: str, exclude_patterns: List[str]) -> bool:
    """
    Check if file should be excluded from share package.

    Args:
        filename: Name of file
        exclude_patterns: List of regex patterns to exclude

    Returns:
        True if file should be excluded
    """
    for pattern in exclude_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False
