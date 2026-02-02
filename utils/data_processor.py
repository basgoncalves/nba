"""Module for processing and analyzing NBA data"""
import pandas as pd
import numpy as np


class NBADataProcessor:
    """Process and analyze NBA statistics data"""
    
    @staticmethod
    def calculate_averages(df, columns):
        """
        Calculate averages for specified columns
        
        Args:
            df (pd.DataFrame): Input dataframe
            columns (list): List of column names to average
            
        Returns:
            dict: Dictionary of column name to average value
        """
        return {col: df[col].mean() for col in columns if col in df.columns}
    
    @staticmethod
    def calculate_totals(df, columns):
        """
        Calculate totals for specified columns
        
        Args:
            df (pd.DataFrame): Input dataframe
            columns (list): List of column names to sum
            
        Returns:
            dict: Dictionary of column name to total value
        """
        return {col: df[col].sum() for col in columns if col in df.columns}
    
    @staticmethod
    def filter_by_date_range(df, start_date=None, end_date=None, date_column='GAME_DATE'):
        """
        Filter dataframe by date range
        
        Args:
            df (pd.DataFrame): Input dataframe
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            date_column (str): Name of the date column
            
        Returns:
            pd.DataFrame: Filtered dataframe
        """
        if date_column not in df.columns:
            return df
        
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        if start_date:
            df = df[df[date_column] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[date_column] <= pd.to_datetime(end_date)]
        
        return df
    
    @staticmethod
    def calculate_shooting_percentages(df):
        """
        Calculate shooting percentages from game data
        
        Args:
            df (pd.DataFrame): Input dataframe with FGM, FGA, FG3M, FG3A, FTM, FTA
            
        Returns:
            pd.DataFrame: Dataframe with added percentage columns
        """
        df = df.copy()
        
        if 'FGM' in df.columns and 'FGA' in df.columns:
            df['FG_PCT'] = (df['FGM'] / df['FGA'] * 100).round(1)
        
        if 'FG3M' in df.columns and 'FG3A' in df.columns:
            df['FG3_PCT'] = (df['FG3M'] / df['FG3A'] * 100).round(1)
        
        if 'FTM' in df.columns and 'FTA' in df.columns:
            df['FT_PCT'] = (df['FTM'] / df['FTA'] * 100).round(1)
        
        return df
    
    @staticmethod
    def get_top_n_performances(df, column, n=10, ascending=False):
        """
        Get top N performances by a specific stat
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column to sort by
            n (int): Number of top performances to return
            ascending (bool): Sort in ascending order if True
            
        Returns:
            pd.DataFrame: Top N performances
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")
        
        return df.nlargest(n, column) if not ascending else df.nsmallest(n, column)
    
    @staticmethod
    def calculate_rolling_average(df, column, window=5):
        """
        Calculate rolling average for a column
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column to calculate rolling average for
            window (int): Rolling window size
            
        Returns:
            pd.DataFrame: Dataframe with added rolling average column
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")
        
        df = df.copy()
        df[f'{column}_ROLLING_AVG'] = df[column].rolling(window=window).mean()
        return df
    
    @staticmethod
    def calculate_advanced_stats(df):
        """
        Calculate advanced statistics like True Shooting %, Game Score, etc.
        
        Args:
            df (pd.DataFrame): Input dataframe with basic stats
            
        Returns:
            pd.DataFrame: Dataframe with added advanced stats
        """
        df = df.copy()
        
        # True Shooting Percentage
        if all(col in df.columns for col in ['PTS', 'FGA', 'FTA']):
            df['TS_PCT'] = (df['PTS'] / (2 * (df['FGA'] + 0.44 * df['FTA'])) * 100).round(1)
        
        # Effective Field Goal Percentage
        if all(col in df.columns for col in ['FGM', 'FG3M', 'FGA']):
            df['EFG_PCT'] = ((df['FGM'] + 0.5 * df['FG3M']) / df['FGA'] * 100).round(1)
        
        # Game Score (John Hollinger's formula)
        if all(col in df.columns for col in ['PTS', 'FGM', 'FGA', 'FTM', 'FTA', 
                                               'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']):
            df['GAME_SCORE'] = (df['PTS'] + 0.4 * df['FGM'] - 0.7 * df['FGA'] - 
                               0.4 * (df['FTA'] - df['FTM']) + 0.7 * df['REB'] + 
                               0.7 * df['AST'] + df['STL'] + 0.7 * df['BLK'] - 
                               0.7 * df['PF'] - df['TOV']).round(1)
        
        return df
    
    @staticmethod
    def compare_players(df_list, player_names, stat_columns):
        """
        Compare statistics for multiple players
        
        Args:
            df_list (list): List of dataframes for each player
            player_names (list): List of player names
            stat_columns (list): List of stat columns to compare
            
        Returns:
            pd.DataFrame: Comparison dataframe
        """
        comparison = pd.DataFrame()
        comparison['Player'] = player_names
        
        for i, df in enumerate(df_list):
            for col in stat_columns:
                if col in df.columns:
                    comparison.loc[i, f'{col}_AVG'] = df[col].mean().round(1)
                    comparison.loc[i, f'{col}_TOTAL'] = df[col].sum().round(1)
        
        return comparison
    
    @staticmethod
    def get_summary_stats(df, columns):
        """
        Get summary statistics (mean, median, std, min, max) for columns
        
        Args:
            df (pd.DataFrame): Input dataframe
            columns (list): List of columns to summarize
            
        Returns:
            pd.DataFrame: Summary statistics dataframe
        """
        summary = pd.DataFrame()
        
        for col in columns:
            if col in df.columns:
                summary[col] = {
                    'Mean': df[col].mean().round(2),
                    'Median': df[col].median().round(2),
                    'Std Dev': df[col].std().round(2),
                    'Min': df[col].min(),
                    'Max': df[col].max()
                }
        
        return summary.T
