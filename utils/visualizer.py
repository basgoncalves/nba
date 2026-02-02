"""Module for visualizing NBA statistics"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

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
                                save_path=None, color_column=None, team_column='TEAM'):
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
        
        # Add color column to hover if specified
        if color_column and color_column in df.columns:
            hover_data[color_column] = ':.1f'
        
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
            custom_data=[team_column] if team_column else None
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
        if team_column:
            hover_template += f'Team: %{{customdata[0]}}<br>'
        hover_template += (f'{xlabel or x_column}: %{{x:.1f}}<br>' +
                          f'{ylabel or y_column}: %{{y:.1f}}<br>' +
                          f'{size_column.replace("_", " ").title()}: %{{marker.size:.1f}}<br>' +
                          '<extra></extra>')
        
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

