# Installation and Setup Guide

## Prerequisites

- Python 3.9+
- Redis (for caching, optional but recommended)
- PostgreSQL (for historical data, optional)

## Installation Steps

### 1. Install Dependencies

```bash
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api

# Option 1: Using pip
pip install -r requirements.txt

# Option 2: Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check all packages are installed
python3 -c "import numpy, scipy, pandas, copulas; print('All dependencies OK')"
```

### 3. Start Redis (Optional but Recommended)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or using Homebrew (macOS)
brew services start redis

# Or using apt (Linux)
sudo systemctl start redis
```

### 4. Configure Environment

Create or update `.env` file:

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_CACHE_TTL=3600

# Database (if using historical data)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/betterbros

# Environment
ENVIRONMENT=development
```

## Running Examples

### Without Redis (Standalone)

The system works without Redis but won't cache results:

```bash
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api
python3 -m src.corr.example_usage
```

### With Redis (Full Features)

Ensure Redis is running, then:

```bash
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api
python3 -m src.corr.example_usage
```

## Quick Test

Create a test file `test_correlation.py`:

```python
import asyncio
from src.corr import CorrelationAnalyzer
from src.types import PropLeg, BetDirection

async def test():
    # Create sample props
    props = [
        PropLeg(
            id="1",
            player_id="player1",
            player_name="Player One",
            stat_type="points",
            line=25.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="TEAM1",
            opponent="TEAM2",
            game_id="game_1",
            position="G"
        ),
        PropLeg(
            id="2",
            player_id="player2",
            player_name="Player Two",
            stat_type="rebounds",
            line=8.5,
            direction=BetDirection.OVER,
            odds=1.85,
            team="TEAM2",
            opponent="TEAM1",
            game_id="game_2",
            position="F"
        ),
    ]

    # Analyze correlation
    analyzer = CorrelationAnalyzer(redis_client=None)
    corr_matrix = await analyzer.estimate_correlation_matrix(props, use_cache=False)

    print("Correlation matrix:")
    print(corr_matrix)
    print("\nTest passed!")

asyncio.run(test())
```

Run it:

```bash
python3 test_correlation.py
```

## Integration with API

### FastAPI Endpoint Example

```python
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from src.db.session import get_redis
from src.corr import CorrelationAnalyzer, CorrelatedSampler
from src.types import PropLeg

router = APIRouter()

@router.post("/api/correlation/analyze")
async def analyze_correlation(
    props: List[PropLeg],
    redis: Redis = Depends(get_redis)
):
    """Analyze correlation structure for props"""
    analyzer = CorrelationAnalyzer(redis_client=redis)

    # Estimate correlation matrix
    corr_matrix = await analyzer.estimate_correlation_matrix(props)

    # Get statistics
    stats = await analyzer.get_correlation_stats(props)

    return {
        "correlation_matrix": corr_matrix.tolist(),
        "statistics": stats
    }

@router.post("/api/simulation/run")
async def run_simulation(
    props: List[PropLeg],
    probabilities: List[float],
    n_sims: int = 10000,
    redis: Redis = Depends(get_redis)
):
    """Run Monte Carlo simulation with correlated sampling"""
    sampler = CorrelatedSampler(redis_client=redis)

    # Generate samples
    samples = await sampler.generate_samples(
        props=props,
        probabilities=probabilities,
        n_sims=n_sims
    )

    # Analyze results
    stats = await sampler.get_sample_statistics(samples, props)

    return {
        "samples_generated": n_sims,
        "statistics": stats
    }
```

## Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Make sure you're in the right directory
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start it
docker run -d -p 6379:6379 redis:latest
```

### Issue: Copulas Import Error

```bash
# Reinstall copulas
pip uninstall copulas
pip install copulas==0.10.1
```

### Issue: Numpy/Scipy Version Conflicts

```bash
# Upgrade to compatible versions
pip install --upgrade numpy==1.26.3 scipy==1.11.4
```

## Performance Optimization

### 1. Enable Redis Caching

Always use Redis in production for significant performance gains:

```python
from src.db.session import get_redis_client

redis = await get_redis_client()
analyzer = CorrelationAnalyzer(redis_client=redis, cache_ttl=3600)
```

### 2. Batch Processing

Process multiple correlation analyses together:

```python
# Good - batch processing
all_correlations = await asyncio.gather(
    analyzer.estimate_correlation_matrix(props_1),
    analyzer.estimate_correlation_matrix(props_2),
    analyzer.estimate_correlation_matrix(props_3)
)

# Bad - sequential processing
corr_1 = await analyzer.estimate_correlation_matrix(props_1)
corr_2 = await analyzer.estimate_correlation_matrix(props_2)
corr_3 = await analyzer.estimate_correlation_matrix(props_3)
```

### 3. Use Snapshot IDs for Caching

Always provide snapshot_id when available:

```python
# Enables caching
corr_matrix = await analyzer.estimate_correlation_matrix(
    props,
    snapshot_id="snapshot_20241014_001"
)
```

## Next Steps

1. Review the [README.md](README.md) for comprehensive documentation
2. Run the examples in [example_usage.py](example_usage.py)
3. Integrate with your optimization pipeline
4. Set up monitoring for cache hit rates
5. Configure historical data ingestion for empirical correlations

## Support

For issues or questions:
- Check the [README.md](README.md) documentation
- Review [example_usage.py](example_usage.py) for patterns
- Examine the source code (all modules are well-documented)
