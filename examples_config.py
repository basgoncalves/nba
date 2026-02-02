# Example Configurations for NBA Analysis

# ====================
# Example 1: Single Season Player Analysis
# ====================
ANALYSIS_TYPE = 'player'
DOWNLOAD_LATEST = True
PLAYER_NAME = 'LeBron James'
SEASONS = ['2023-24']
STATS_TO_PLOT = ['PTS', 'AST', 'REB']

# ====================
# Example 2: Multi-Season Player Analysis
# ====================
ANALYSIS_TYPE = 'player'
DOWNLOAD_LATEST = True
PLAYER_NAME = 'Stephen Curry'
SEASONS = ['2021-22', '2022-23', '2023-24']
STATS_TO_PLOT = ['PTS', 'FG3M', 'AST']

# ====================
# Example 3: Quick Testing (Using Cached Data)
# ====================
ANALYSIS_TYPE = 'player'
DOWNLOAD_LATEST = False  # Use cached data - much faster!
PLAYER_NAME = 'LeBron James'
SEASONS = ['2023-24']
STATS_TO_PLOT = ['PTS', 'AST']

# ====================
# Example 4: Compare Players Across Multiple Seasons
# ====================
ANALYSIS_TYPE = 'player_comparison'
DOWNLOAD_LATEST = True
PLAYER_NAME = 'LeBron James'
PLAYER_NAME_2 = 'Kevin Durant'
SEASONS = ['2022-23', '2023-24']
COMPARISON_STATS = ['PTS', 'AST', 'REB', 'FG_PCT']

# ====================
# Example 5: Team Multi-Season Analysis
# ====================
ANALYSIS_TYPE = 'team'
DOWNLOAD_LATEST = True
TEAM_NAME = 'LAL'
SEASONS = ['2021-22', '2022-23', '2023-24']
STATS_TO_PLOT = ['PTS', 'REB', 'AST']

# ====================
# Example 6: League Leaders (Always Single Season)
# ====================
ANALYSIS_TYPE = 'league_leaders'
DOWNLOAD_LATEST = True
STAT_CATEGORY = 'PTS'
PER_MODE = 'PerGame'
TOP_N = 15
LEADERS_SEASON = '2023-24'

# ====================
# Example 7: Interactive League Overview Bubble Plot
# ====================
ANALYSIS_TYPE = 'league_overview'
DOWNLOAD_LATEST = True
OVERVIEW_SEASONS_START = 2023    # Start year (2023 = 2023-24 season)
OVERVIEW_SEASONS_END = 2023      # End year (same = single season)
OVERVIEW_STATS = ['PTS', 'AST', 'REB']  # Multiple stats!
MIN_GAMES_PLAYED = 30            # Filter for consistent players
# Creates interactive HTML bubble plot for EACH stat:
# X-axis: Minutes played per game
# Y-axis: Each stat (PTS, AST, REB)
# Bubble size: Player rating (composite score)
# Result: 3 HTML files (one per stat)

# ====================
# Example 8: Multi-Season League Overview
# ====================
ANALYSIS_TYPE = 'league_overview'
DOWNLOAD_LATEST = True
OVERVIEW_SEASONS_START = 2021    # Start at 2021-22
OVERVIEW_SEASONS_END = 2023      # End at 2023-24 (3 seasons!)
OVERVIEW_STATS = ['PTS', 'AST']  # 2 stats × 3 seasons = 6 visualizations
MIN_GAMES_PLAYED = 25
# Automatically generates all seasons in range:
# 2021-22, 2022-23, 2023-24
# Creates bubble plot for each season × stat combination
