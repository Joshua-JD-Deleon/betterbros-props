"""
Simplified BetterBros Props API - No Database/Redis Required
This version uses in-memory data and works without external dependencies.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import random

# Simple data models
class PropLeg(BaseModel):
    id: str
    sport: str
    player: str
    position: Optional[str]
    team: str
    opponent: str
    stat_type: str
    stat_category: Optional[str]
    line: float
    over_odds: float
    under_odds: float
    confidence: float
    ev: float
    is_live: bool
    game_time: str
    market: str

class FetchPropsRequest(BaseModel):
    sport: str
    week: int
    season: str
    minEV: Optional[float] = None
    liveOnly: Optional[bool] = False

class OptimizeRequest(BaseModel):
    propIds: List[str]
    riskProfile: str
    bankroll: float

class OptimizedSlip(BaseModel):
    id: str
    legs: List[dict]
    ev: float
    win_probability: float
    correlation_adjusted_probability: float
    max_correlation: float
    diversity_score: float
    kelly_stake: float
    correlation_notes: List[str]
    risk_level: str

# Create FastAPI app
app = FastAPI(
    title="BetterBros Props API (Simplified)",
    description="Simplified API without database requirements",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data generator
def generate_mock_props(sport: str, week: int, count: int = 10) -> List[dict]:
    """Generate realistic mock props for testing"""
    props = []

    # Sport-specific configurations
    sport_configs = {
        "NFL": {
            "positions": ["QB", "RB", "WR", "TE"],
            "stats": ["Passing Yards", "Rushing Yards", "Receiving Yards", "Total TDs", "Solo Tackles"],
            "teams": ["KC", "BUF", "SF", "PHI", "DAL", "MIA", "CIN", "BAL"],
        },
        "NBA": {
            "positions": ["PG", "SG", "SF", "PF", "C"],
            "stats": ["Points", "Rebounds", "Assists", "3-Pointers Made", "Steals"],
            "teams": ["LAL", "BOS", "MIL", "DEN", "PHX", "GSW", "MIA", "DAL"],
        },
        "MLB": {
            "positions": ["SP", "RP", "1B", "2B", "SS", "3B", "OF"],
            "stats": ["Strikeouts", "Hits Allowed", "Home Runs", "RBI", "Total Bases"],
            "teams": ["LAD", "ATL", "HOU", "NYY", "TB", "TOR", "SEA", "TEX"],
        },
        "NHL": {
            "positions": ["C", "LW", "RW", "D", "G"],
            "stats": ["Points", "Goals", "Assists", "Shots on Goal", "Saves"],
            "teams": ["TOR", "BOS", "COL", "VGK", "CAR", "EDM", "NYR", "DAL"],
        }
    }

    config = sport_configs.get(sport, sport_configs["NFL"])
    players = [
        "Patrick Mahomes", "Josh Allen", "Christian McCaffrey", "Tyreek Hill",
        "LeBron James", "Luka Doncic", "Nikola Jokic", "Giannis Antetokounmpo",
        "Shohei Ohtani", "Aaron Judge", "Mookie Betts", "Ronald Acuna",
        "Connor McDavid", "Auston Matthews", "Nathan MacKinnon", "Leon Draisaitl"
    ]

    for i in range(count):
        team_idx = i % len(config["teams"])
        opp_idx = (i + 1) % len(config["teams"])

        confidence = random.uniform(45, 85)
        ev = (confidence - 50) * random.uniform(0.8, 1.5)
        line = random.choice([20.5, 24.5, 28.5, 32.5, 1.5, 2.5, 3.5, 45.5, 50.5])

        props.append({
            "id": f"prop_{sport}_{i}_{week}",
            "sport": sport,
            "player": random.choice(players),
            "position": random.choice(config["positions"]),
            "team": config["teams"][team_idx],
            "opponent": f"vs {config['teams'][opp_idx]}",
            "stat_type": random.choice(config["stats"]),
            "stat_category": "Scoring" if i % 3 == 0 else "Performance",
            "line": line,
            "over_odds": random.choice([-110, -115, -120, +100, +105]),
            "under_odds": random.choice([-110, -115, -120, +100, +105]),
            "confidence": confidence,
            "ev": ev,
            "is_live": random.random() < 0.15,
            "game_time": f"2024-12-{random.randint(15, 22)} 19:00",
            "market": random.choice(["PrizePicks", "Underdog", "DraftKings"]),
        })

    return props

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "BetterBros Props API (Simplified)",
        "version": "1.0.0",
        "status": "running",
        "note": "No database required"
    }

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "simplified-api",
        "timestamp": datetime.now().isoformat()
    }

# Props endpoint
@app.post("/api/props")
async def fetch_props(request: FetchPropsRequest):
    """Fetch props with filtering"""
    try:
        # Generate mock props
        props = generate_mock_props(request.sport, request.week, count=15)

        # Apply filters
        if request.minEV:
            props = [p for p in props if p["ev"] >= request.minEV]

        if request.liveOnly:
            props = [p for p in props if p["is_live"]]

        return {
            "props": props,
            "total": len(props),
            "apiCredits": {
                "used": 10,
                "remaining": 990
            },
            "cached": False,
            "sport": request.sport,
            "week": request.week
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optimize endpoint
@app.post("/api/optimize")
async def optimize_slips(request: OptimizeRequest):
    """Generate optimized parlay slips"""
    try:
        # Risk profile configurations
        risk_configs = {
            "conservative": {"min_legs": 2, "max_legs": 4, "correlation_penalty": 0.3},
            "balanced": {"min_legs": 2, "max_legs": 5, "correlation_penalty": 0.2},
            "aggressive": {"min_legs": 3, "max_legs": 6, "correlation_penalty": 0.1}
        }

        config = risk_configs.get(request.riskProfile, risk_configs["balanced"])

        # Generate optimized slips (mock algorithm)
        optimized_slips = []
        for i in range(5):  # Generate top 5 slips
            num_legs = random.randint(config["min_legs"], config["max_legs"])

            # Mock legs
            legs = []
            for j in range(num_legs):
                legs.append({
                    "id": f"leg_{i}_{j}",
                    "player": f"Player {j}",
                    "stat_type": "Points",
                    "line": 24.5 + j,
                    "odds": -110,
                    "confidence": random.uniform(60, 80)
                })

            base_prob = 0.5 ** num_legs
            adjusted_prob = base_prob * (1 - config["correlation_penalty"] * 0.5)
            ev = random.uniform(5, 20) - (i * 2)

            slip = {
                "id": f"slip_{i}",
                "legs": legs,
                "ev": ev,
                "win_probability": base_prob,
                "correlation_adjusted_probability": adjusted_prob,
                "max_correlation": config["correlation_penalty"],
                "diversity_score": random.uniform(0.7, 0.95),
                "kelly_stake": (adjusted_prob * 2 - 1) * request.bankroll * 0.25,
                "correlation_notes": [
                    f"Detected same-game correlation in {num_legs} legs"
                ] if num_legs > 3 else [],
                "risk_level": request.riskProfile
            }

            optimized_slips.append(slip)

        # Sort by EV
        optimized_slips.sort(key=lambda x: x["ev"], reverse=True)

        return {
            "optimizedSlips": optimized_slips,
            "totalEvaluated": len(request.propIds) * 100,
            "computationTimeMs": random.uniform(50, 200),
            "riskProfile": request.riskProfile
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting simplified BetterBros API on port 8001...")
    print("No database or Redis required!")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
