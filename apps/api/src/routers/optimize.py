"""
Optimization Router
Endpoints for parlay optimization and slip detection
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from src.types import (
    OptimizationRequest,
    OptimizationResponse,
    SlipDetectionRequest,
    SlipDetectionResponse,
    ParlayCandidate,
    SlipCandidate,
    SlipDriver,
    UserProfile,
    PropLeg,
    ModelPrediction,
    BetDirection,
)
from src.auth.deps import get_current_active_user, require_pro_tier
from src.db import get_db, get_redis
from src.optimize import SlipOptimizer, MonteCarloSimulator, KellyCriterion, create_constraints_for_risk_mode
from src.corr import CorrelationAnalyzer
from src.config import settings

router = APIRouter()


@router.post("/parlays", response_model=OptimizationResponse)
async def optimize_parlays(
    request: OptimizationRequest,
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Optimize parlay combinations from available prop legs

    Uses SlipOptimizer to:
    - Get predictions for all prop legs
    - Get correlation matrix
    - Apply optimization algorithm (greedy, genetic, or beam search)
    - Score candidates by EV, edge, diversification
    - Filter by constraints (correlation, exposure limits)
    - Return top K candidates
    """
    start_time = time.time()

    try:
        # Initialize optimizer
        optimizer = SlipOptimizer(
            correlation_penalty_weight=0.15,
            diversity_bonus_weight=0.05,
            n_simulations=10000,
            kelly_fraction=0.25,
        )

        # Get predictions for prop legs (placeholder - would fetch from cache/model)
        predictions = {}
        for prop_leg_id in request.prop_leg_ids:
            # In production, fetch actual predictions
            predictions[prop_leg_id] = {
                "prob_over": 0.58,
                "prob_under": 0.42,
                "predicted_value": 25.5,
                "line_value": 24.5,
                "edge": 0.08,
                "confidence": 0.65,
            }

        # Get correlation matrix (placeholder)
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)
        # correlations = await analyzer.compute_correlations(request.prop_leg_ids)

        # For now, use placeholder correlation matrix
        correlation_matrix = {}
        for i, leg_id_1 in enumerate(request.prop_leg_ids):
            for leg_id_2 in request.prop_leg_ids[i+1:]:
                correlation_matrix[(leg_id_1, leg_id_2)] = 0.15

        # Create constraints based on request
        constraints = request.constraints

        # Optimize slips
        # In production:
        # optimized_slips = optimizer.optimize_slips(
        #     props=prop_legs,
        #     predictions=predictions,
        #     correlations=correlation_matrix,
        #     constraints=constraints,
        #     top_n=request.top_k,
        #     algorithm=request.algorithm,
        # )

        # Create placeholder parlay candidates
        candidates = []
        for i in range(min(request.top_k, 5)):
            # Create placeholder legs
            legs = [
                PropLeg(
                    id=f"leg_{j}",
                    player_id=f"player_{j}",
                    player_name=f"Player {j}",
                    stat_type="points",
                    line=24.5 + j,
                    direction=BetDirection.OVER,
                    odds=1.9,
                    team="Team A",
                    opponent="Team B",
                    game_id=f"game_{j}",
                )
                for j in range(3)
            ]

            # Create placeholder predictions
            preds = [
                ModelPrediction(
                    prop_leg_id=leg.id,
                    player_id=leg.player_id,
                    stat_type=leg.stat_type,
                    predicted_value=leg.line + 1.0,
                    line_value=leg.line,
                    prob_over=0.58,
                    prob_under=0.42,
                    confidence=0.65,
                    edge=0.08,
                    kelly_fraction=0.04,
                    model_type="ensemble",
                    model_version=settings.MODEL_VERSION,
                )
                for leg in legs
            ]

            candidate = ParlayCandidate(
                prop_leg_ids=[leg.id for leg in legs],
                legs=legs,
                predictions=preds,
                expected_value=15.2 - (i * 2),
                total_edge=0.24 - (i * 0.03),
                win_probability=0.195 - (i * 0.02),
                combined_confidence=0.68 - (i * 0.05),
                kelly_stake=12.5 - (i * 1.5),
                max_correlation=0.18,
                diversification_score=0.85 - (i * 0.05),
                rank=i + 1,
                score=95.0 - (i * 8),
            )
            candidates.append(candidate)

        computation_time = (time.time() - start_time) * 1000

        return OptimizationResponse(
            candidates=candidates,
            total_evaluated=len(request.prop_leg_ids) * 100,
            computation_time_ms=computation_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize parlays: {str(e)}",
        )


@router.post("/slips", response_model=SlipDetectionResponse)
async def detect_slips(
    request: SlipDetectionRequest,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Detect high-edge slip opportunities

    Analyzes all active prop markets to find:
    - High-edge opportunities
    - Market inefficiencies
    - Injury-driven edges
    - Line movement opportunities
    """
    try:
        # In production, fetch all active markets and predictions
        # markets = await get_active_markets(db)
        # predictions = await get_all_predictions(markets, redis_client)

        # Create placeholder slip candidates
        slips = []
        for i in range(min(request.top_k, 10)):
            drivers = [
                SlipDriver(
                    type="model_edge",
                    description="Model predicts significantly higher value than line",
                    impact_score=0.7,
                ),
                SlipDriver(
                    type="market_inefficiency",
                    description="Line hasn't adjusted to recent injury news",
                    impact_score=0.5,
                ),
            ]

            slip = SlipCandidate(
                prop_leg_id=f"slip_{i}",
                player_name=f"Player {i}",
                stat_type="points",
                line=24.5,
                direction=BetDirection.OVER,
                edge=0.15 - (i * 0.01),
                confidence=0.75 - (i * 0.02),
                expected_value=12.5 - (i * 1.0),
                drivers=drivers,
                primary_driver="model_edge",
                risk_score=0.3 + (i * 0.02),
                volatility=5.2,
            )
            slips.append(slip)

        # Filter by request criteria
        filtered_slips = [
            s for s in slips
            if s.edge >= request.min_edge
            and s.confidence >= request.min_confidence
            and s.risk_score <= request.max_risk
        ]

        return SlipDetectionResponse(
            slips=filtered_slips[:request.top_k],
            total_evaluated=len(slips),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect slips: {str(e)}",
        )


@router.post("/validate-parlay")
async def validate_parlay(
    prop_leg_ids: list[str],
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Validate a user-selected parlay against constraints

    Checks:
    - Correlations between legs
    - Exposure limits
    - Expected value and risk
    - Returns warnings and recommendations
    """
    try:
        optimizer = SlipOptimizer()
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)

        # In production, fetch correlations and predictions
        # correlations = await analyzer.compute_correlations(prop_leg_ids)
        # predictions = await get_predictions(prop_leg_ids, redis_client)

        # Placeholder validation
        warnings = []
        is_valid = True

        # Check for high correlations
        if len(prop_leg_ids) > 2:
            warnings.append({
                "type": "correlation",
                "severity": "medium",
                "message": "Two legs from same game have correlation > 0.3",
            })

        # Check for same player exposure
        # if has_same_player_multiple_props(prop_leg_ids):
        #     warnings.append(...)

        metrics = {
            "expected_value": 15.2,
            "win_probability": 0.195,
            "total_edge": 0.24,
            "max_correlation": 0.32,
            "diversification_score": 0.78,
        }

        return {
            "is_valid": is_valid,
            "warnings": warnings,
            "metrics": metrics,
            "recommendations": [
                "Consider removing one leg from Game XYZ to reduce correlation",
                "Current Kelly stake recommendation: $12.50",
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate parlay: {str(e)}",
        )


@router.post("/simulate")
async def simulate_parlay(
    prop_leg_ids: list[str],
    num_simulations: int = 10000,
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Run Monte Carlo simulation for a parlay

    Simulates outcomes accounting for:
    - Correlations between legs
    - Win probability distribution
    - Expected profit distribution
    - Risk metrics (VaR, CVaR)
    """
    try:
        simulator = MonteCarloSimulator(n_simulations=num_simulations)
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)

        # In production, fetch predictions and correlations
        # predictions = await get_predictions(prop_leg_ids, redis_client)
        # correlations = await analyzer.compute_correlations(prop_leg_ids)

        # Run simulation
        # results = simulator.simulate_parlay(
        #     predictions=predictions,
        #     correlations=correlations,
        #     payout_multiplier=3.0,
        #     stake=10.0,
        # )

        # Placeholder simulation results
        return {
            "prop_leg_ids": prop_leg_ids,
            "simulations_run": num_simulations,
            "results": {
                "win_probability": 0.195,
                "expected_profit": 5.85,
                "profit_percentiles": {
                    "p5": -10.0,
                    "p25": -10.0,
                    "p50": -10.0,
                    "p75": 20.0,
                    "p95": 20.0,
                },
                "var_95": -10.0,
                "cvar_95": -10.0,
                "sharpe_ratio": 0.45,
            },
            "distribution": {
                "win_count": int(num_simulations * 0.195),
                "loss_count": int(num_simulations * 0.805),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to simulate parlay: {str(e)}",
        )


@router.get("/strategies")
async def list_strategies(
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    List available optimization strategies

    Returns algorithms and their characteristics
    """
    return {
        "strategies": [
            {
                "name": "greedy",
                "description": "Fast greedy optimization - builds parlays by iteratively selecting best legs",
                "speed": "fast",
                "quality": "good",
                "recommended_for": "Real-time optimization, quick decisions",
                "typical_time_ms": 50,
            },
            {
                "name": "genetic",
                "description": "Genetic algorithm optimization - evolutionary search for optimal combinations",
                "speed": "medium",
                "quality": "excellent",
                "recommended_for": "Batch optimization, finding global optimum",
                "typical_time_ms": 500,
            },
            {
                "name": "beam_search",
                "description": "Beam search optimization - balanced breadth and depth search",
                "speed": "medium",
                "quality": "very good",
                "recommended_for": "Moderate complexity searches",
                "typical_time_ms": 200,
            },
        ],
    }


@router.post("/auto-build")
async def auto_build_parlays(
    sport: Optional[str] = None,
    target_payout: Optional[float] = None,
    max_risk: float = 0.5,
    current_user: UserProfile = Depends(require_pro_tier),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Automatically build optimal parlays from all available markets

    Fetches all active markets, generates predictions, and optimizes
    to return multiple parlay options with different risk/reward profiles
    """
    try:
        optimizer = SlipOptimizer()

        # In production:
        # markets = await get_active_markets(db, sport=sport)
        # predictions = await generate_predictions(markets)
        # correlations = await analyzer.compute_correlations(all_prop_legs)

        # Build risk profiles
        risk_modes = ["conservative", "moderate", "aggressive"]
        parlays = []

        for risk_mode in risk_modes:
            # In production:
            # constraints = create_constraints_for_risk_mode(risk_mode)
            # optimized = optimizer.optimize_slips(
            #     props=markets,
            #     predictions=predictions,
            #     correlations=correlations,
            #     risk_mode=risk_mode,
            #     top_n=3,
            # )

            # Placeholder
            parlays.append({
                "risk_mode": risk_mode,
                "parlay": {
                    "legs": 3 + risk_modes.index(risk_mode),
                    "expected_value": 10.0 + (risk_modes.index(risk_mode) * 5),
                    "win_probability": 0.25 - (risk_modes.index(risk_mode) * 0.05),
                    "payout": 20.0 + (risk_modes.index(risk_mode) * 10),
                },
            })

        return {
            "parlays": parlays,
            "total_markets_analyzed": 150,
            "sport": sport or "all",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-build parlays: {str(e)}",
        )
