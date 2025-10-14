# API Documentation

This folder contains documentation and resources for the various APIs used in **BetterBros Props**.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [The Odds API](#the-odds-api)
   - [NFL](#the-odds-api---nfl)
   - [NBA](#the-odds-api---nba)
   - [MLB](#the-odds-api---mlb)
3. [SportsGameOdds API](#sportsgameodds-api)
   - [NFL](#sportsgameodds---nfl)
   - [NBA](#sportsgameodds---nba)
   - [MLB](#sportsgameodds---mlb)
4. [API Comparison](#api-comparison)
5. [Resources](#resources)

---

## API Overview

BetterBros Props integrates with two primary APIs for fetching sports odds and player props:

| API | Client | Free Tier | Advantages |
|-----|--------|-----------|------------|
| **The Odds API** | `src/ingest/odds_api_client.py` | 500 requests/month | Wide bookmaker coverage, simple API |
| **SportsGameOdds API** | `src/ingest/sportgameodds_client.py` | TBD | Comprehensive player props, better player data |

---

## The Odds API

**Base URL**: `https://api.the-odds-api.com/v4`
**Documentation**: https://the-odds-api.com/liveapi/guides/v4/
**Free Tier**: 500 requests/month
**Supported Sports**: NFL, NBA, MLB, NHL, Soccer, and more

### Authentication
```bash
?apiKey=YOUR_API_KEY
```

### The Odds API - NFL

**Sport Key**: `americanfootball_nfl`

#### Available Markets
- Moneyline (h2h)
- Spreads (handicap)
- Over/Under (totals)
- Quarter/Half time odds
- **Player Props** (US & AU bookmakers only):
  - Passing yards, TDs, completions, attempts, interceptions
  - Rushing yards, attempts, TDs
  - Receiving yards, receptions, TDs
  - Field goals, kicking points

#### Example Request
```http
GET https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regions=us&markets=h2h,spreads,totals&oddsFormat=american&apiKey=YOUR_API_KEY
```

#### Example Response
```json
[{
  "id": "42db668449664943833b5c04a583328a",
  "sport_key": "americanfootball_nfl",
  "sport_title": "NFL",
  "commence_time": "2023-09-08T00:21:00Z",
  "home_team": "Kansas City Chiefs",
  "away_team": "Detroit Lions",
  "bookmakers": [
    {
      "key": "fanduel",
      "title": "FanDuel",
      "last_update": "2023-07-18T07:38:01Z",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {"name": "Detroit Lions", "price": 245},
            {"name": "Kansas City Chiefs", "price": -300}
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {"name": "Detroit Lions", "price": -105, "point": 6.5},
            {"name": "Kansas City Chiefs", "price": -115, "point": -6.5}
          ]
        }
      ]
    }
  ]
}]
```

#### Supported Bookmakers
**US**: DraftKings, FanDuel, BetMGM, Caesars, Bovada, FoxBet
**UK**: Unibet, William Hill, Ladbrokes, Betfair, Bet Victor, Paddy Power
**EU**: 1xBet, Pinnacle, Betclic, Betsson
**AU**: Sportsbet, TAB, Neds

---

### The Odds API - NBA

**Sport Key**: `basketball_nba`

#### Available Markets
- Moneyline (h2h)
- Spreads (handicap)
- Over/Under (totals)
- Quarter/Half time odds
- **Player Props** (US & AU bookmakers only):
  - Points, rebounds, assists
  - Three-pointers made
  - Blocks, steals
  - First basket

#### Example Request
```http
GET https://api.the-odds-api.com/v4/sports/basketball_nba/odds?regions=us&markets=h2h,spreads,totals&oddsFormat=american&apiKey=YOUR_API_KEY
```

#### Example Response
```json
[{
  "id": "4f88be957c08fec11f1a32985c4e0ca4",
  "sport_key": "basketball_nba",
  "sport_title": "NBA",
  "commence_time": "2023-02-01T00:10:00Z",
  "home_team": "Cleveland Cavaliers",
  "away_team": "Miami Heat",
  "bookmakers": [
    {
      "key": "draftkings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {"name": "Cleveland Cavaliers", "price": -165},
            {"name": "Miami Heat", "price": 140}
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {"name": "Cleveland Cavaliers", "price": -110, "point": -4.0},
            {"name": "Miami Heat", "price": -110, "point": 4.0}
          ]
        },
        {
          "key": "totals",
          "outcomes": [
            {"name": "Over", "price": -105, "point": 211.0},
            {"name": "Under", "price": -115, "point": 211.0}
          ]
        }
      ]
    }
  ]
}]
```

---

### The Odds API - MLB

**Sport Key**: `baseball_mlb`

#### Available Markets
- Moneyline (h2h)
- Spreads (handicap)
- Over/Under (totals)
- Innings odds (1st 5 innings)
- **Player Props** (US & AU bookmakers only):
  - Pitcher strikeouts, outs
  - Home runs
  - Hits, RBIs

#### Example Request
```http
GET https://api.the-odds-api.com/v4/sports/baseball_mlb/odds?regions=us&markets=h2h,spreads,totals&oddsFormat=american&apiKey=YOUR_API_KEY
```

#### Example Response
```json
[{
  "id": "5c4d8f368956b33f3f2639aed5152e2f",
  "sport_key": "baseball_mlb",
  "sport_title": "MLB",
  "commence_time": "2023-07-19T01:40:00Z",
  "home_team": "Seattle Mariners",
  "away_team": "Minnesota Twins",
  "bookmakers": [
    {
      "key": "draftkings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {"name": "Minnesota Twins", "price": 105},
            {"name": "Seattle Mariners", "price": -125}
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {"name": "Minnesota Twins", "price": -200, "point": 1.5},
            {"name": "Seattle Mariners", "price": 170, "point": -1.5}
          ]
        }
      ]
    }
  ]
}]
```

#### Historical Data
Historical MLB odds available from mid-2020 for featured markets (moneyline, spreads, totals).

---

## SportsGameOdds API

**Base URL**: `https://api.sportsgameodds.com/v1`
**Client**: `src/ingest/sportgameodds_client.py`
**Advantages**: More comprehensive player props, better player data with IDs

### Authentication
```javascript
headers: {
  'X-Api-Key': 'YOUR_API_KEY'
}
```

### SportsGameOdds - NFL

#### Available Markets
- Moneylines
- Spreads
- Over-Unders
- **Player Props**:
  - Passing yards, TDs, completions, attempts, interceptions
  - Rushing yards, attempts, TDs
  - Receiving yards, receptions, TDs
  - Anytime touchdown, First touchdown
  - Field goals, kicking points
- Team Props
- Futures
- Partial Game (1st half)
- Pre-Market Odds
- Fair Odds (zero-juice)
- Avg Sportsbook Odds
- Live Odds (in-game)

#### Example Request
```javascript
fetch('https://api.sportsgameodds.com/v1/odds?oddsAvailable=true&limit=10&leagueID=NFL&oddIDs=points-home-game-ml-home', {
  headers: {
    'X-Api-Key': 'YOUR_API_KEY'
  }
})
```

#### Query Parameters
- `oddsAvailable=true` - Filter for available odds
- `limit=10` - Limit number of results
- `leagueID=NFL` - Specify league (NFL, NBA, MLB)
- `oddIDs=points-home-game-ml-home` - Specific market IDs

#### Visual Examples
**Moneyline Query**: See `REFERENCES/NFL Moneyline Query Example.png`
**Moneyline Response**: See `REFERENCES/NFL Moneyline Query Example Return.png`
**Props Query**: See `REFERENCES/NFL Props Query Example.png`
**Props Response**: See `REFERENCES/NFL Props Query Example Return.png`

---

### SportsGameOdds - NBA

#### Available Markets
- Spreads
- Moneylines
- Over-Unders
- **Player Props**:
  - Points, rebounds, assists
  - Three-pointers made
  - First basket
  - Blocks, steals, turnovers
- Team Props
- Futures
- Partial Game (1st half, quarters)
- Pre-Market Odds
- Fair Odds (zero-juice)
- Avg Sportsbook Odds
- Live Odds (in-game)

#### Visual Examples
**Moneyline Query**: See `REFERENCES/NBA Moneyline Query Example.png`
**Moneyline Response**: See `REFERENCES/NBA Moneyline Query Example Return.png`
**Props Query**: See `REFERENCES/NBA Props Query Example.png`
**Props Response**: See `REFERENCES/NBA Props Query Example Return.png`

---

### SportsGameOdds - MLB

#### Available Markets
- Moneylines
- Spreads
- Over-Unders
- **Player Props**:
  - Pitcher strikeouts, outs
  - Home runs
  - Hits, RBIs, stolen bases
- Team Props
- Futures
- Partial Game (1st 5 innings)
- Pre-Market Odds
- Fair Odds (zero-juice)
- Avg Sportsbook Odds
- Live Odds (in-game)

#### Visual Examples
**Moneyline Query**: See `REFERENCES/MLB Moneyline Query Example.png`
**Moneyline Response**: See `REFERENCES/MLB Moneyline Query Return.png`
**Props Query**: See `REFERENCES/MLB Props Query Example Return.png`

---

## API Comparison

| Feature | The Odds API | SportsGameOdds API |
|---------|--------------|-------------------|
| **Free Tier** | 500 requests/month | TBD |
| **Player IDs** | ❌ No | ✅ Yes |
| **Props Coverage** | Good | Excellent |
| **Bookmakers** | 30+ | Multiple |
| **Live Odds** | ✅ Yes | ✅ Yes |
| **Historical Data** | ✅ Yes (mid-2020+) | ✅ Yes |
| **Fair Odds** | ❌ No | ✅ Yes (zero-juice) |
| **API Version** | v4 | v1 |
| **Documentation** | Excellent | Good |

---

## Resources

### Reference Images
All example queries and responses are stored in:
```
docs/api/REFERENCES/
├── NFL Moneyline Query Example.png
├── NFL Moneyline Query Example Return.png
├── NFL Props Query Example.png
├── NFL Props Query Example Return.png
├── NBA Moneyline Query Example.png
├── NBA Props Query Example.png
├── NBA Props Query Example Return.png
├── MLB Moneyline Query Example.png
├── MLB Moneyline Query Return.png
└── MLB Props Query Example Return.png
```

### Implementation Files
- **The Odds API Client**: `src/ingest/odds_api_client.py`
- **SportsGameOdds Client**: `src/ingest/sportgameodds_client.py`

### Configuration
- **API Keys**: Stored in `.env` file
  - `ODDS_API_KEY` - The Odds API key
  - `SPORTGAMEODDS_API_KEY` - SportsGameOdds API key

### External Links
- [The Odds API Documentation](https://the-odds-api.com/liveapi/guides/v4/)
- [SportsGameOdds Website](https://sportsgameodds.com/)

---

## Future API Integrations

Potential APIs to explore:
- Sleeper API (player stats, roster data)
- ESPN API (advanced stats)
- NFL/NBA/MLB official APIs
- Weather APIs for game conditions

---

**Last Updated**: 2025-10-13
**Maintained By**: BetterBros Props Team