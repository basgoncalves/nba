# League Overview - Interactive Bubble Plot Guide

## What is it?

The League Overview analysis creates **interactive bubble plots** that visualize all NBA players in a season, showing the relationship between playing time, performance, and overall player rating.

**NEW**: Now supports multiple stats, season ranges, and **team filtering**!

## Visualization Details

### Axes & Bubbles
- **X-Axis**: Minutes played per game (MIN)
- **Y-Axis**: Your chosen statistics (can plot multiple!)
- **Bubble Size**: Player Rating (composite metric)
- **Color**: Gradient based on player rating (darker = higher rating)

### Interactive Features
- **Team Filter Dropdown**: Select any team to focus on their players
  - Non-selected teams' players appear grayed out (15% opacity)
  - Selected team players maintain full color with white borders
  - "All Teams" option to view everyone
  - Fully reversible - switch between teams instantly
- **Hover Details**: See player name, team, exact stats
- **Zoom & Pan**: Explore dense areas of the plot
- **Export**: Save as PNG or download data

### Player Rating Formula
The player rating is calculated as:
```
Rating = PTS + (AST × 1.5) + (REB × 1.2) + (STL × 2) + (BLK × 2) - (TOV × 1.5)
```

This gives a balanced view of a player's overall contribution.

## How to Use

### 1. Basic Configuration (Single Season, Multiple Stats)

```python
ANALYSIS_TYPE = 'league_overview'
DOWNLOAD_LATEST = True
OVERVIEW_SEASONS_START = 2023       # Year for 2023-24 season
OVERVIEW_SEASONS_END = 2023         # Same year = single season
OVERVIEW_STATS = ['PTS', 'AST', 'REB']  # Create 3 bubble plots!
MIN_GAMES_PLAYED = 20
```

### 2. Multi-Season Configuration

```python
ANALYSIS_TYPE = 'league_overview'
DOWNLOAD_LATEST = True
OVERVIEW_SEASONS_START = 2021       # Start at 2021-22
OVERVIEW_SEASONS_END = 2023         # End at 2023-24
OVERVIEW_STATS = ['PTS', 'AST']     # 2 stats × 3 seasons = 6 plots!
MIN_GAMES_PLAYED = 25
```

This automatically generates:
- 2021-22 season
- 2022-23 season  
- 2023-24 season

And creates bubble plots for each stat in each season!

### 2. Run the Analysis

```bash
python __main__.py
```

**What happens:**
1. Data is downloaded/loaded from cache
2. Player ratings calculated and filtered
3. Interactive HTML files created
4. **Files automatically open in your default browser!** 🎉

### 3. View the Results

The analysis generates:
- **CSV files**: `outputs/league_overview_YYYY-YY_processed.csv` (one per season)
- **HTML files**: `outputs/league_overview_YYYY-YY_STAT_bubble.html` (one per stat per season)

**Auto-Open Feature:**
- When `SHOW_PLOTS = True`, all HTML files open automatically in your browser
- Each visualization opens in a new tab
- Perfect for quick exploration!

**Control Auto-Opening:**
```python
SHOW_PLOTS = True   # Auto-open all HTML files in browser
SHOW_PLOTS = False  # Save files but don't open (good for batch processing)
```

For example, with 3 stats and 2 seasons, you get:
```
league_overview_2022-23_PTS_bubble.html
league_overview_2022-23_AST_bubble.html
league_overview_2022-23_REB_bubble.html
league_overview_2023-24_PTS_bubble.html
league_overview_2023-24_AST_bubble.html
league_overview_2023-24_REB_bubble.html
```

Open any HTML file in your web browser to interact with the visualization!

## Interactive Features

### Team Filter Dropdown (NEW!)
- **Located**: Top-left corner of each plot
- **Options**: "All Teams" + all 30 NBA teams
- **Functionality**:
  - Select any team to highlight their players
  - Non-selected teams fade to gray (15% opacity)
  - Selected team gets white borders for emphasis
  - Switch teams instantly - fully reversible
  - Great for comparing teams or focusing on specific rosters

### Hover Information
Hover over any bubble to see:
- Player name
- **Team** (NEW!)
- Minutes per game
- Selected stat value
- Player rating

### Zoom & Pan
- **Scroll**: Zoom in/out
- **Click & Drag**: Pan around the plot
- **Double-click**: Reset view

### Legend
Click on legend items to show/hide data ranges

## Use Cases

### 1. Compare Teams Across Statistics
```python
OVERVIEW_SEASONS_START = 2023
OVERVIEW_SEASONS_END = 2023
OVERVIEW_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK']
MIN_GAMES_PLAYED = 30
# Use team filter to compare Lakers vs Celtics across all stats!
```

### 2. Track Individual Team Performance Over Time
```python
OVERVIEW_SEASONS_START = 2020       # 2020-21 season
OVERVIEW_SEASONS_END = 2023         # 2023-24 season
OVERVIEW_STATS = ['PTS']
MIN_GAMES_PLAYED = 40
# Filter to one team and see roster evolution season-by-season!
```

### 3. Find Efficient Players by Team
```python
OVERVIEW_STATS = ['PTS']
MIN_GAMES_PLAYED = 30
# Filter by team, look for large bubbles on the left = high scoring with less minutes
```

### 4. Discover Assist Specialists
```python
OVERVIEW_STATS = ['AST']
MIN_GAMES_PLAYED = 25
# Top-right bubbles = high minutes + high assists + good rating
```

### 5. Multi-Metric Analysis
```python
OVERVIEW_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK', 'FG_PCT']
# Get comprehensive view across all major categories
```

## Tips

### Efficient Workflow with Multiple Stats
First run:
```python
DOWNLOAD_LATEST = True          # Download and cache data
OVERVIEW_STATS = ['PTS']        # Start with one stat
```

Add more stats without re-downloading:
```python
DOWNLOAD_LATEST = False                              # Use cached data!
OVERVIEW_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK'] # Add more stats
# Creates 4 new visualizations instantly!
```

### Season Range Best Practices
```python
# Single season
OVERVIEW_SEASONS_START = 2023
OVERVIEW_SEASONS_END = 2023

# Last 3 seasons
OVERVIEW_SEASONS_START = 2021
OVERVIEW_SEASONS_END = 2023

# Last 5 seasons
OVERVIEW_SEASONS_START = 2019
OVERVIEW_SEASONS_END = 2023
```

### Filter Quality
```python
MIN_GAMES_PLAYED = 10   # Include more players (bench players, rookies)
MIN_GAMES_PLAYED = 40   # Only regular starters and stars
MIN_GAMES_PLAYED = 60   # Only iron-man players (full season)
```

## Example Workflow

```python
# Step 1: Download multiple seasons
ANALYSIS_TYPE = 'league_overview'
DOWNLOAD_LATEST = True
OVERVIEW_SEASONS_START = 2022    # 2022-23 and 2023-24
OVERVIEW_SEASONS_END = 2023
OVERVIEW_STATS = ['PTS']         # Start with one stat
MIN_GAMES_PLAYED = 30

# Run: python __main__.py
# Result: 2 HTML files (one per season)

# Step 2: Add more stats using cached data
DOWNLOAD_LATEST = False          # Use cached data - instant!
OVERVIEW_STATS = ['PTS', 'AST', 'REB', 'STL']  # 4 stats

# Run: python __main__.py (very fast!)
# Result: 8 HTML files total (4 stats × 2 seasons)

# Step 3: Analyze a specific stat over longer period
OVERVIEW_SEASONS_START = 2020    # 4 seasons total
OVERVIEW_SEASONS_END = 2023
OVERVIEW_STATS = ['FG3M']        # Track 3-point shooting evolution
DOWNLOAD_LATEST = True           # Need to download 2020-21, 2021-22 data

# Run: python __main__.py
# Result: 4 HTML files showing 3-point shooting trends
```

## Interpreting the Plot

### Top-Right Quadrant
- High minutes + High stat + Large bubble
- **Elite performers** in this category

### Top-Left Quadrant  
- Low minutes + High stat + Large bubble
- **Efficient players** - productive per minute

### Bottom-Right Quadrant
- High minutes + Low stat + Small bubble
- Role players or defensive specialists

### Bottom-Left Quadrant
- Low minutes + Low stat
- Bench players or developing talent

### Large Bubbles
Anywhere on the plot = high overall player rating

### Small Bubbles
Specialized players or limited contributors

## Technical Notes

- Uses **Plotly** for interactive visualization
- HTML file is self-contained and portable
- Works in any modern web browser
- No internet connection needed to view saved HTML
- Responsive design adapts to screen size

## Troubleshooting

**"Plotly not installed" warning:**
```bash
pip install plotly
```

**No HTML file generated:**
- Check `SAVE_PLOTS = True` in configuration
- Verify `outputs` folder exists or can be created

**Empty or very sparse plot:**
- Lower `MIN_GAMES_PLAYED` value
- Check if data for the season is available
- Verify `OVERVIEW_SEASON` format (e.g., '2023-24')

## Advanced Customization

Want to modify the player rating formula? Edit the `analyze_league_overview` function in `__main__.py`:

```python
# Current formula (line ~440)
df['PLAYER_RATING'] = (
    df['PTS'] + 
    df['AST'] * 1.5 + 
    df['REB'] * 1.2 + 
    df['STL'] * 2 + 
    df['BLK'] * 2 - 
    df['TOV'] * 1.5
).round(1)

# Example: Emphasize scoring
df['PLAYER_RATING'] = (
    df['PTS'] * 2 +      # Double weight on points
    df['AST'] * 1.5 + 
    df['REB'] * 1.2
).round(1)
```

Happy analyzing! 🏀📊
