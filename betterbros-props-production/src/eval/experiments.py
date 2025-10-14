"""
Experiment tracking for model evaluation and slip generation.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import sqlite3
import pandas as pd


class ExperimentTracker:
    """Tracks experiments and configuration changes."""

    def __init__(self, tracking_dir: Optional[Path] = None, use_sqlite: bool = False):
        """
        Initialize experiment tracker.

        Args:
            tracking_dir: Directory for tracking files
            use_sqlite: Use SQLite instead of JSONL
        """
        self.tracking_dir = tracking_dir or Path("./experiments")
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.use_sqlite = use_sqlite

        if use_sqlite:
            self.db_path = self.tracking_dir / "experiments.sqlite"
            self._init_db()
        else:
            self.jsonl_path = self.tracking_dir / "tracking.jsonl"

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                snapshot_id TEXT,
                week INTEGER,
                season INTEGER,
                risk_mode TEXT,
                bankroll REAL,
                num_props INTEGER,
                num_slips INTEGER,
                event_type TEXT,
                metrics TEXT,
                config TEXT,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    def record_event(self, event: Dict[str, Any]) -> None:
        """
        Log experiment event.

        Args:
            event: Dictionary with experiment data
                Required fields:
                    - event_type: Type of event
                Optional fields:
                    - timestamp: ISO timestamp (auto-generated if missing)
                    - snapshot_id: Snapshot identifier
                    - week: Week number
                    - season: Season year
                    - risk_mode: Risk mode used
                    - bankroll: Current bankroll
                    - num_props: Number of props
                    - num_slips: Number of slips generated
                    - metrics: Performance metrics dict
                    - config: Configuration dict
                    - notes: Additional notes
        """
        # Add timestamp if not present
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()

        if self.use_sqlite:
            self._record_to_sqlite(event)
        else:
            self._record_to_jsonl(event)

    def _record_to_sqlite(self, event: Dict[str, Any]) -> None:
        """Record event to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO experiments (
                timestamp, snapshot_id, week, season, risk_mode,
                bankroll, num_props, num_slips, event_type,
                metrics, config, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get('timestamp'),
            event.get('snapshot_id'),
            event.get('week'),
            event.get('season'),
            event.get('risk_mode'),
            event.get('bankroll'),
            event.get('num_props'),
            event.get('num_slips'),
            event.get('event_type'),
            json.dumps(event.get('metrics', {})),
            json.dumps(event.get('config', {})),
            event.get('notes')
        ))

        conn.commit()
        conn.close()

    def _record_to_jsonl(self, event: Dict[str, Any]) -> None:
        """Record event to JSONL file."""
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def query_experiments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Query experiment history.

        Args:
            filters: Optional filters to apply
                - event_type: Filter by event type
                - week: Filter by week
                - season: Filter by season
                - risk_mode: Filter by risk mode
                - start_date: ISO timestamp for start
                - end_date: ISO timestamp for end
            limit: Maximum number of results

        Returns:
            DataFrame with experiment history
        """
        if self.use_sqlite:
            return self._query_sqlite(filters, limit)
        else:
            return self._query_jsonl(filters, limit)

    def _query_sqlite(
        self,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> pd.DataFrame:
        """Query SQLite database."""
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM experiments WHERE 1=1"
        params = []

        if filters:
            if 'event_type' in filters:
                query += " AND event_type = ?"
                params.append(filters['event_type'])

            if 'week' in filters:
                query += " AND week = ?"
                params.append(filters['week'])

            if 'season' in filters:
                query += " AND season = ?"
                params.append(filters['season'])

            if 'risk_mode' in filters:
                query += " AND risk_mode = ?"
                params.append(filters['risk_mode'])

            if 'start_date' in filters:
                query += " AND timestamp >= ?"
                params.append(filters['start_date'])

            if 'end_date' in filters:
                query += " AND timestamp <= ?"
                params.append(filters['end_date'])

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(query, conn, params=params)

        # Parse JSON columns
        if 'metrics' in df.columns:
            df['metrics'] = df['metrics'].apply(lambda x: json.loads(x) if x else {})

        if 'config' in df.columns:
            df['config'] = df['config'].apply(lambda x: json.loads(x) if x else {})

        conn.close()

        return df

    def _query_jsonl(
        self,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> pd.DataFrame:
        """Query JSONL file."""
        if not self.jsonl_path.exists():
            return pd.DataFrame()

        # Read all events
        events = []
        with open(self.jsonl_path, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    continue

        if not events:
            return pd.DataFrame()

        df = pd.DataFrame(events)

        # Apply filters
        if filters:
            if 'event_type' in filters:
                df = df[df['event_type'] == filters['event_type']]

            if 'week' in filters:
                df = df[df['week'] == filters['week']]

            if 'season' in filters:
                df = df[df['season'] == filters['season']]

            if 'risk_mode' in filters:
                df = df[df['risk_mode'] == filters['risk_mode']]

            if 'start_date' in filters and 'timestamp' in df.columns:
                df = df[df['timestamp'] >= filters['start_date']]

            if 'end_date' in filters and 'timestamp' in df.columns:
                df = df[df['timestamp'] <= filters['end_date']]

        # Sort by timestamp (newest first)
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)

        # Apply limit
        if limit:
            df = df.head(limit)

        return df

    def get_recent_experiments(self, n: int = 10) -> pd.DataFrame:
        """
        Get N most recent experiments.

        Args:
            n: Number of experiments to return

        Returns:
            DataFrame with recent experiments
        """
        return self.query_experiments(limit=n)

    def get_experiments_by_week(self, week: int, season: int) -> pd.DataFrame:
        """
        Get all experiments for a specific week.

        Args:
            week: Week number
            season: Season year

        Returns:
            DataFrame with experiments for that week
        """
        return self.query_experiments(filters={'week': week, 'season': season})

    def export_to_csv(self, output_path: str) -> None:
        """
        Export all experiments to CSV.

        Args:
            output_path: Path to output CSV file
        """
        df = self.query_experiments()

        if df.empty:
            print("No experiments to export")
            return

        # Flatten metrics and config columns for CSV export
        if 'metrics' in df.columns:
            metrics_df = pd.json_normalize(df['metrics'])
            metrics_df.columns = [f"metric_{col}" for col in metrics_df.columns]
            df = pd.concat([df.drop('metrics', axis=1), metrics_df], axis=1)

        if 'config' in df.columns:
            config_df = pd.json_normalize(df['config'])
            config_df.columns = [f"config_{col}" for col in config_df.columns]
            df = pd.concat([df.drop('config', axis=1), config_df], axis=1)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} experiments to {output_path}")


# Convenience functions
def record_experiment(
    event: Dict[str, Any],
    tracking_dir: Optional[Path] = None,
    use_sqlite: bool = False
) -> None:
    """
    Convenience function to record an experiment event.

    Args:
        event: Event dictionary
        tracking_dir: Optional tracking directory
        use_sqlite: Use SQLite instead of JSONL
    """
    tracker = ExperimentTracker(tracking_dir=tracking_dir, use_sqlite=use_sqlite)
    tracker.record_event(event)


def query_experiments(
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    tracking_dir: Optional[Path] = None,
    use_sqlite: bool = False
) -> pd.DataFrame:
    """
    Convenience function to query experiments.

    Args:
        filters: Optional filters
        limit: Maximum number of results
        tracking_dir: Optional tracking directory
        use_sqlite: Use SQLite instead of JSONL

    Returns:
        DataFrame with experiment history
    """
    tracker = ExperimentTracker(tracking_dir=tracking_dir, use_sqlite=use_sqlite)
    return tracker.query_experiments(filters=filters, limit=limit)


# Common event types
EVENT_TYPES = {
    'PROPS_FETCHED': 'props_fetched',
    'SLIP_GENERATED': 'slip_generated',
    'BACKTEST_RUN': 'backtest_run',
    'FILTER_CHANGE': 'filter_change',
    'CONFIG_UPDATE': 'config_update',
    'MODEL_PREDICTION': 'model_prediction',
    'SNAPSHOT_CREATED': 'snapshot_created',
    'CALIBRATION_CHECK': 'calibration_check',
    'EXPORT': 'export',
}
