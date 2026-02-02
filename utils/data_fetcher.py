"""Module for fetching NBA data from various sources"""
from nba_api.stats.endpoints import (
    playercareerstats, 
    playergamelog,
    leaguegamefinder,
    teamgamelog,
    commonplayerinfo,
    commonteamroster,
    leagueleaders,
    teamestimatedmetrics,
    leaguestandingsv3
)
from nba_api.stats.static import players, teams
import pandas as pd


class NBADataFetcher:
    """Fetch NBA statistics from the NBA API"""
    
    def __init__(self):
        """Initialize the data fetcher"""
        self.all_players = players.get_players()
        self.all_teams = teams.get_teams()
    
    def get_player_id(self, player_name):
        """
        Get player ID from player name
        
        Args:
            player_name (str): Full name of the player
            
        Returns:
            int: Player ID or None if not found
        """
        player = [p for p in self.all_players if p['full_name'].lower() == player_name.lower()]
        if player:
            return player[0]['id']
        return None
    
    def get_team_id(self, team_name):
        """
        Get team ID from team name (full name or abbreviation)
        
        Args:
            team_name (str): Team name or abbreviation
            
        Returns:
            int: Team ID or None if not found
        """
        team = [t for t in self.all_teams 
                if t['full_name'].lower() == team_name.lower() 
                or t['abbreviation'].lower() == team_name.lower()]
        if team:
            return team[0]['id']
        return None
    
    def get_player_career_stats(self, player_name):
        """
        Get career statistics for a player
        
        Args:
            player_name (str): Full name of the player
            
        Returns:
            pd.DataFrame: Career statistics dataframe
        """
        player_id = self.get_player_id(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found")
        
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        return career.get_data_frames()[0]
    
    def get_player_season_stats(self, player_name, season='2023-24'):
        """
        Get season game log for a player
        
        Args:
            player_name (str): Full name of the player
            season (str): Season in format 'YYYY-YY' (e.g., '2023-24')
            
        Returns:
            pd.DataFrame: Season game log dataframe
        """
        player_id = self.get_player_id(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found")
        
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        return gamelog.get_data_frames()[0]
    
    def get_team_season_stats(self, team_name, season='2023-24'):
        """
        Get season game log for a team
        
        Args:
            team_name (str): Team name or abbreviation
            season (str): Season in format 'YYYY-YY' (e.g., '2023-24')
            
        Returns:
            pd.DataFrame: Team game log dataframe
        """
        team_id = self.get_team_id(team_name)
        if not team_id:
            raise ValueError(f"Team '{team_name}' not found")
        
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        return gamelog.get_data_frames()[0]
    
    def get_league_leaders(self, season='2023-24', stat_category='PTS', per_mode='PerGame'):
        """
        Get league leaders for a specific stat category
        
        Args:
            season (str): Season in format 'YYYY-YY'
            stat_category (str): Stat category (PTS, AST, REB, etc.)
            per_mode (str): 'PerGame', 'Totals', or 'Per48'
            
        Returns:
            pd.DataFrame: League leaders dataframe
        """
        leaders = leagueleaders.LeagueLeaders(
            season=season,
            stat_category_abbreviation=stat_category,
            per_mode48=per_mode
        )
        return leaders.get_data_frames()[0]
    
    def get_player_info(self, player_name):
        """
        Get detailed player information
        
        Args:
            player_name (str): Full name of the player
            
        Returns:
            pd.DataFrame: Player information dataframe
        """
        player_id = self.get_player_id(player_name)
        if not player_id:
            raise ValueError(f"Player '{player_name}' not found")
        
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        return info.get_data_frames()[0]
    
    def search_players(self, search_term):
        """
        Search for players by name
        
        Args:
            search_term (str): Search term
            
        Returns:
            list: List of matching player dictionaries
        """
        return [p for p in self.all_players 
                if search_term.lower() in p['full_name'].lower()]
    
    def get_all_teams(self):
        """
        Get list of all NBA teams
        
        Returns:
            list: List of team dictionaries
        """
        return self.all_teams
    
    def get_team_standings(self, season='2023-24'):
        """
        Get team standings for a season
        
        Args:
            season (str): Season in format 'YYYY-YY'
            
        Returns:
            pd.DataFrame: Team standings with rankings
        """
        try:
            standings = leaguestandingsv3.LeagueStandingsV3(
                league_id='00',
                season=season,
                season_type='Regular Season'
            )
            df = standings.get_data_frames()[0]
            
            # Add overall league rank based on win percentage
            if 'WinPCT' in df.columns:
                df['LEAGUE_RANK'] = df['WinPCT'].rank(ascending=False, method='min').astype(int)
            elif 'W' in df.columns and 'L' in df.columns:
                df['WinPCT'] = df['W'] / (df['W'] + df['L'])
                df['LEAGUE_RANK'] = df['WinPCT'].rank(ascending=False, method='min').astype(int)
            
            # Create mapping dictionary with team abbreviation
            if 'TeamCity' in df.columns and 'TeamName' in df.columns:
                # Create full team names for matching
                df['FULL_NAME'] = df['TeamCity'] + ' ' + df['TeamName']
            
            return df
        except Exception as e:
            print(f"Warning: Could not fetch team standings: {e}")
            return pd.DataFrame()
