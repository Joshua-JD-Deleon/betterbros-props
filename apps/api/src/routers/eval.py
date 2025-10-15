"""
Evaluation Router
Endpoints for backtesting and model evaluation
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from src.types import (
    BacktestConfig,
    BacktestRequest,
    BacktestResult,
    UserProfile,
)
from src.auth.deps import get_current_active_user, require_pro_tier
from src.db import get_db, get_redis
from src.eval import BacktestEngine, CalibrationMonitor, MetricsCalculator
from src.config import settings

router = APIRouter()


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Run backtest with specified configuration

    Uses BacktestEngine to:
    - Fetch historical prop markets and outcomes
    - Apply strategy rules to select bets
    - Simulate bet execution with stake sizing
    - Calculate performance metrics (ROI, Sharpe, drawdown)
    - Evaluate calibration (Brier score)
    - Generate equity curve
    """
    try:
        # Initialize backtest engine
        engine = BacktestEngine(
            db_session=db,
            initial_bankroll=request.config.simulated_bankroll,
            risk_mode="balanced",
        )

        # In production, run actual backtest
        # results = await engine.run_backtest(
        #     start_date=request.config.start_date,
        #     end_date=request.config.end_date,
        #     strategy=request.config.strategy,
        #     min_edge=request.config.min_edge,
        #     min_confidence=request.config.min_confidence,
        #     stake_method=request.config.stake_method,
        #     kelly_multiplier=request.config.kelly_multiplier,
        # )

        # Placeholder backtest result
        result = BacktestResult(
            config=request.config,
            total_bets=150,
            winning_bets=95,
            losing_bets=55,
            win_rate=0.633,
            total_wagered=1500.0,
            total_profit=285.50,
            roi=0.190,
            sharpe_ratio=1.45,
            max_drawdown=0.125,
            avg_edge=0.095,
            avg_confidence=0.68,
            avg_odds=1.9,
            calibration_score=0.92,
            brier_score=0.18,
            daily_pnl=[
                {"date": "2025-10-01", "pnl": 25.50},
                {"date": "2025-10-02", "pnl": -15.00},
                {"date": "2025-10-03", "pnl": 42.30},
            ],
            equity_curve=[
                {"date": "2025-10-01", "equity": 10025.50},
                {"date": "2025-10-02", "equity": 10010.50},
                {"date": "2025-10-03", "equity": 10052.80},
            ],
            computed_at=datetime.utcnow(),
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run backtest: {str(e)}",
        )


@router.get("/backtest/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve saved backtest result

    Fetches complete backtest data from database
    """
    try:
        # In production, query database for backtest
        # result = await db.query(BacktestModel).filter_by(id=backtest_id).first()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest {backtest_id} not found",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backtest: {str(e)}",
        )


@router.get("/backtests", response_model=List[BacktestResult])
async def list_backtests(
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all backtests for current user

    Returns list with metadata
    """
    try:
        # In production, query database
        # backtests = await db.query(BacktestModel).filter_by(user_id=current_user.user_id).all()

        return []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backtests: {str(e)}",
        )


@router.post("/quick-backtest")
async def quick_backtest(
    start_date: datetime,
    end_date: datetime,
    min_edge: float = 0.1,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run quick backtest with simplified parameters

    Uses default strategy and constraints for fast evaluation
    """
    try:
        engine = BacktestEngine(db_session=db, initial_bankroll=10000.0)

        # In production, run quick backtest
        # results = await engine.quick_backtest(
        #     start_date=start_date,
        #     end_date=end_date,
        #     min_edge=min_edge,
        # )

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": {
                "total_bets": 75,
                "win_rate": 0.65,
                "roi": 0.18,
                "total_profit": 135.50,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run quick backtest: {str(e)}",
        )


@router.post("/calibration")
async def evaluate_calibration(
    start_date: datetime,
    end_date: datetime,
    model_version: Optional[str] = None,
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate model calibration over date range

    Uses CalibrationMonitor to:
    - Fetch predictions and outcomes
    - Calculate calibration curve
    - Compute Brier score, log loss
    - Plot predicted vs actual probabilities
    """
    try:
        monitor = CalibrationMonitor(db_session=db)

        # In production, evaluate calibration
        # calibration = await monitor.evaluate_calibration(
        #     start_date=start_date,
        #     end_date=end_date,
        #     model_version=model_version or settings.MODEL_VERSION,
        # )

        return {
            "calibration_score": 0.94,
            "brier_score": 0.16,
            "log_loss": 0.42,
            "calibration_curve": [
                {"predicted": 0.1, "actual": 0.12, "count": 50},
                {"predicted": 0.3, "actual": 0.28, "count": 120},
                {"predicted": 0.5, "actual": 0.52, "count": 200},
                {"predicted": 0.7, "actual": 0.68, "count": 150},
                {"predicted": 0.9, "actual": 0.88, "count": 80},
            ],
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "model_version": model_version or settings.MODEL_VERSION,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate calibration: {str(e)}",
        )


@router.post("/performance-by-segment")
async def analyze_performance_by_segment(
    start_date: datetime,
    end_date: datetime,
    segment_by: str = "sport",
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze model performance broken down by segments

    Segments can be: sport, stat_type, player, team, etc.
    Identifies strengths and weaknesses
    """
    try:
        calculator = MetricsCalculator()

        # In production, fetch and segment data
        # segments = await calculator.calculate_by_segment(
        #     start_date=start_date,
        #     end_date=end_date,
        #     segment_by=segment_by,
        # )

        return {
            "segment_by": segment_by,
            "segments": [
                {
                    "name": "NBA",
                    "total_bets": 120,
                    "win_rate": 0.675,
                    "roi": 0.22,
                    "avg_edge": 0.105,
                    "brier_score": 0.15,
                },
                {
                    "name": "NFL",
                    "total_bets": 80,
                    "win_rate": 0.625,
                    "roi": 0.15,
                    "avg_edge": 0.085,
                    "brier_score": 0.19,
                },
            ],
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze performance by segment: {str(e)}",
        )


@router.get("/live-tracking")
async def get_live_performance_tracking(
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get live performance tracking for today's bets

    Tracks which bets are live, won, or lost
    Calculates current P&L
    """
    try:
        # In production, fetch today's bets and current status
        # tracking = await get_live_tracking(db, current_user.user_id)

        return {
            "date": datetime.utcnow().date().isoformat(),
            "live_bets": [
                {
                    "prop_leg_id": "live_1",
                    "player_name": "LeBron James",
                    "stat_type": "points",
                    "line": 25.5,
                    "direction": "over",
                    "current_value": 18.0,
                    "game_time_remaining": "Q3 8:45",
                    "status": "in_progress",
                },
            ],
            "completed_bets": [
                {
                    "prop_leg_id": "comp_1",
                    "player_name": "Giannis Antetokounmpo",
                    "stat_type": "rebounds",
                    "line": 11.5,
                    "direction": "over",
                    "final_value": 13.0,
                    "result": "win",
                    "pnl": +10.0,
                },
            ],
            "current_pnl": +5.0,
            "pending_pnl": +15.0,
            "total_bets_today": 8,
            "bets_in_progress": 1,
            "bets_completed": 7,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live tracking: {str(e)}",
        )
