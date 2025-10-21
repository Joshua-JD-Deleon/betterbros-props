/**
 * Props API Route
 * Fetches props from Python backend or returns mock data
 */

import { NextRequest, NextResponse } from 'next/server';
import type { FetchPropsRequest, FetchPropsResponse, Prop } from '@/lib/types/props';
import { mockProps } from '@/lib/mock-data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

/**
 * POST /api/props
 * Fetch props based on filters
 */
export async function POST(request: NextRequest) {
  try {
    const body: FetchPropsRequest = await request.json();
    const { filters = {}, use_mock = false, refresh_cache = false } = body;

    // Use Python backend by default
    if (!use_mock) {
      try {
        const pythonResponse = await callPythonBackend(filters);
        return NextResponse.json(pythonResponse);
      } catch (backendError) {
        console.error('Python backend error, falling back to mock data:', backendError);
        // Fall back to mock data if backend unavailable
        return handleMockData(filters);
      }
    }

    // Use mock data if explicitly requested
    return handleMockData(filters);

  } catch (error) {
    console.error('Props API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch props',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * Handle mock data response
 */
function handleMockData(filters: any): NextResponse {
  // Convert mock data to Prop format
  const props: Prop[] = mockProps.map((mockProp) => ({
    // Identifiers
    id: mockProp.id,
    player_id: mockProp.id + '_player',
    game_id: `game_${mockProp.sport}_${mockProp.game_time}`,

    // Player info
    player_name: mockProp.player,
    team: mockProp.team,
    opponent: mockProp.opponent,
    position: mockProp.position || 'UNK',

    // Prop details
    sport: mockProp.sport,
    stat_type: mockProp.stat_type,
    prop_type: mockProp.stat_type,
    line: mockProp.line,
    direction: 'over' as const,

    // Odds
    over_odds: mockProp.over_odds,
    under_odds: mockProp.under_odds,
    decimal_odds: convertToDecimal(mockProp.over_odds),

    // Probabilities
    prob_over: mockProp.confidence / 100,
    prob_under: 1 - mockProp.confidence / 100,
    confidence: mockProp.confidence,

    // Projections
    projection: mockProp.projection,

    // Expected value
    ev: mockProp.ev / 100,
    ev_percentage: mockProp.ev,

    // Market info
    market: mockProp.market,
    sportsbook: mockProp.market,

    // Game info
    game_time: mockProp.game_time,
    is_live: mockProp.is_live,

    // Metadata
    last_updated: new Date().toISOString(),
    source: 'mock',
  }));

  // Apply filters
  let filtered = props;

  if (filters.sport) {
    filtered = filtered.filter((p) => p.sport === filters.sport);
  }

  if (filters.min_ev !== undefined) {
    filtered = filtered.filter((p) => p.ev_percentage >= filters.min_ev);
  }

  if (filters.is_live !== undefined) {
    filtered = filtered.filter((p) => p.is_live === filters.is_live);
  }

  if (filters.position) {
    filtered = filtered.filter((p) => p.position === filters.position);
  }

  if (filters.market) {
    filtered = filtered.filter((p) => p.market === filters.market);
  }

  const response: FetchPropsResponse = {
    props: filtered,
    total_count: filtered.length,
    cached: false,
    api_credits_used: 0, // Mock doesn't use credits
    api_credits_remaining: 1000,
    timestamp: new Date().toISOString(),
  };

  return NextResponse.json(response);
}

/**
 * Convert American odds to decimal
 */
function convertToDecimal(americanOdds: number): number {
  if (americanOdds > 0) {
    return americanOdds / 100 + 1;
  } else {
    return 100 / Math.abs(americanOdds) + 1;
  }
}

/**
 * Call Python backend via HTTP
 */
async function callPythonBackend(filters: any) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';

  const requestBody = {
    sport: filters.sport || 'NFL',
    week: filters.week || 1,
    season: filters.season || '2024',
    minEV: filters.min_ev,
    liveOnly: filters.is_live || false,
  };

  const response = await fetch(`${backendUrl}/api/props`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();

  // Transform Python backend response to our frontend format
  const props: Prop[] = data.props.map((prop: any) => ({
    id: prop.id,
    player_id: prop.id + '_player',
    game_id: `game_${prop.sport}_${prop.game_time}`,
    player_name: prop.player,
    team: prop.team,
    opponent: prop.opponent,
    position: prop.position || 'UNK',
    sport: prop.sport,
    stat_type: prop.stat_type,
    prop_type: prop.stat_type,
    line: prop.line,
    direction: 'over' as const,
    over_odds: prop.over_odds,
    under_odds: prop.under_odds,
    decimal_odds: convertToDecimal(prop.over_odds),
    prob_over: prop.confidence / 100,
    prob_under: 1 - prop.confidence / 100,
    confidence: prop.confidence,
    projection: prop.line + (prop.confidence > 50 ? 1 : -1),
    ev: prop.ev / 100,
    ev_percentage: prop.ev,
    market: prop.market,
    sportsbook: prop.market,
    game_time: prop.game_time,
    is_live: prop.is_live,
    last_updated: new Date().toISOString(),
    source: 'backend',
  }));

  return {
    props,
    total_count: props.length,
    cached: data.cached || false,
    api_credits_used: data.apiCredits?.used || 10,
    api_credits_remaining: data.apiCredits?.remaining || 990,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Call Python backend (placeholder for future implementation)
 */
async function callPythonBackend(filters: any) {
  // This would call the Python backend via subprocess or HTTP
  // For now, this is a placeholder

  // Example implementation:
  // const { spawn } = require('child_process');
  // const python = spawn('python3', [
  //   'scripts/fetch_props.py',
  //   JSON.stringify(filters)
  // ]);

  throw new Error('Python backend integration not yet implemented');
}
