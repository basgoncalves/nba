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

# Analysis Type: 'player', 'team', 'league_leaders', 'player_comparison', 'league_overview'
ANALYSIS_TYPE = 'league_overview'

# Data Management
DOWNLOAD_LATEST = True                     # True: Download fresh data, False: Use cached CSV files

# Player Settings (for 'player' and 'player_comparison' analysis)
PLAYER_NAME = 'LeBron James'              # Full player name
PLAYER_NAME_2 = 'Stephen Curry'           # Second player for comparison
SEASONS = ['2023-24']                      # List of seasons: ['2023-24'] or ['2022-23', '2023-24']

# Team Settings (for 'team' analysis)
TEAM_NAME = 'LAL'                          # Team abbreviation or full name

# League Leaders Settings (for 'league_leaders' analysis)
STAT_CATEGORY = 'PTS'                      # PTS, AST, REB, STL, BLK, etc.
PER_MODE = 'PerGame'                       # 'PerGame', 'Totals', 'Per48'
TOP_N = 10                                 # Number of leaders to show
LEADERS_SEASON = '2023-24'                 # Single season for league leaders

# League Overview Settings (for 'league_overview' analysis)
OVERVIEW_SEASONS_START = 2024              # Start year for league overview (e.g., 2023 for 2023-24)
OVERVIEW_SEASONS_END = 2026                # End year (e.g., 2023 for single season, 2024 for 2023-24 and 2024-25)
OVERVIEW_STATS = ['PTS', 'AST', 'REB', 'FG3_PCT']     # Y-axis stats (list: PTS, AST, REB, etc.)
MIN_GAMES_PLAYED = 20                      # Minimum games played to include player
OVERVIEW_COLOR_MODE = 'team'               # 'team' for team colors, 'rating' for rating-based gradient

# Statistics to Visualize
STATS_TO_PLOT = ['PTS', 'AST', 'REB']     # Stats for line charts
COMPARISON_STATS = ['PTS', 'AST', 'REB', 'STL', 'BLK']  # Stats for comparison

# Visualization Settings
SHOW_PLOTS = True                          # Display plots in window (also auto-opens HTML files)
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
    
    elif ANALYSIS_TYPE == 'league_overview':
        analyze_league_overview(fetcher, processor, visualizer)
    
    else:
        print(f"Unknown analysis type: {ANALYSIS_TYPE}")
        print("Valid types: 'player', 'team', 'league_leaders', 'player_comparison', 'league_overview'")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)


def analyze_player(fetcher, processor, visualizer):
    """Analyze individual player statistics"""
    all_data = []
    
    for season in SEASONS:
        print(f"\nProcessing {PLAYER_NAME} ({season})...")
        
        # Generate filename for cached data
        csv_filename = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{season}_raw.csv"
        
        try:
            if DOWNLOAD_LATEST:
                # Download fresh data
                print(f"  Downloading data from NBA API...")
                df = fetcher.get_player_season_stats(PLAYER_NAME, season)
                print(f"  ✓ Retrieved {len(df)} games")
                
                # Save to CSV for future use
                import os
                os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                df.to_csv(csv_filename, index=False)
                print(f"  ✓ Cached to {csv_filename}")
            else:
                # Load from cached CSV
                print(f"  Loading from cached file: {csv_filename}")
                df = pd.read_csv(csv_filename)
                print(f"  ✓ Loaded {len(df)} games from cache")
            
            df['SEASON'] = season
            all_data.append(df)
            
        except FileNotFoundError:
            print(f"  ✗ Cache file not found. Set DOWNLOAD_LATEST=True to download data.")
            continue
        except Exception as e:
            print(f"  ✗ Error processing {season}: {e}")
            continue
    
    if not all_data:
        print("\n✗ No data available. Check your settings or set DOWNLOAD_LATEST=True.")
        return
    
    # Combine all seasons
    df = pd.concat(all_data, ignore_index=True)
    print(f"\n✓ Combined {len(df)} games across {len(SEASONS)} season(s)")
    
    try:
        
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
        seasons_str = ', '.join(SEASONS)
        print(f"\n{PLAYER_NAME} - {seasons_str} Summary:")
        print("-" * 70)
        summary = processor.get_summary_stats(df, STATS_TO_PLOT)
        print(summary)
        
        # Save processed data to CSV
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{'_'.join(SEASONS)}_processed.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n✓ Saved processed data to {csv_path}")
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        # Add game numbers and prepare data
        df = df.sort_values('GAME_DATE') if 'GAME_DATE' in df.columns else df
        df['GAME_NUM'] = list(range(1, len(df) + 1))
        
        # Line chart for each stat over time
        for stat in STATS_TO_PLOT:
            if stat in df.columns:
                save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{stat}_{'_'.join(SEASONS)}.png" if SAVE_PLOTS else None
                
                if len(SEASONS) > 1:
                    # Multi-season visualization with season markers
                    visualizer.plot_multi_season_line(
                        df, 'GAME_NUM', stat, 'SEASON',
                        title=f"{PLAYER_NAME} - {stat} per Game",
                        xlabel='Game Number',
                        ylabel=stat,
                        save_path=save_path
                    )
                else:
                    # Single season visualization
                    visualizer.plot_line_chart(
                        df, 'GAME_NUM', stat,
                        title=f"{PLAYER_NAME} - {stat} per Game ({SEASONS[0]})",
                        xlabel='Game Number',
                        ylabel=stat,
                        save_path=save_path
                    )
                print(f"  ✓ Created {stat} line chart")
        
        # Multiple stats on one chart
        if len(STATS_TO_PLOT) > 1:
            save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_multi_stats_{'_'.join(SEASONS)}.png" if SAVE_PLOTS else None
            visualizer.plot_multiple_lines(
                df, 'GAME_NUM', STATS_TO_PLOT,
                title=f"{PLAYER_NAME} - Season Performance ({seasons_str})",
                xlabel='Game Number',
                ylabel='Value',
                save_path=save_path
            )
            print(f"  ✓ Created multi-stat comparison chart")
        
        # Distribution plot for points
        if 'PTS' in df.columns:
            save_path = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_PTS_distribution_{'_'.join(SEASONS)}.png" if SAVE_PLOTS else None
            visualizer.plot_distribution(
                df, 'PTS',
                title=f"{PLAYER_NAME} - Points Distribution ({seasons_str})",
                save_path=save_path
            )
            print(f"  ✓ Created points distribution chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def analyze_team(fetcher, processor, visualizer):
    """Analyze team statistics"""
    all_data = []
    
    for season in SEASONS:
        print(f"\nProcessing {TEAM_NAME} ({season})...")
        
        # Generate filename for cached data
        csv_filename = f"{OUTPUT_FOLDER}/{TEAM_NAME}_{season}_raw.csv"
        
        try:
            if DOWNLOAD_LATEST:
                # Download fresh data
                print(f"  Downloading data from NBA API...")
                df = fetcher.get_team_season_stats(TEAM_NAME, season)
                print(f"  ✓ Retrieved {len(df)} games")
                
                # Save to CSV
                import os
                os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                df.to_csv(csv_filename, index=False)
                print(f"  ✓ Cached to {csv_filename}")
            else:
                # Load from cached CSV
                print(f"  Loading from cached file: {csv_filename}")
                df = pd.read_csv(csv_filename)
                print(f"  ✓ Loaded {len(df)} games from cache")
            
            df['SEASON'] = season
            all_data.append(df)
            
        except FileNotFoundError:
            print(f"  ✗ Cache file not found. Set DOWNLOAD_LATEST=True to download data.")
            continue
        except Exception as e:
            print(f"  ✗ Error processing {season}: {e}")
            continue
    
    if not all_data:
        print("\n✗ No data available. Check your settings or set DOWNLOAD_LATEST=True.")
        return
    
    # Combine all seasons
    df = pd.concat(all_data, ignore_index=True)
    print(f"\n✓ Combined {len(df)} games across {len(SEASONS)} season(s)")
    
    try:
        
        # Calculate shooting percentages
        df = processor.calculate_shooting_percentages(df)
        
        # Display summary
        seasons_str = ', '.join(SEASONS)
        print(f"\n{TEAM_NAME} - {seasons_str} Summary:")
        print("-" * 70)
        summary = processor.get_summary_stats(df, STATS_TO_PLOT)
        print(summary)
        
        # Calculate win percentage
        if 'WL' in df.columns:
            wins = (df['WL'] == 'W').sum()
            total_games = len(df)
            win_pct = (wins / total_games * 100).round(1)
            print(f"\nOverall Record: {wins}-{total_games - wins} ({win_pct}% Win Rate)")
        
        # Save data
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/{TEAM_NAME}_{'_'.join(SEASONS)}_processed.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n✓ Saved processed data to {csv_path}")
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        df = df.sort_values('GAME_DATE') if 'GAME_DATE' in df.columns else df
        df['GAME_NUM'] = list(range(1, len(df) + 1))
        
        save_path = f"{OUTPUT_FOLDER}/{TEAM_NAME}_performance_{'_'.join(SEASONS)}.png" if SAVE_PLOTS else None
        visualizer.plot_multiple_lines(
            df, 'GAME_NUM', STATS_TO_PLOT,
            title=f"{TEAM_NAME} - Season Performance ({seasons_str})",
            xlabel='Game Number',
            ylabel='Value',
            save_path=save_path
        )
        print(f"  ✓ Created performance chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def analyze_league_leaders(fetcher, processor, visualizer):
    """Analyze league leaders"""
    season = LEADERS_SEASON
    print(f"\nProcessing {STAT_CATEGORY} leaders for {season}...")
    
    # Generate filename for cached data
    csv_filename = f"{OUTPUT_FOLDER}/leaders_{STAT_CATEGORY}_{season}_{PER_MODE}_raw.csv"
    
    try:
        if DOWNLOAD_LATEST:
            # Download fresh data
            print(f"  Downloading data from NBA API...")
            df = fetcher.get_league_leaders(season, STAT_CATEGORY, PER_MODE)
            print(f"  ✓ Retrieved league leaders")
            
            # Save to CSV
            import os
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            df.to_csv(csv_filename, index=False)
            print(f"  ✓ Cached to {csv_filename}")
        else:
            # Load from cached CSV
            print(f"  Loading from cached file: {csv_filename}")
            df = pd.read_csv(csv_filename)
            print(f"  ✓ Loaded league leaders from cache")
        
        df_top = df.head(TOP_N)
        
        # Display leaders
        print(f"\nTop {TOP_N} in {STAT_CATEGORY} ({season}):")
        print("-" * 70)
        display_cols = ['PLAYER', 'TEAM', STAT_CATEGORY]
        print(df_top[display_cols].to_string(index=False))
        
        # Save data
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/league_leaders_{STAT_CATEGORY}_{season}_top{TOP_N}.csv"
            df_top.to_csv(csv_path, index=False)
            print(f"\n✓ Saved data to {csv_path}")
        
        # Create visualization
        print("\nGenerating visualization...")
        save_path = f"{OUTPUT_FOLDER}/league_leaders_{STAT_CATEGORY}_{season}.png" if SAVE_PLOTS else None
        visualizer.plot_bar_chart(
            df_top, 'PLAYER', STAT_CATEGORY,
            title=f"Top {TOP_N} in {STAT_CATEGORY} ({season})",
            save_path=save_path,
            horizontal=True
        )
        print(f"  ✓ Created leaders bar chart")
        
    except FileNotFoundError:
        print(f"✗ Cache file not found. Set DOWNLOAD_LATEST=True to download data.")
    except Exception as e:
        print(f"✗ Error: {e}")


def compare_players(fetcher, processor, visualizer):
    """Compare two players"""
    all_data_p1 = []
    all_data_p2 = []
    
    for season in SEASONS:
        print(f"\nProcessing {season}...")
        
        # Player 1
        csv_filename_p1 = f"{OUTPUT_FOLDER}/{PLAYER_NAME.replace(' ', '_')}_{season}_raw.csv"
        try:
            if DOWNLOAD_LATEST:
                print(f"  Downloading {PLAYER_NAME} data...")
                df1 = fetcher.get_player_season_stats(PLAYER_NAME, season)
                import os
                os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                df1.to_csv(csv_filename_p1, index=False)
                print(f"  ✓ Cached {PLAYER_NAME} data")
            else:
                df1 = pd.read_csv(csv_filename_p1)
                print(f"  ✓ Loaded {PLAYER_NAME} from cache")
            df1['SEASON'] = season
            all_data_p1.append(df1)
        except Exception as e:
            print(f"  ✗ Error with {PLAYER_NAME}: {e}")
        
        # Player 2
        csv_filename_p2 = f"{OUTPUT_FOLDER}/{PLAYER_NAME_2.replace(' ', '_')}_{season}_raw.csv"
        try:
            if DOWNLOAD_LATEST:
                print(f"  Downloading {PLAYER_NAME_2} data...")
                df2 = fetcher.get_player_season_stats(PLAYER_NAME_2, season)
                df2.to_csv(csv_filename_p2, index=False)
                print(f"  ✓ Cached {PLAYER_NAME_2} data")
            else:
                df2 = pd.read_csv(csv_filename_p2)
                print(f"  ✓ Loaded {PLAYER_NAME_2} from cache")
            df2['SEASON'] = season
            all_data_p2.append(df2)
        except Exception as e:
            print(f"  ✗ Error with {PLAYER_NAME_2}: {e}")
    
    if not all_data_p1 or not all_data_p2:
        print("\n✗ Insufficient data for comparison. Check settings or set DOWNLOAD_LATEST=True.")
        return
    
    # Combine all seasons
    df1 = pd.concat(all_data_p1, ignore_index=True)
    df2 = pd.concat(all_data_p2, ignore_index=True)
    print(f"\n✓ Combined data across {len(SEASONS)} season(s)")
    
    try:
        
        # Compare statistics
        comparison = processor.compare_players(
            [df1, df2],
            [PLAYER_NAME, PLAYER_NAME_2],
            COMPARISON_STATS
        )
        
        # Display comparison
        seasons_str = ', '.join(SEASONS)
        print(f"\n{PLAYER_NAME} vs {PLAYER_NAME_2} ({seasons_str}):")
        print("-" * 70)
        print(comparison.to_string(index=False))
        
        # Save comparison
        if SAVE_PLOTS:
            csv_path = f"{OUTPUT_FOLDER}/comparison_{PLAYER_NAME.replace(' ', '_')}_vs_{PLAYER_NAME_2.replace(' ', '_')}_{'_'.join(SEASONS)}.csv"
            comparison.to_csv(csv_path, index=False)
            print(f"\n✓ Saved comparison to {csv_path}")
        
        # Create visualization
        print("\nGenerating comparison chart...")
        avg_cols = [col for col in comparison.columns if col.endswith('_AVG')]
        save_path = f"{OUTPUT_FOLDER}/player_comparison_{'_'.join(SEASONS)}.png" if SAVE_PLOTS else None
        visualizer.plot_comparison_bars(
            comparison, 'Player', avg_cols,
            title=f"{PLAYER_NAME} vs {PLAYER_NAME_2} - Per Game Stats ({seasons_str})",
            save_path=save_path
        )
        print(f"  ✓ Created comparison chart")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def analyze_league_overview(fetcher, processor, visualizer):
    """Analyze league-wide player statistics with interactive bubble plot"""
    import os
    
    # Generate list of seasons from start to end year
    seasons = []
    for year in range(OVERVIEW_SEASONS_START, OVERVIEW_SEASONS_END + 1):
        seasons.append(f"{year}-{str(year + 1)[-2:]}")
    
    print(f"\nProcessing league overview for {len(seasons)} season(s): {', '.join(seasons)}")
    print(f"Stats to visualize: {', '.join(OVERVIEW_STATS)}")
    
    # Process each season
    for season in seasons:
        print(f"\n{'='*70}")
        print(f"Season: {season}")
        print(f"{'='*70}")
        
        # Generate filename for cached data
        csv_filename = f"{OUTPUT_FOLDER}/league_overview_{season}_raw.csv"
        
        try:
            if DOWNLOAD_LATEST:
                # Download fresh data - get top 300 players to capture most of the league
                print(f"  Downloading league data from NBA API...")
                df = fetcher.get_league_leaders(season, 'PTS', 'PerGame')
                print(f"  ✓ Retrieved {len(df)} players")
                
                # Save to CSV
                os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                df.to_csv(csv_filename, index=False)
                print(f"  ✓ Cached to {csv_filename}")
            else:
                # Load from cached CSV
                print(f"  Loading from cached file: {csv_filename}")
                df = pd.read_csv(csv_filename)
                print(f"  ✓ Loaded {len(df)} players from cache")
            
            # Filter by minimum games played
            if 'GP' in df.columns:
                df = df[df['GP'] >= MIN_GAMES_PLAYED]
                print(f"  ✓ Filtered to {len(df)} players with {MIN_GAMES_PLAYED}+ games")
            
            # Calculate player rating (simple formula based on common stats)
            if all(col in df.columns for col in ['PTS', 'AST', 'REB', 'STL', 'BLK', 'TOV']):
                df['PLAYER_RATING'] = (
                    df['PTS'] + 
                    df['AST'] * 1.5 + 
                    df['REB'] * 1.2 + 
                    df['STL'] * 2 + 
                    df['BLK'] * 2 - 
                    df['TOV'] * 1.5
                ).round(1)
            else:
                # Fallback to simpler rating
                df['PLAYER_RATING'] = df['PTS'] if 'PTS' in df.columns else 0
            
            # Calculate rating rank (1 = highest rating)
            df['RATING_RANK'] = df['PLAYER_RATING'].rank(ascending=False, method='min').astype(int)
            
            # Display summary
            print(f"\n  League Summary - {season}:")
            print("  " + "-" * 66)
            print(f"  Total players: {len(df)}")
            print(f"  Avg MIN: {df['MIN'].mean():.1f}" if 'MIN' in df.columns else "")
            print(f"  Avg Player Rating: {df['PLAYER_RATING'].mean():.1f}")
            for stat in OVERVIEW_STATS:
                if stat in df.columns:
                    print(f"  Avg {stat}: {df[stat].mean():.1f}")
            
            # Save data
            if SAVE_PLOTS:
                csv_path = f"{OUTPUT_FOLDER}/league_overview_{season}_processed.csv"
                df.to_csv(csv_path, index=False)
                print(f"\n  ✓ Saved data to {csv_path}")
            
            # Create single interactive bubble plot with multiple stats as subplots
            print(f"\n  Generating interactive bubble plot with {len(OVERVIEW_STATS)} stat(s)...")
            
            # Filter valid stats
            valid_stats = [stat for stat in OVERVIEW_STATS if stat in df.columns]
            if not valid_stats:
                print(f"  ✗ No valid stats found in data")
                continue
            
            save_path = f"{OUTPUT_FOLDER}/league_overview_{season}_bubble.html" if SAVE_PLOTS else None
            
            visualizer.plot_multi_stat_subplots(
                df,
                x_column='MIN',
                stats_list=valid_stats,
                size_column='PLAYER_RATING',
                label_column='PLAYER',
                title=f"NBA League Overview - {season}",
                xlabel='Minutes Per Game',
                save_path=save_path,
                team_column='TEAM',
                rank_column='RATING_RANK',
                color_mode=OVERVIEW_COLOR_MODE
            )
            
            print(f"  ✓ Created multi-stat bubble plot with {len(valid_stats)} stat(s)")
            if save_path:
                print(f"    -> {save_path}")
            
        except FileNotFoundError:
            print(f"  ✗ Cache file not found. Set DOWNLOAD_LATEST=True to download data.")
            continue
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*70}")
    print(f"Completed {len(seasons)} season(s)")
    print(f"Total visualizations created: {len(seasons)}")
    print(f"{'='*70}")
    
    # Open generated HTML files in browser
    if SAVE_PLOTS and SHOW_PLOTS:
        import webbrowser
        import time
        
        print(f"\nOpening visualizations in browser...")
        html_files = []
        
        for season in seasons:
            html_path = f"{OUTPUT_FOLDER}/league_overview_{season}_bubble.html"
            if os.path.exists(html_path):
                html_files.append(html_path)
        
        if html_files:
            print(f"  Opening {len(html_files)} HTML file(s)...")
            for i, html_file in enumerate(html_files):
                # Convert to absolute path and proper file URL
                abs_path = os.path.abspath(html_file)
                file_url = 'file:///' + abs_path.replace('\\', '/')
                webbrowser.open(file_url)
                print(f"  ✓ Opened: {os.path.basename(html_file)}")
                # Small delay to avoid overwhelming the browser
                if i < len(html_files) - 1:
                    time.sleep(0.3)
            print(f"\n  💡 Tip: Use the 'Select Stats' dropdown to toggle between stats")
            print(f"  💡 Use 'Show All' to see all stats as subplots simultaneously")
        else:
            print(f"  ⚠ No HTML files found to open")
    elif SAVE_PLOTS and not SHOW_PLOTS:
        print(f"\n  💡 HTML files saved but not opened (SHOW_PLOTS=False)")
        print(f"  💡 To auto-open files in browser, set SHOW_PLOTS=True")


if __name__ == "__main__":
    main()
