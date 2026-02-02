# NBA Statistics Analysis Application

A comprehensive Python application for importing, analyzing, and visualizing NBA statistics with easy-to-configure variables.

## Features

- **Player Analysis**: Fetch and visualize individual player statistics
- **Team Analysis**: Analyze team performance throughout a season
- **League Leaders**: View top performers in any statistical category
- **Player Comparison**: Compare statistics between two players
- **Advanced Metrics**: Calculate TS%, EFG%, Game Score, and more
- **Multiple Visualizations**: Line charts, bar charts, distributions, and more
- **Easy Configuration**: Simply modify variables at the top of main.py

## Installation

1. **Install Python** (3.8 or higher recommended)

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. Open `main.py` in your editor

2. Modify the configuration variables at the top:
   ```python
   ANALYSIS_TYPE = 'player'          # Choose analysis type
   PLAYER_NAME = 'LeBron James'      # Player to analyze
   SEASON = '2023-24'                # Season to analyze
   STATS_TO_PLOT = ['PTS', 'AST', 'REB']  # Stats to visualize
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Check the `outputs` folder for generated charts and CSV files

## Configuration Options

### Analysis Types

Set `ANALYSIS_TYPE` to one of:
- `'player'` - Analyze single player statistics
- `'team'` - Analyze team performance
- `'league_leaders'` - View league leaders in a category
- `'player_comparison'` - Compare two players side-by-side

### Common Variables

```python
# Player Settings
PLAYER_NAME = 'LeBron James'           # Full player name
PLAYER_NAME_2 = 'Stephen Curry'        # Second player (for comparison)
SEASON = '2023-24'                     # Format: 'YYYY-YY'

# Team Settings
TEAM_NAME = 'LAL'                      # Team abbreviation or full name

# Statistics to Plot
STATS_TO_PLOT = ['PTS', 'AST', 'REB']  # Any valid NBA stat

# Visualization Settings
SHOW_PLOTS = True                      # Display plots in window
SAVE_PLOTS = True                      # Save plots to files
OUTPUT_FOLDER = 'outputs'              # Output directory

# Advanced Options
CALCULATE_ROLLING_AVG = True           # Calculate rolling averages
ROLLING_WINDOW = 5                     # Rolling average window size
SHOW_ADVANCED_STATS = True             # Calculate advanced metrics
```

## Available Statistics

Common stats you can use in `STATS_TO_PLOT`:
- `PTS` - Points
- `AST` - Assists
- `REB` - Rebounds
- `STL` - Steals
- `BLK` - Blocks
- `FG_PCT` - Field Goal Percentage
- `FG3_PCT` - Three-Point Percentage
- `FT_PCT` - Free Throw Percentage
- `TOV` - Turnovers
- `PF` - Personal Fouls

## Module Usage

You can also use the modules directly in your own scripts:

```python
from utils import NBADataFetcher, NBADataProcessor, NBAVisualizer

# Initialize
fetcher = NBADataFetcher()
processor = NBADataProcessor()
visualizer = NBAVisualizer()

# Fetch data
df = fetcher.get_player_season_stats('LeBron James', '2023-24')

# Process data
df = processor.calculate_advanced_stats(df)
summary = processor.get_summary_stats(df, ['PTS', 'AST', 'REB'])

# Visualize
visualizer.plot_line_chart(df, 'GAME_DATE', 'PTS', 
                           title='Points per Game')
```

## Examples

### Example 1: Analyze Player Performance
```python
ANALYSIS_TYPE = 'player'
PLAYER_NAME = 'Stephen Curry'
SEASON = '2023-24'
STATS_TO_PLOT = ['PTS', 'FG3M', 'AST']
```

### Example 2: Compare Two Players
```python
ANALYSIS_TYPE = 'player_comparison'
PLAYER_NAME = 'LeBron James'
PLAYER_NAME_2 = 'Kevin Durant'
SEASON = '2023-24'
COMPARISON_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK']
```

### Example 3: View League Leaders
```python
ANALYSIS_TYPE = 'league_leaders'
STAT_CATEGORY = 'PTS'  # Points leaders
PER_MODE = 'PerGame'
TOP_N = 15
```

### Example 4: Analyze Team Performance
```python
ANALYSIS_TYPE = 'team'
TEAM_NAME = 'GSW'  # Golden State Warriors
SEASON = '2023-24'
STATS_TO_PLOT = ['PTS', 'REB', 'AST']
```

## Team Abbreviations

Common NBA team abbreviations:
- ATL, BOS, BKN, CHA, CHI, CLE, DAL, DEN, DET, GSW
- HOU, IND, LAC, LAL, MEM, MIA, MIL, MIN, NOP, NYK
- OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA, WAS

## Output Files

When `SAVE_PLOTS = True`, the application creates:
- **CSV files**: Raw statistics data
- **PNG files**: High-resolution charts (300 DPI)

All files are saved in the folder specified by `OUTPUT_FOLDER` (default: `outputs/`)

## Troubleshooting

**Player not found error**:
- Use the player's full name (e.g., "LeBron James" not "Lebron")
- Make sure the spelling is correct

**No data for season**:
- Verify the season format: 'YYYY-YY' (e.g., '2023-24')
- Check that the player/team was active in that season

**Module import errors**:
- Make sure all packages are installed: `pip install -r requirements.txt`
- Ensure you're in the correct directory

## Advanced Features

### Custom Analysis Scripts

Create your own analysis by using the utility modules:

```python
from utils import NBADataFetcher, NBADataProcessor, NBAVisualizer

fetcher = NBADataFetcher()

# Search for players
results = fetcher.search_players('James')
for player in results:
    print(player['full_name'])

# Get career stats
career_df = fetcher.get_player_career_stats('LeBron James')

# Calculate rolling averages
season_df = fetcher.get_player_season_stats('LeBron James', '2023-24')
season_df = processor.calculate_rolling_average(season_df, 'PTS', window=10)

# Custom visualization
visualizer.plot_scatter(season_df, 'AST', 'PTS', 
                        title='Assists vs Points',
                        color_column='REB')
```

## Data Source

This application uses the [nba_api](https://github.com/swar/nba_api) library, which provides access to official NBA statistics from stats.nba.com.

## License

This project is open source and available for personal and educational use.

## Support

For issues or questions:
1. Check that all dependencies are installed correctly
2. Verify your configuration variables match the expected format
3. Ensure you have an active internet connection (required for NBA API)

---

**Happy Analyzing!** 🏀📊
