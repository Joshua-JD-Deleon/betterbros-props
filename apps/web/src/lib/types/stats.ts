/**
 * Comprehensive stat type definitions for all supported sports
 * Based on Sleeper Picks statistical categories
 */

export type Sport = 'NFL' | 'NBA' | 'MLB' | 'NHL';

// ============================================================================
// NFL Stats
// ============================================================================

export type NFLStatType =
  // Passing
  | 'Passing Yards'
  | 'Passing TDs'
  | 'Interceptions'
  | 'Pass Completions'
  | 'Pass Attempts'
  | 'Completion %'

  // Rushing
  | 'Rushing Yards'
  | 'Rushing TDs'
  | 'Rushing Attempts'
  | 'Yards Per Carry'

  // Receiving
  | 'Receptions'
  | 'Receiving Yards'
  | 'Receiving TDs'
  | 'Targets'

  // Defense
  | 'Solo Tackles'
  | 'Assisted Tackles'
  | 'Total Tackles'
  | 'Sacks'
  | 'Interceptions Def'
  | 'Forced Fumbles'
  | 'Fumble Recoveries'

  // Kicking
  | 'Field Goals Made'
  | 'Extra Points Made'
  | 'Kicking Points'

  // Special/Combined
  | 'Anytime TD'
  | 'First TD'
  | 'Pass + Rush Yards'
  | 'Rush + Rec Yards'
  | 'Fantasy Points';

export const NFL_STAT_ABBREVIATIONS: Record<NFLStatType, string> = {
  'Passing Yards': 'PASS YD',
  'Passing TDs': 'PASS TD',
  'Interceptions': 'INT',
  'Pass Completions': 'CMP',
  'Pass Attempts': 'ATT',
  'Completion %': 'CMP%',
  'Rushing Yards': 'RUSH YD',
  'Rushing TDs': 'RUSH TD',
  'Rushing Attempts': 'RUSH ATT',
  'Yards Per Carry': 'YPC',
  'Receptions': 'REC',
  'Receiving Yards': 'REC YD',
  'Receiving TDs': 'REC TD',
  'Targets': 'TGT',
  'Solo Tackles': 'SOLO TKL',
  'Assisted Tackles': 'AST TKL',
  'Total Tackles': 'TOT TKL',
  'Sacks': 'SACK',
  'Interceptions Def': 'INT',
  'Forced Fumbles': 'FF',
  'Fumble Recoveries': 'FR',
  'Field Goals Made': 'FGM',
  'Extra Points Made': 'XPM',
  'Kicking Points': 'KICK PTS',
  'Anytime TD': 'ANYTIME TD',
  'First TD': 'FIRST TD',
  'Pass + Rush Yards': 'PASS+RUSH YD',
  'Rush + Rec Yards': 'RUSH+REC YD',
  'Fantasy Points': 'FPTS',
};

// ============================================================================
// NBA Stats
// ============================================================================

export type NBAStatType =
  // Standard
  | 'Points'
  | 'Rebounds'
  | 'Assists'
  | 'Steals'
  | 'Blocks'
  | 'Turnovers'
  | 'Field Goals Made'
  | 'Field Goal Attempts'
  | 'Three Pointers Made'
  | 'Free Throws Made'

  // Quarter-specific
  | '1st Quarter Points'
  | '1st Quarter Rebounds'
  | '1st Quarter Assists'

  // Milestones
  | 'Double Double'
  | 'Triple Double'

  // Fantasy
  | 'Fantasy Points';

export const NBA_STAT_ABBREVIATIONS: Record<NBAStatType, string> = {
  'Points': 'PTS',
  'Rebounds': 'REB',
  'Assists': 'AST',
  'Steals': 'STL',
  'Blocks': 'BLK',
  'Turnovers': 'TO',
  'Field Goals Made': 'FGM',
  'Field Goal Attempts': 'FGA',
  'Three Pointers Made': '3PM',
  'Free Throws Made': 'FTM',
  '1st Quarter Points': '1Q PTS',
  '1st Quarter Rebounds': '1Q REB',
  '1st Quarter Assists': '1Q AST',
  'Double Double': 'DBL DBL',
  'Triple Double': 'TRPL DBL',
  'Fantasy Points': 'FPTS',
};

// ============================================================================
// MLB Stats
// ============================================================================

export type MLBStatType =
  // Pitcher Stats
  | 'Strikeouts'
  | 'Hits Allowed'
  | 'Earned Runs'
  | 'Outs'
  | 'Pitcher Walks'
  | 'Innings Pitched'
  | 'Wins'

  // Batter Stats
  | 'Singles'
  | 'Doubles'
  | 'Triples'
  | 'Home Runs'
  | 'Total Bases'
  | 'Hits'
  | 'Runs'
  | 'RBI'
  | 'Batter Walks'
  | 'Stolen Bases'

  // Fantasy
  | 'Fantasy Points';

export const MLB_STAT_ABBREVIATIONS: Record<MLBStatType, string> = {
  'Strikeouts': 'K',
  'Hits Allowed': 'HA',
  'Earned Runs': 'ER',
  'Outs': 'OUTS',
  'Pitcher Walks': 'P BB',
  'Innings Pitched': 'IP',
  'Wins': 'W',
  'Singles': '1B',
  'Doubles': '2B',
  'Triples': '3B',
  'Home Runs': 'HR',
  'Total Bases': 'BASES',
  'Hits': 'HITS',
  'Runs': 'RUNS',
  'RBI': 'RBI',
  'Batter Walks': 'BB',
  'Stolen Bases': 'SB',
  'Fantasy Points': 'FPTS',
};

// ============================================================================
// NHL Stats
// ============================================================================

export type NHLStatType =
  // Skater Stats
  | 'Goals'
  | 'Assists'
  | 'Points'
  | 'Power Play Points'
  | 'Shots on Goal'
  | 'Blocked Shots'
  | 'Hits'
  | 'Plus Minus'

  // Goalie Stats
  | 'Saves'
  | 'Goals Against'
  | 'Save Percentage'
  | 'Shutouts';

export const NHL_STAT_ABBREVIATIONS: Record<NHLStatType, string> = {
  'Goals': 'G',
  'Assists': 'A',
  'Points': 'PTS',
  'Power Play Points': 'PPP',
  'Shots on Goal': 'SOG',
  'Blocked Shots': 'BKS',
  'Hits': 'HIT',
  'Plus Minus': '+/-',
  'Saves': 'SV',
  'Goals Against': 'GA',
  'Save Percentage': 'SV%',
  'Shutouts': 'SO',
};

// ============================================================================
// Combined Types
// ============================================================================

export type StatType = NFLStatType | NBAStatType | MLBStatType | NHLStatType;

export const STAT_ABBREVIATIONS = {
  NFL: NFL_STAT_ABBREVIATIONS,
  NBA: NBA_STAT_ABBREVIATIONS,
  MLB: MLB_STAT_ABBREVIATIONS,
  NHL: NHL_STAT_ABBREVIATIONS,
} as const;

// ============================================================================
// Stat Categories
// ============================================================================

export type StatCategory =
  | 'Passing'
  | 'Rushing'
  | 'Receiving'
  | 'Defense'
  | 'Kicking'
  | 'Combined'
  | 'Scoring'
  | 'Rebounding'
  | 'Playmaking'
  | 'Pitching'
  | 'Batting'
  | 'Skater'
  | 'Goalie';

export const NFL_STAT_CATEGORIES: Record<StatCategory, NFLStatType[]> = {
  Passing: ['Passing Yards', 'Passing TDs', 'Interceptions', 'Pass Completions', 'Pass Attempts', 'Completion %'],
  Rushing: ['Rushing Yards', 'Rushing TDs', 'Rushing Attempts', 'Yards Per Carry'],
  Receiving: ['Receptions', 'Receiving Yards', 'Receiving TDs', 'Targets'],
  Defense: ['Solo Tackles', 'Assisted Tackles', 'Total Tackles', 'Sacks', 'Interceptions Def', 'Forced Fumbles', 'Fumble Recoveries'],
  Kicking: ['Field Goals Made', 'Extra Points Made', 'Kicking Points'],
  Combined: ['Anytime TD', 'First TD', 'Pass + Rush Yards', 'Rush + Rec Yards', 'Fantasy Points'],
  Scoring: [],
  Rebounding: [],
  Playmaking: [],
  Pitching: [],
  Batting: [],
  Skater: [],
  Goalie: [],
};

export const NBA_STAT_CATEGORIES: Record<StatCategory, NBAStatType[]> = {
  Scoring: ['Points', 'Field Goals Made', 'Field Goal Attempts', 'Three Pointers Made', 'Free Throws Made', '1st Quarter Points'],
  Rebounding: ['Rebounds', '1st Quarter Rebounds'],
  Playmaking: ['Assists', '1st Quarter Assists'],
  Defense: ['Steals', 'Blocks'],
  Combined: ['Turnovers', 'Double Double', 'Triple Double', 'Fantasy Points'],
  Passing: [],
  Rushing: [],
  Receiving: [],
  Kicking: [],
  Pitching: [],
  Batting: [],
  Skater: [],
  Goalie: [],
};

export const MLB_STAT_CATEGORIES: Record<StatCategory, MLBStatType[]> = {
  Pitching: ['Strikeouts', 'Hits Allowed', 'Earned Runs', 'Outs', 'Pitcher Walks', 'Innings Pitched', 'Wins'],
  Batting: ['Singles', 'Doubles', 'Triples', 'Home Runs', 'Total Bases', 'Hits', 'Runs', 'RBI', 'Batter Walks', 'Stolen Bases'],
  Combined: ['Fantasy Points'],
  Passing: [],
  Rushing: [],
  Receiving: [],
  Defense: [],
  Kicking: [],
  Scoring: [],
  Rebounding: [],
  Playmaking: [],
  Skater: [],
  Goalie: [],
};

export const NHL_STAT_CATEGORIES: Record<StatCategory, NHLStatType[]> = {
  Skater: ['Goals', 'Assists', 'Points', 'Power Play Points', 'Shots on Goal', 'Blocked Shots', 'Hits', 'Plus Minus'],
  Goalie: ['Saves', 'Goals Against', 'Save Percentage', 'Shutouts'],
  Passing: [],
  Rushing: [],
  Receiving: [],
  Defense: [],
  Kicking: [],
  Combined: [],
  Scoring: [],
  Rebounding: [],
  Playmaking: [],
  Pitching: [],
  Batting: [],
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getStatAbbreviation(sport: Sport, stat: StatType): string {
  return STAT_ABBREVIATIONS[sport][stat as keyof typeof STAT_ABBREVIATIONS[typeof sport]] || stat;
}

export function getStatsByCategory(sport: Sport, category: StatCategory): StatType[] {
  switch (sport) {
    case 'NFL':
      return NFL_STAT_CATEGORIES[category] || [];
    case 'NBA':
      return NBA_STAT_CATEGORIES[category] || [];
    case 'MLB':
      return MLB_STAT_CATEGORIES[category] || [];
    case 'NHL':
      return NHL_STAT_CATEGORIES[category] || [];
    default:
      return [];
  }
}

export function getAllStatsForSport(sport: Sport): StatType[] {
  switch (sport) {
    case 'NFL':
      return Object.keys(NFL_STAT_ABBREVIATIONS) as NFLStatType[];
    case 'NBA':
      return Object.keys(NBA_STAT_ABBREVIATIONS) as NBAStatType[];
    case 'MLB':
      return Object.keys(MLB_STAT_ABBREVIATIONS) as MLBStatType[];
    case 'NHL':
      return Object.keys(NHL_STAT_ABBREVIATIONS) as NHLStatType[];
    default:
      return [];
  }
}

export function getCategoriesForSport(sport: Sport): StatCategory[] {
  switch (sport) {
    case 'NFL':
      return ['Passing', 'Rushing', 'Receiving', 'Defense', 'Kicking', 'Combined'];
    case 'NBA':
      return ['Scoring', 'Rebounding', 'Playmaking', 'Defense', 'Combined'];
    case 'MLB':
      return ['Pitching', 'Batting', 'Combined'];
    case 'NHL':
      return ['Skater', 'Goalie'];
    default:
      return [];
  }
}

// ============================================================================
// Stat Metadata
// ============================================================================

export interface StatMetadata {
  displayName: string;
  abbreviation: string;
  category: StatCategory;
  sport: Sport;
  description: string;
  isCountingStat: boolean;
  isPercentageStat: boolean;
  isCombinedStat: boolean;
  isMilestoneStat: boolean;
}

export const STAT_METADATA: Partial<Record<StatType, StatMetadata>> = {
  // NFL
  'Solo Tackles': {
    displayName: 'Solo Tackles',
    abbreviation: 'SOLO TKL',
    category: 'Defense',
    sport: 'NFL',
    description: 'Primary or only player to tackle the offensive ball carrier (excludes special teams)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: false,
  },
  'Assisted Tackles': {
    displayName: 'Assisted Tackles',
    abbreviation: 'AST TKL',
    category: 'Defense',
    sport: 'NFL',
    description: 'Tackles made together with other players (excludes special teams)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: false,
  },
  'Total Tackles': {
    displayName: 'Total Tackles',
    abbreviation: 'TOT TKL',
    category: 'Defense',
    sport: 'NFL',
    description: 'Combined solo tackles + assisted tackles',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },
  'Anytime TD': {
    displayName: 'Anytime Touchdown',
    abbreviation: 'ANYTIME TD',
    category: 'Combined',
    sport: 'NFL',
    description: 'Player in possession of the ball in the opponent\'s end zone (excludes passing TDs)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: true,
  },
  'First TD': {
    displayName: 'First Touchdown',
    abbreviation: 'FIRST TD',
    category: 'Combined',
    sport: 'NFL',
    description: 'First rushing, receiving, defensive, or special teams TD in a game (excludes passing TDs)',
    isCountingStat: false,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: true,
  },
  'Pass + Rush Yards': {
    displayName: 'Passing + Rushing Yards',
    abbreviation: 'PASS+RUSH YD',
    category: 'Combined',
    sport: 'NFL',
    description: 'Sum of passing and rushing yards from scrimmage',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },
  'Rush + Rec Yards': {
    displayName: 'Rushing + Receiving Yards',
    abbreviation: 'RUSH+REC YD',
    category: 'Combined',
    sport: 'NFL',
    description: 'Sum of rushing and receiving yards from scrimmage',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },
  'Kicking Points': {
    displayName: 'Kicking Points',
    abbreviation: 'KICK PTS',
    category: 'Kicking',
    sport: 'NFL',
    description: 'Total points from made kicks (XP=1pt, FG=3pts)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },

  // NBA
  'Double Double': {
    displayName: 'Double Double',
    abbreviation: 'DBL DBL',
    category: 'Combined',
    sport: 'NBA',
    description: 'Double figures (10+) in two of: points, rebounds, assists, steals, blocks',
    isCountingStat: false,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: true,
  },
  'Triple Double': {
    displayName: 'Triple Double',
    abbreviation: 'TRPL DBL',
    category: 'Combined',
    sport: 'NBA',
    description: 'Double figures (10+) in three of: points, rebounds, assists, steals, blocks',
    isCountingStat: false,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: true,
  },
  '1st Quarter Points': {
    displayName: '1st Quarter Points',
    abbreviation: '1Q PTS',
    category: 'Scoring',
    sport: 'NBA',
    description: 'Points scored in the 1st quarter only (excludes overtime)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: false,
  },

  // MLB
  'Total Bases': {
    displayName: 'Total Bases',
    abbreviation: 'BASES',
    category: 'Batting',
    sport: 'MLB',
    description: 'Bases gained through hits: 1B=1, 2B=2, 3B=3, HR=4 (excludes walks/errors)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },
  'Hits Allowed': {
    displayName: 'Hits Allowed',
    abbreviation: 'HA',
    category: 'Pitching',
    sport: 'MLB',
    description: 'Number of hits given up by a pitcher (excludes walks)',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: false,
  },

  // NHL
  'Power Play Points': {
    displayName: 'Power Play Points',
    abbreviation: 'PPP',
    category: 'Skater',
    sport: 'NHL',
    description: 'Goals and assists earned during powerplay man advantages',
    isCountingStat: true,
    isPercentageStat: false,
    isCombinedStat: true,
    isMilestoneStat: false,
  },
  'Shutouts': {
    displayName: 'Shutouts',
    abbreviation: 'SO',
    category: 'Goalie',
    sport: 'NHL',
    description: 'Goalie allows zero goals against',
    isCountingStat: false,
    isPercentageStat: false,
    isCombinedStat: false,
    isMilestoneStat: true,
  },
};
