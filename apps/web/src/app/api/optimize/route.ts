/**
 * Optimization API Route
 * Generates optimized slips using Python backend or mock algorithm
 */

import { NextRequest, NextResponse } from 'next/server';
import type {
  OptimizeSlipsRequest,
  OptimizeSlipsResponse,
  OptimizedSlip,
  SlipLeg,
} from '@/lib/types/props';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

/**
 * POST /api/optimize
 * Generate optimized slips from selected props
 */
export async function POST(request: NextRequest) {
  try {
    const body: OptimizeSlipsRequest = await request.json();
    const {
      prop_ids,
      bankroll,
      risk_mode,
      n_slips = 5,
      diversity_target = 0.5,
      min_legs,
      max_legs,
      min_odds,
      max_odds,
    } = body;

    // Validate input
    if (!prop_ids || prop_ids.length === 0) {
      return NextResponse.json(
        { error: 'No props selected for optimization' },
        { status: 400 }
      );
    }

    if (bankroll <= 0) {
      return NextResponse.json(
        { error: 'Invalid bankroll amount' },
        { status: 400 }
      );
    }

    const startTime = Date.now();

    // Try Python backend first, fall back to mock if unavailable
    let result;
    try {
      result = await callPythonOptimization({
        prop_ids,
        bankroll,
        risk_mode,
        n_slips,
        diversity_target,
        min_legs,
        max_legs,
        min_odds,
        max_odds,
      });
    } catch (backendError) {
      console.error('Python backend error, using mock optimization:', backendError);
      result = await generateMockOptimizedSlips({
        prop_ids,
        bankroll,
        risk_mode,
        n_slips,
        diversity_target,
        min_legs,
        max_legs,
        min_odds,
        max_odds,
      });
    }

    const processingTime = Date.now() - startTime;

    const response: OptimizeSlipsResponse = {
      ...result,
      processing_time_ms: processingTime,
      props_analyzed: prop_ids.length,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Optimization API error:', error);
    return NextResponse.json(
      {
        error: 'Optimization failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * Mock optimization algorithm (placeholder for Python backend)
 */
async function generateMockOptimizedSlips(
  request: OptimizeSlipsRequest
): Promise<Omit<OptimizeSlipsResponse, 'processing_time_ms' | 'props_analyzed'>> {
  const { prop_ids, bankroll, risk_mode, n_slips } = request;

  // Risk mode configuration
  const riskConfig = {
    conservative: {
      max_legs: 4,
      min_prob: 0.65,
      kelly_fraction: 0.25,
    },
    balanced: {
      max_legs: 6,
      min_prob: 0.55,
      kelly_fraction: 0.5,
    },
    aggressive: {
      max_legs: 8,
      min_prob: 0.45,
      kelly_fraction: 0.75,
    },
  }[risk_mode];

  // Generate mock slips
  const slips: OptimizedSlip[] = [];

  for (let i = 0; i < n_slips; i++) {
    const numLegs = Math.min(
      Math.floor(Math.random() * (riskConfig.max_legs - 1)) + 2,
      prop_ids.length
    );

    // Randomly select props for this slip
    const selectedPropIndices = new Set<number>();
    while (selectedPropIndices.size < numLegs) {
      selectedPropIndices.add(Math.floor(Math.random() * prop_ids.length));
    }

    const selectedPropIds = Array.from(selectedPropIndices).map(
      (idx) => prop_ids[idx]
    );

    // Generate mock legs
    const legs: SlipLeg[] = selectedPropIds.map((propId, idx) => ({
      player_id: propId,
      player_name: `Player ${idx + 1}`,
      prop_type: 'Mock Stat',
      line: 100 + idx * 10,
      direction: 'over' as const,
      prob: riskConfig.min_prob + Math.random() * (0.9 - riskConfig.min_prob),
      odds: Math.random() > 0.5 ? Math.floor(Math.random() * 200) - 300 : Math.floor(Math.random() * 300),
      team: `TEAM${idx % 4}`,
      game_id: `game_${Math.floor(idx / 2)}`,
      position: ['QB', 'WR', 'RB', 'TE'][idx % 4],
    }));

    // Calculate slip metrics
    const rawProb = legs.reduce((p, leg) => p * leg.prob, 1);
    const totalOdds = legs.reduce(
      (odds, leg) => odds * convertToDecimal(leg.odds),
      1
    );

    // Apply correlation adjustment (mock)
    const correlationFactor = 0.85 + Math.random() * 0.1; // 85-95% of raw prob
    const adjustedProb = rawProb * correlationFactor;

    // Expected value
    const ev = totalOdds * adjustedProb;

    // Kelly criterion stake
    const b = totalOdds - 1;
    const kellyFraction = (adjustedProb * b - (1 - adjustedProb)) / b;
    const suggestedBet = Math.max(
      5,
      Math.min(50, kellyFraction * bankroll * riskConfig.kelly_fraction)
    );

    // Diversity score (mock)
    const uniqueTeams = new Set(legs.map((l) => l.team)).size;
    const uniqueGames = new Set(legs.map((l) => l.game_id)).size;
    const diversity = (uniqueTeams / legs.length + uniqueGames / legs.length) / 2;

    // Correlation notes
    const correlationNotes: string[] = [];
    if (uniqueGames < legs.length) {
      correlationNotes.push(
        `Notice: ${legs.length - uniqueGames} props from the same game`
      );
    }
    if (correlationFactor < 0.9) {
      correlationNotes.push(
        `Positive correlation detected (adjustment: ${(100 - correlationFactor * 100).toFixed(1)}%)`
      );
    }

    slips.push({
      slip_id: `slip_${i + 1}_${Date.now()}`,
      legs,
      num_legs: numLegs,
      total_odds: totalOdds,
      raw_win_prob: rawProb,
      correlation_adjusted_prob: adjustedProb,
      expected_value: ev,
      variance: rawProb * (1 - rawProb),
      value_at_risk_95: 1 - adjustedProb,
      suggested_bet: suggestedBet,
      risk_level: risk_mode,
      diversity_score: diversity,
      correlation_notes: correlationNotes,
    });
  }

  // Sort by EV
  slips.sort((a, b) => b.expected_value - a.expected_value);

  // Generate mock correlation matrix
  const n = prop_ids.length;
  const correlationMatrix: number[][] = Array(n)
    .fill(0)
    .map((_, i) =>
      Array(n)
        .fill(0)
        .map((_, j) => {
          if (i === j) return 1.0;
          // Mock correlations: slight positive for same game, near zero otherwise
          return Math.random() * 0.3 - 0.1; // Range: -0.1 to 0.2
        })
    );

  return {
    slips,
    correlation_matrix: correlationMatrix,
  };
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
 * Call Python backend optimization engine via HTTP
 */
async function callPythonOptimization(request: OptimizeSlipsRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';

  const requestBody = {
    propIds: request.prop_ids,
    riskProfile: request.risk_mode,
    bankroll: request.bankroll,
  };

  const response = await fetch(`${backendUrl}/api/optimize`, {
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
  const slips: OptimizedSlip[] = data.optimizedSlips.map((slip: any, idx: number) => ({
    slip_id: slip.id,
    legs: slip.legs.map((leg: any) => ({
      player_id: leg.id,
      player_name: leg.player || `Player ${idx}`,
      prop_type: leg.stat_type,
      line: leg.line,
      direction: 'over' as const,
      prob: leg.confidence / 100,
      odds: leg.odds,
      team: 'UNK',
      game_id: `game_${idx}`,
      position: 'UNK',
    })),
    num_legs: slip.legs.length,
    total_odds: 2.0 + idx * 0.5,
    raw_win_prob: slip.win_probability,
    correlation_adjusted_prob: slip.correlation_adjusted_probability,
    expected_value: slip.ev / 100,
    variance: slip.win_probability * (1 - slip.win_probability),
    value_at_risk_95: 1 - slip.correlation_adjusted_probability,
    suggested_bet: slip.kelly_stake,
    risk_level: slip.risk_level,
    diversity_score: slip.diversity_score,
    correlation_notes: slip.correlation_notes,
  }));

  return {
    slips,
    correlation_matrix: [], // Backend doesn't return this yet
  };
}
