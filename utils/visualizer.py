"""Module for visualizing NBA statistics"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import json
import os

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class NBAVisualizer:
    """Create visualizations for NBA statistics"""
    
    def __init__(self, style='darkgrid', palette='husl'):
        """
        Initialize visualizer with style settings
        
        Args:
            style (str): Seaborn style ('darkgrid', 'whitegrid', 'dark', 'white', 'ticks')
            palette (str): Color palette
        """
        sns.set_style(style)
        sns.set_palette(palette)
        self.figure_size = (12, 6)
        self.team_colors = self._load_team_colors()
    
    def _load_team_colors(self):
        """Load NBA team colors from JSON file"""
        colors_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nba_team_colors.json')
        try:
            with open(colors_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Team colors file not found at {colors_file}")
            return {}
    
    def plot_line_chart(self, df, x_column, y_column, title=None, xlabel=None, ylabel=None, 
                        figsize=None, save_path=None):
        """
        Create a line chart
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis
            y_column (str): Column for y-axis
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure (if None, displays plot)
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        plt.plot(df[x_column], df[y_column], marker='o', linewidth=2, markersize=6)
        plt.title(title or f'{y_column} over {x_column}', fontsize=14, fontweight='bold')
        plt.xlabel(xlabel or x_column, fontsize=12)
        plt.ylabel(ylabel or y_column, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_multi_season_line(self, df, x_column, y_column, season_column, 
                                title=None, xlabel=None, ylabel=None, 
                                figsize=None, save_path=None):
        """
        Create a line chart with multiple seasons shown with different colors
        
        Args:
            df (pd.DataFrame): Input dataframe with season column
            x_column (str): Column for x-axis (e.g., game number)
            y_column (str): Column for y-axis (stat to plot)
            season_column (str): Column containing season labels
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        # Plot each season separately
        seasons = df[season_column].unique()
        for season in seasons:
            season_df = df[df[season_column] == season]
            # Reset game numbers for each season to start from 1
            season_df = season_df.copy()
            season_df['GAME_NUM_RESET'] = range(1, len(season_df) + 1)
            plt.plot(season_df['GAME_NUM_RESET'], season_df[y_column], 
                    marker='o', linewidth=2, markersize=5, label=season, alpha=0.8)
        
        plt.title(title or f'{y_column} by {season_column}', fontsize=14, fontweight='bold')
        plt.xlabel(xlabel or 'Game Number (per season)', fontsize=12)
        plt.ylabel(ylabel or y_column, fontsize=12)
        plt.legend(title='Season')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_bar_chart(self, df, x_column, y_column, title=None, xlabel=None, ylabel=None,
                       figsize=None, save_path=None, horizontal=False):
        """
        Create a bar chart
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis (categories)
            y_column (str): Column for y-axis (values)
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
            horizontal (bool): Create horizontal bar chart
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        if horizontal:
            plt.barh(df[x_column], df[y_column])
            plt.xlabel(ylabel or y_column, fontsize=12)
            plt.ylabel(xlabel or x_column, fontsize=12)
        else:
            plt.bar(df[x_column], df[y_column])
            plt.xlabel(xlabel or x_column, fontsize=12)
            plt.ylabel(ylabel or y_column, fontsize=12)
            plt.xticks(rotation=45, ha='right')
        
        plt.title(title or f'{y_column} by {x_column}', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_scatter(self, df, x_column, y_column, title=None, xlabel=None, ylabel=None,
                     figsize=None, save_path=None, color_column=None):
        """
        Create a scatter plot
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis
            y_column (str): Column for y-axis
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
            color_column (str): Column to use for color coding
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        if color_column and color_column in df.columns:
            scatter = plt.scatter(df[x_column], df[y_column], 
                                 c=df[color_column], cmap='viridis', 
                                 s=100, alpha=0.6, edgecolors='black')
            plt.colorbar(scatter, label=color_column)
        else:
            plt.scatter(df[x_column], df[y_column], s=100, alpha=0.6, edgecolors='black')
        
        plt.title(title or f'{y_column} vs {x_column}', fontsize=14, fontweight='bold')
        plt.xlabel(xlabel or x_column, fontsize=12)
        plt.ylabel(ylabel or y_column, fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_heatmap(self, df, title=None, figsize=None, save_path=None, annot=True):
        """
        Create a heatmap (correlation matrix or any 2D data)
        
        Args:
            df (pd.DataFrame): Input dataframe
            title (str): Chart title
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
            annot (bool): Annotate cells with values
        """
        figsize = figsize or (10, 8)
        plt.figure(figsize=figsize)
        
        sns.heatmap(df, annot=annot, fmt='.2f', cmap='coolwarm', 
                   center=0, linewidths=0.5, cbar_kws={'label': 'Value'})
        
        plt.title(title or 'Heatmap', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_multiple_lines(self, df, x_column, y_columns, title=None, xlabel=None, 
                           ylabel=None, figsize=None, save_path=None, labels=None):
        """
        Plot multiple lines on the same chart
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis
            y_columns (list): List of columns for y-axis
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
            labels (list): Custom labels for each line
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        for i, col in enumerate(y_columns):
            if col in df.columns:
                label = labels[i] if labels and i < len(labels) else col
                plt.plot(df[x_column], df[col], marker='o', linewidth=2, 
                        markersize=6, label=label)
        
        plt.title(title or 'Multiple Stats Comparison', fontsize=14, fontweight='bold')
        plt.xlabel(xlabel or x_column, fontsize=12)
        plt.ylabel(ylabel or 'Value', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_comparison_bars(self, df, categories_column, value_columns, 
                            title=None, figsize=None, save_path=None):
        """
        Create grouped bar chart for comparing multiple metrics
        
        Args:
            df (pd.DataFrame): Input dataframe
            categories_column (str): Column with category names
            value_columns (list): List of columns to compare
            title (str): Chart title
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
        """
        figsize = figsize or (14, 6)
        
        df_plot = df.set_index(categories_column)[value_columns]
        ax = df_plot.plot(kind='bar', figsize=figsize, width=0.8)
        
        plt.title(title or 'Statistics Comparison', fontsize=14, fontweight='bold')
        plt.xlabel(categories_column, fontsize=12)
        plt.ylabel('Value', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Stats', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_distribution(self, df, column, title=None, xlabel=None, 
                         figsize=None, save_path=None, bins=30):
        """
        Plot distribution histogram with KDE
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column to plot distribution for
            title (str): Chart title
            xlabel (str): X-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
            bins (int): Number of histogram bins
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        sns.histplot(df[column], bins=bins, kde=True, color='skyblue', edgecolor='black')
        
        plt.title(title or f'Distribution of {column}', fontsize=14, fontweight='bold')
        plt.xlabel(xlabel or column, fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_box_plot(self, df, columns, title=None, ylabel=None, 
                      figsize=None, save_path=None):
        """
        Create box plots for multiple columns
        
        Args:
            df (pd.DataFrame): Input dataframe
            columns (list): List of columns to plot
            title (str): Chart title
            ylabel (str): Y-axis label
            figsize (tuple): Figure size (width, height)
            save_path (str): Path to save figure
        """
        figsize = figsize or self.figure_size
        plt.figure(figsize=figsize)
        
        df_plot = df[columns]
        df_plot.boxplot()
        
        plt.title(title or 'Statistics Distribution', fontsize=14, fontweight='bold')
        plt.ylabel(ylabel or 'Value', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_interactive_bubble(self, df, x_column, y_column, size_column, 
                                label_column, title=None, xlabel=None, ylabel=None,
                                save_path=None, color_column=None, team_column='TEAM',
                                rank_column=None):
        """
        Create an interactive bubble plot using Plotly with team filtering
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis (e.g., minutes played)
            y_column (str): Column for y-axis (e.g., points)
            size_column (str): Column for bubble size (e.g., player rating)
            label_column (str): Column for labels (e.g., player names)
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            save_path (str): Path to save HTML file
            color_column (str): Optional column for color coding
            team_column (str): Column containing team names for filtering
            rank_column (str): Column containing rank values to display with size_column
        """
        if not PLOTLY_AVAILABLE:
            print("Warning: Plotly not installed. Install with: pip install plotly")
            print("Falling back to static scatter plot...")
            self.plot_scatter(df, x_column, y_column, title, xlabel, ylabel, 
                            save_path=save_path.replace('.html', '.png') if save_path else None)
            return
        
        # Check if team column exists
        if team_column not in df.columns:
            team_column = None
        
        # Check if rank column exists
        if rank_column and rank_column not in df.columns:
            rank_column = None
        
        # Prepare hover data
        hover_data = {
            label_column: True,
            x_column: ':.1f',
            y_column: ':.1f',
            size_column: ':.1f'
        }
        
        # Add team to hover data if available
        if team_column:
            hover_data[team_column] = True
        
        # Add rank to hover data if available
        if rank_column:
            hover_data[rank_column] = True
        
        # Add color column to hover if specified
        if color_column and color_column in df.columns:
            hover_data[color_column] = ':.1f'
        
        # Prepare custom data for hover template
        custom_data_cols = []
        if team_column:
            custom_data_cols.append(team_column)
        if rank_column:
            custom_data_cols.append(rank_column)
        
        # Create the bubble chart
        fig = px.scatter(
            df,
            x=x_column,
            y=y_column,
            size=size_column,
            color=color_column if color_column else size_column,
            hover_name=label_column,
            hover_data=hover_data,
            title=title or f'{y_column} vs {x_column}',
            labels={
                x_column: xlabel or x_column,
                y_column: ylabel or y_column,
                size_column: size_column.replace('_', ' ').title()
            },
            color_continuous_scale='Viridis',
            size_max=40,
            custom_data=custom_data_cols if custom_data_cols else None
        )
        
        # Update layout for better appearance
        fig.update_layout(
            font=dict(size=12),
            title_font=dict(size=16, family='Arial Black'),
            hovermode='closest',
            plot_bgcolor='rgba(240,240,240,0.9)',
            xaxis=dict(
                showgrid=True,
                gridcolor='white',
                title_font=dict(size=14)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='white',
                title_font=dict(size=14)
            ),
            height=750,
            margin=dict(t=100)  # More space for dropdown
        )
        
        # Add hover template customization
        hover_template = '<b>%{hovertext}</b><br>'
        custom_idx = 0
        if team_column:
            hover_template += f'Team: %{{customdata[{custom_idx}]}}<br>'
            custom_idx += 1
        hover_template += f'{xlabel or x_column}: %{{x:.1f}}<br>'
        hover_template += f'{ylabel or y_column}: %{{y:.1f}}<br>'
        
        # Add rating with rank if available
        if rank_column:
            hover_template += f'{size_column.replace("_", " ").title()}: %{{marker.size:.1f}} (rk %{{customdata[{custom_idx}]}})<br>'
        else:
            hover_template += f'{size_column.replace("_", " ").title()}: %{{marker.size:.1f}}<br>'
        
        hover_template += '<extra></extra>'
        
        fig.update_traces(hovertemplate=hover_template)
        
        # Add team filter dropdown if team column exists
        if team_column:
            teams = sorted(df[team_column].unique())
            
            # Get the original color values for restoration
            # Store color column data for creating gray vs colored distinction
            color_col = color_column if color_column else size_column
            
            # Create buttons for dropdown menu
            buttons = [
                dict(
                    label="All Teams",
                    method="update",
                    args=[{
                        "marker.color": [df[color_col].tolist()],
                        "marker.line.width": [0] * len(df),
                        "marker.line.color": [''] * len(df),
                        "marker.coloraxis": "coloraxis"
                    }]
                )
            ]
            
            # Add button for each team
            for team in teams:
                # For selected team: keep original color scale
                # For non-selected teams: use gray with lower opacity
                color_list = []
                for i in range(len(df)):
                    if df[team_column].iloc[i] == team:
                        # Keep original color value for selected team
                        color_list.append(df[color_col].iloc[i])
                    else:
                        # Use None for non-selected to make them gray
                        color_list.append(None)
                
                # Create border for selected team
                border_width = [3 if df[team_column].iloc[i] == team else 0 
                               for i in range(len(df))]
                border_color = ['white' if df[team_column].iloc[i] == team else '' 
                               for i in range(len(df))]
                
                # For non-selected players, we'll make them gray by removing from color axis
                # and setting explicit gray color
                marker_colors = []
                for i in range(len(df)):
                    if df[team_column].iloc[i] == team:
                        marker_colors.append(df[color_col].iloc[i])
                    else:
                        marker_colors.append('rgba(200, 200, 200, 0.3)')  # Light gray with transparency
                
                buttons.append(
                    dict(
                        label=team,
                        method="restyle",
                        args=[{
                            "marker.color": [marker_colors],
                            "marker.line.width": border_width,
                            "marker.line.color": border_color,
                            "marker.coloraxis": None  # Disable color axis to use explicit colors
                        }]
                    )
                )
            
            # Add dropdown menu
            fig.update_layout(
                updatemenus=[
                    dict(
                        buttons=buttons,
                        direction="down",
                        pad={"r": 10, "t": 10},
                        showactive=True,
                        x=0.01,
                        xanchor="left",
                        y=1.15,
                        yanchor="top",
                        bgcolor="white",
                        bordercolor="#333",
                        borderwidth=2,
                        font=dict(size=11)
                    )
                ]
            )
            
            # Add annotation for dropdown
            fig.add_annotation(
                text="<b>Filter by Team:</b>",
                xref="paper",
                yref="paper",
                x=0.01,
                y=1.18,
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=12, color="#333")
            )
        
        # Save or show
        if save_path:
            fig.write_html(save_path)
        else:
            fig.show()
    
    def plot_multi_stat_subplots(self, df, x_column, stats_list, size_column,
                                  label_column, title=None, xlabel=None,
                                  save_path=None, color_column=None, team_column='TEAM',
                                  rank_column=None, color_mode='rating'):
        """
        Create interactive bubble plots with checkboxes to toggle between stats as subplots
        
        Args:
            df (pd.DataFrame): Input dataframe
            x_column (str): Column for x-axis (e.g., minutes played)
            stats_list (list): List of stat columns to create subplots for
            size_column (str): Column for bubble size (e.g., player rating)
            label_column (str): Column for labels (e.g., player names)
            title (str): Chart title
            xlabel (str): X-axis label
            save_path (str): Path to save HTML file
            color_column (str): Optional column for color coding
            team_column (str): Column containing team names for filtering
            rank_column (str): Column containing rank values to display
            color_mode (str): 'rating' for rating-based colors or 'team' for team colors
        """
        if not PLOTLY_AVAILABLE:
            print("Warning: Plotly not installed. Install with: pip install plotly")
            return
        
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        # Check columns
        if team_column not in df.columns:
            team_column = None
        if rank_column and rank_column not in df.columns:
            rank_column = None
        
        # Filter valid stats
        valid_stats = [stat for stat in stats_list if stat in df.columns]
        if not valid_stats:
            print("No valid stats found in dataframe")
            return
        
        # Check if dataframe has data
        if len(df) == 0:
            print("Empty dataframe - no players to plot")
            return
        
        color_col = color_column if color_column else size_column
        
        # Determine colors based on mode
        if color_mode == 'team' and team_column and team_column in df.columns:
            # Map team colors
            marker_colors = []
            for team in df[team_column]:
                if team in self.team_colors:
                    marker_colors.append(self.team_colors[team]['primary'])
                else:
                    marker_colors.append('#808080')  # Gray for unknown teams
            use_colorscale = False
        else:
            # Use rating-based color scale
            marker_colors = df[color_col]
            use_colorscale = True
        
        # Prepare custom data
        custom_data_cols = []
        if team_column:
            custom_data_cols.append(team_column)
        if rank_column:
            custom_data_cols.append(rank_column)
        
        custom_data = df[custom_data_cols].values if custom_data_cols else None
        
        # Create subplots - one row per stat
        fig = make_subplots(
            rows=len(valid_stats),
            cols=1,
            subplot_titles=[f"{stat} per Game" for stat in valid_stats],
            vertical_spacing=0.08,
            specs=[[{"type": "scatter"}] for _ in valid_stats]
        )
        
        # Add a trace for each stat
        for idx, stat in enumerate(valid_stats, start=1):
            # Create scatter trace
            trace_marker = dict(
                size=df[size_column] / 2,  # Scale down for subplot
                color=marker_colors,
                line=dict(width=0, color='white')
            )
            
            # Add colorscale only if using rating mode
            if use_colorscale:
                trace_marker['colorscale'] = 'Viridis'
                trace_marker['showscale'] = (idx == 1)  # Show colorbar only for first subplot
                if idx == 1:
                    trace_marker['colorbar'] = dict(
                        title=size_column.replace('_', ' ').title(),
                        x=1.12,
                        len=0.3,
                        y=0.85
                    )
            
            trace = go.Scatter(
                x=df[x_column],
                y=df[stat],
                mode='markers',
                name=stat,
                marker=trace_marker,
                text=df[label_column],
                customdata=custom_data,
                visible=True,  # All visible by default
                hovertemplate=self._create_hover_template(
                    xlabel or x_column, stat, size_column, 
                    team_column, rank_column, custom_data_cols
                )
            )
            
            fig.add_trace(trace, row=idx, col=1)
            
            # Update axes for each subplot
            fig.update_xaxes(
                title_text=xlabel or x_column if idx == len(valid_stats) else "",
                showgrid=True,
                gridcolor='white',
                row=idx, col=1
            )
            fig.update_yaxes(
                title_text=f"{stat}",
                showgrid=True,
                gridcolor='white',
                row=idx, col=1
            )
        
        # Create checkboxes for toggling stats
        buttons = []
        for i, stat in enumerate(valid_stats):
            visible = [j == i for j in range(len(valid_stats))]
            buttons.append(
                dict(
                    label=stat,
                    method='update',
                    args=[
                        {'visible': visible},
                        {
                            'title': f"{title} - {stat}" if title else f"{stat} Analysis",
                            'showlegend': False
                        }
                    ]
                )
            )
        
        # Add "Show All" button
        buttons.insert(0, dict(
            label='Show All',
            method='update',
            args=[
                {'visible': [True] * len(valid_stats)},
                {
                    'title': title or 'League Overview - All Stats',
                    'showlegend': False
                }
            ]
        ))
        
        # Team filter buttons
        team_buttons = []
        if team_column:
            teams = sorted(df[team_column].unique())
            
            # All Teams button - restore original colors
            team_buttons.append(dict(
                label="All Teams",
                method="restyle",
                args=[{
                    'marker.color': [marker_colors] * len(valid_stats),
                    'marker.line.width': [0] * len(df),
                    'marker.line.color': ['white'] * len(df)
                }]
            ))
            
            # Individual team buttons
            for team in teams:
                # Create color list: original color for selected team, gray for others
                team_marker_colors = []
                border_widths = []
                border_colors = []
                
                for i in range(len(df)):
                    if df[team_column].iloc[i] == team:
                        # Keep original color
                        if color_mode == 'team':
                            team_marker_colors.append(marker_colors[i])
                        else:
                            team_marker_colors.append(marker_colors.iloc[i] if hasattr(marker_colors, 'iloc') else marker_colors[i])
                        border_widths.append(3)
                        border_colors.append('white')
                    else:
                        # Gray out non-selected teams
                        team_marker_colors.append('rgba(200, 200, 200, 0.3)')
                        border_widths.append(0)
                        border_colors.append('white')
                
                team_buttons.append(dict(
                    label=team,
                    method="restyle",
                    args=[{
                        'marker.color': [team_marker_colors] * len(valid_stats),
                        'marker.line.width': border_widths,
                        'marker.line.color': border_colors
                    }]
                ))
        
        # Color mode toggle buttons
        color_mode_buttons = []
        if team_column:
            # Team color mode
            team_color_list = []
            for team in df[team_column]:
                if team in self.team_colors:
                    team_color_list.append(self.team_colors[team]['primary'])
                else:
                    team_color_list.append('#808080')
            
            color_mode_buttons.append(dict(
                label="Team Colors",
                method="restyle",
                args=[{
                    'marker.color': [team_color_list] * len(valid_stats),
                    'marker.coloraxis': [None] * len(valid_stats),
                    'marker.showscale': [False] * len(valid_stats)
                }]
            ))
            
            # Rating color mode
            rating_colors = df[color_col].tolist()
            color_mode_buttons.append(dict(
                label="Rating Colors",
                method="restyle",
                args=[{
                    'marker.color': [rating_colors] * len(valid_stats),
                    'marker.colorscale': ['Viridis'] * len(valid_stats),
                    'marker.showscale': [True if i == 0 else False for i in range(len(valid_stats))]
                }]
            ))
        
        # Update layout
        total_height = 400 * len(valid_stats)
        
        updatemenus_list = [
            # Stats selector
            dict(
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="bottom",
                bgcolor="white",
                bordercolor="#333",
                borderwidth=2,
                font=dict(size=11)
            )
        ]
        
        # Add team filter if available
        if team_column:
            updatemenus_list.append(
                dict(
                    buttons=team_buttons,
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.18,
                    xanchor="left",
                    y=1.02,
                    yanchor="bottom",
                    bgcolor="white",
                    bordercolor="#333",
                    borderwidth=2,
                    font=dict(size=11)
                )
            )
            
            # Add color mode toggle
            updatemenus_list.append(
                dict(
                    buttons=color_mode_buttons,
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.35,
                    xanchor="left",
                    y=1.02,
                    yanchor="bottom",
                    bgcolor="white",
                    bordercolor="#333",
                    borderwidth=2,
                    font=dict(size=11)
                )
            )
        
        fig.update_layout(
            title=dict(
                text=title or 'NBA League Overview',
                font=dict(size=18, family='Arial Black'),
                x=0.5,
                xanchor='center'
            ),
            height=total_height,
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='rgba(240,240,240,0.9)',
            font=dict(size=11),
            margin=dict(t=150, b=50, l=80, r=150),
            updatemenus=updatemenus_list
        )
        
        # Add annotations for dropdowns
        annotations = [
            dict(
                text="<b>Select Stats:</b>",
                xref="paper",
                yref="paper",
                x=0.01,
                y=1.04,
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font=dict(size=12, color="#333")
            )
        ]
        
        if team_column:
            annotations.extend([
                dict(
                    text="<b>Filter by Team:</b>",
                    xref="paper",
                    yref="paper",
                    x=0.18,
                    y=1.04,
                    xanchor="left",
                    yanchor="bottom",
                    showarrow=False,
                    font=dict(size=12, color="#333")
                ),
                dict(
                    text="<b>Color Mode:</b>",
                    xref="paper",
                    yref="paper",
                    x=0.35,
                    y=1.04,
                    xanchor="left",
                    yanchor="bottom",
                    showarrow=False,
                    font=dict(size=12, color="#333")
                )
            ])
        
        fig.update_layout(annotations=annotations)
        
        # Save or show
        if save_path:
            fig.write_html(save_path)
        else:
            fig.show()
    
    def _create_hover_template(self, xlabel, ylabel, size_column, team_column, 
                               rank_column, custom_data_cols):
        """Helper to create hover template"""
        hover_template = '<b>%{text}</b><br>'
        custom_idx = 0
        
        if team_column and team_column in custom_data_cols:
            hover_template += f'Team: %{{customdata[{custom_idx}]}}<br>'
            custom_idx += 1
        
        hover_template += f'{xlabel}: %{{x:.1f}}<br>'
        hover_template += f'{ylabel}: %{{y:.1f}}<br>'
        
        if rank_column and rank_column in custom_data_cols:
            hover_template += f'{size_column.replace("_", " ").title()}: (rk %{{customdata[{custom_idx}]}})<br>'
        
        hover_template += '<extra></extra>'
        return hover_template

