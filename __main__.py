"""
NBA Statistics Analysis Application

Configure the variables below to customize your analysis:
- Change player names, teams, seasons, and statistics to analyze
- Modify visualization settings and output options
- Run the script to fetch data and generate visualizations
"""

from utils import NBADataFetcher, NBADataProcessor, NBAVisualizer
import pandas as pd

# ============================================================================
# CONFIGURATION - Modify these variables to customize your analysis
# ============================================================================

# Analysis Type: 'player', 'team', 'league_leaders', 'player_comparison'
ANALYSIS_TYPE = 'player_comparison'

# Player Settings (for 'player' and 'player_comparison' analysis)
PLAYER_NAME = 'LeBron James'              # Full player name
PLAYER_NAME_2 = 'Stephen Curry'           # Second player for comparison
SEASON = '2023-24'                         # Season format: 'YYYY-YY'

# Team Settings (for 'team' analysis)
TEAM_NAME = 'LAL'                          # Team abbreviation or full name

# League Leaders Settings (for 'league_leaders' analysis)
STAT_CATEGORY = 'PTS'                      # PTS, AST, REB, STL, BLK, etc.
PER_MODE = 'PerGame'                       # 'PerGame', 'Totals', 'Per48'
TOP_N = 10                                 # Number of leaders to show

# Statistics to Visualize
STATS_TO_PLOT = ['PTS', 'AST', 'REB']     # Stats for line charts
COMPARISON_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK']  # Stats for comparison

# Visualization Settings
SHOW_PLOTS = True                          # Display plots in window
SAVE_PLOTS = True                          # Save plots to files
OUTPUT_FOLDER = 'outputs'                  # Folder to save outputs

# Advanced Options
CALCULATE_ROLLING_AVG = True               # Calculate rolling averages
ROLLING_WINDOW = 5                         # Window size for rolling average
SHOW_ADVANCED_STATS = True                 # Calculate advanced metrics (TS%, EFG%, etc.)

# ============================================================================
# MAIN APPLICATION - No need to modify below unless customizing functionality
# ============================================================================

def main():
    """Main application function"""
    print("=" * 70)
    print("NBA STATISTICS ANALYSIS")
    print("=" * 70)
    
    # Initialize modules
    print("\nInitializing NBA data modules...")
    fetcher = NBADataFetcher()
    processor = NBADataProcessor()
    visualizer = NBAVisualizer()
    
    # Create output folder if saving plots
    if SAVE_PLOTS:
        import os
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Execute analysis based on type
    if ANALYSIS_TYPE == 'player':
        analyze_player(fetcher, processor, visualizer)
    
    elif ANALYSIS_TYPE == 'team':
        analyze_team(fetcher, processor, visualizer)
    
    elif ANALYSIS_TYPE == 'league_leaders':
        analyze_league_leaders(fetcher, processor, visualizer)
    
    elif ANALYSIS_TYPE == 'player_comparison':
        compare_players(fetcher, processor, visualizer)
    
    else:
        print(f"Unknown analysis type: {ANALYSIS_TYPE}")
        print("Valid types: 'player', 'team', 'league_leaders', 'player_comparison'")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)


def analyze_player(fetcher, processor, visualizer):
    """Analyze individual player statistics"""
    print(f"\nFetching data for {PLAYER_NAME} ({SEASON})...")
    
    try:
        # Fetch player season stats
        df = fetcher.get_player_season_stats(PLAYER_NAME, SEASON)
        print(f"✓ Retrieved {len(df)} games")
        
        # Calculate advanced stats if requested
        if SHOW_ADVANCED_STATS:
            df = processor.calculate_advanced_stats(df)
            print("✓ Calculated advanced statistics")
        
        # Calculate rolling averages if requested
        if CALCULATE_ROLLING_AVG:
            for stat in STATS_TO_PLOT:
                if stat in df.columns:
                    df = processor.calculate_rolling_average(df, stat, ROLLING_WINDOW)
            print(f"✓ Calculated {ROLLING_WINDOW}-game rolling averages")
        
        # Display summary statistics
        print(f"\n{PLAYER_NAME} - {SEASON} Season Summary:")
        print("-" * 70)
        summary = processor.get_summary_stats(df, STATS_TO_PLOT)
        print(summary)
        
        # Save to CSV
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{SEASON}_stats.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n✓ Saved data to {csv_path}")
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        # Line chart for each stat over the season
        game_numbers = list(range(1, len(df) + 1))
        df['GAME_NUM'] = game_numbers
        
        for stat in STATS_TO_PLOT:
            if stat in df.columns:
                save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{stat}.png" if SAVE_PLOTS else None
                visualizer.plot_line_chart(
                    df, 'GAME_NUM', stat,
                    title=f"{PLAYER_NAME} - {stat} per Game ({SEASON})",
                    xlabel='Game Number',
                    ylabel=stat,
                    save_path=save_path
                )
                print(f"  ✓ Created {stat} line chart")
        
        # Multiple stats on one chart
        if len(STATS_TO_PLOT) > 1:
            save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_multi_stats.png" if SAVE_PLOTS else None
            visualizer.plot_multiple_lines(
                df, 'GAME_NUM', STATS_TO_PLOT,
                title=f"{PLAYER_NAME} - Season Performance ({SEASON})",
                xlabel='Game Number',
                ylabel='Value',
                save_path=save_path
            )
            print(f"  ✓ Created multi-stat comparison chart")
        
        # Distribution plot for points
        if 'PTS' in df.columns:
            save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_PTS_distribution.png" if SAVE_PLOTS else None
            visualizer.plot_distribution(
                df, 'PTS',
                title=f"{PLAYER_NAME} - Points Distribution ({SEASON})",
                save_path=save_path
            )
            print(f"  ✓ Created points distribution chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def analyze_team(fetcher, processor, visualizer):
    """Analyze team statistics"""
    print(f"\nFetching data for {TEAM_NAME} ({SEASON})...")
    
    try:
        # Fetch team season stats
        df = fetcher.get_team_season_stats(TEAM_NAME, SEASON)
        print(f"✓ Retrieved {len(df)} games")
        
        # Calculate shooting percentages
        df = processor.calculate_shooting_percentages(df)
        
        # Display summary
        print(f"\n{TEAM_NAME} - {SEASON} Season Summary:")
        print("-" * 70)
        summary = processor.get_summary_stats(df, STATS_TO_PLOT)
        print(summary)
        
        # Calculate win percentage
        if 'WL' in df.columns:
            wins = (df['WL'] == 'W').sum()
            total_games = len(df)
            win_pct = (wins / total_games * 100).round(1)
            print(f"\nRecord: {wins}-{total_games - wins} ({win_pct}% Win Rate)")
        
        # Save data
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/{TEAM_NAME}_{SEASON}_stats.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n✓ Saved data to {csv_path}")
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        game_numbers = list(range(1, len(df) + 1))
        df['GAME_NUM'] = game_numbers
        
        save_path = f"{OUTPUT_FOLDER}/{TEAM_NAME}_performance.png" if SAVE_PLOTS else None
        visualizer.plot_multiple_lines(
            df, 'GAME_NUM', STATS_TO_PLOT,
            title=f"{TEAM_NAME} - Season Performance ({SEASON})",
            xlabel='Game Number',
            ylabel='Value',
            save_path=save_path
        )
        print(f"  ✓ Created performance chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def analyze_league_leaders(fetcher, processor, visualizer):
    """Analyze league leaders"""
    print(f"\nFetching {STAT_CATEGORY} leaders for {SEASON}...")
    
    try:
        # Fetch league leaders
        df = fetcher.get_league_leaders(SEASON, STAT_CATEGORY, PER_MODE)
        df_top = df.head(TOP_N)
        print(f"✓ Retrieved top {TOP_N} leaders")
        
        # Display leaders
        print(f"\nTop {TOP_N} in {STAT_CATEGORY} ({SEASON}):")
        print("-" * 70)
        display_cols = ['PLAYER', 'TEAM', STAT_CATEGORY]
        print(df_top[display_cols].to_string(index=False))
        
        # Save data
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/league_leaders_{STAT_CATEGORY}_{SEASON}.csv"
            df_top.to_csv(csv_path, index=False)
            print(f"\n✓ Saved data to {csv_path}")
        
        # Create visualization
        print("\nGenerating visualization...")
        save_path = f"{OUTPUT_FOLDER}/league_leaders_{STAT_CATEGORY}.png" if SAVE_PLOTS else None
        visualizer.plot_bar_chart(
            df_top, 'PLAYER', STAT_CATEGORY,
            title=f"Top {TOP_N} in {STAT_CATEGORY} ({SEASON})",
            save_path=save_path,
            horizontal=True
        )
        print(f"  ✓ Created leaders bar chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def compare_players(fetcher, processor, visualizer):
    """Compare two players"""
    print(f"\nComparing {PLAYER_NAME} vs {PLAYER_NAME_2} ({SEASON})...")
    
    try:
        # Fetch data for both players
        df1 = fetcher.get_player_season_stats(PLAYER_NAME, SEASON)
        df2 = fetcher.get_player_season_stats(PLAYER_NAME_2, SEASON)
        print(f"✓ Retrieved data for both players")
        
        # Compare statistics
        comparison = processor.compare_players(
            [df1, df2],
            [PLAYER_NAME, PLAYER_NAME_2],
            COMPARISON_STATS
        )
        
        # Display comparison
        print(f"\n{PLAYER_NAME} vs {PLAYER_NAME_2} ({SEASON}):")
        print("-" * 70)
        print(comparison.to_string(index=False))
        
        # Save comparison
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/comparison_{PLAYER_NAME.replace(' ', '_')}_vs_{PLAYER_NAME_2.replace(' ', '_')}.csv"
            comparison.to_csv(csv_path, index=False)
            print(f"\n✓ Saved comparison to {csv_path}")
        
        # Create visualization
        print("\nGenerating comparison chart...")
        avg_cols = [col for col in comparison.columns if col.endswith('_AVG')]
        save_path = f"{OUTPUT_FOLDER}/player_comparison.png" if SAVE_PLOTS else None
        visualizer.plot_comparison_bars(
            comparison, 'Player', avg_cols,
            title=f"{PLAYER_NAME} vs {PLAYER_NAME_2} - Per Game Stats ({SEASON})",
            save_path=save_path
        )
        print(f"  ✓ Created comparison chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
