"""Module for visualizing NBA statistics"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


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
