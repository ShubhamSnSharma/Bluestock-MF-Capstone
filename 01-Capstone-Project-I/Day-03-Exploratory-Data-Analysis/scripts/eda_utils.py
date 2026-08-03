import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Define base paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PNG_DIR = os.path.join(BASE_DIR, "charts", "png")
HTML_DIR = os.path.join(BASE_DIR, "charts", "html")

os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

# Standardized Color Palettes & Visual Constants
FONT_FAMILY = "Arial, sans-serif"
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#2ca02c"
ACCENT_COLOR = "#ff7f0e"

def set_plot_style():
    """
    Configure global plotting aesthetics for Seaborn, Matplotlib, and Plotly.
    """
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.labelweight'] = 'medium'
    pio.templates.default = "plotly_white"
    print("Global visualization themes & design tokens initialized successfully.")

def apply_plotly_theme(fig, title, xlabel=None, ylabel=None):
    """
    Apply unified design system to a Plotly figure.
    """
    layout_update = dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family=FONT_FAMILY, size=16, color="#2c3e50"),
            x=0.01,
            xanchor="left"
        ),
        font=dict(family=FONT_FAMILY, size=12, color="#333333"),
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        margin=dict(l=60, r=40, t=60, b=60),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1
        )
    )
    if xlabel:
        layout_update["xaxis_title"] = xlabel
    if ylabel:
        layout_update["yaxis_title"] = ylabel
        
    fig.update_layout(**layout_update)
    fig.update_xaxes(showgrid=True, gridcolor="#e9ecef")
    fig.update_yaxes(showgrid=True, gridcolor="#e9ecef")
    return fig

def apply_matplotlib_theme(ax, title, xlabel=None, ylabel=None):
    """
    Apply unified design system to a Matplotlib/Seaborn Axes object.
    """
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#2c3e50')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12, labelpad=10, fontweight='medium')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12, labelpad=10, fontweight='medium')
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1')
    sns.despine(ax=ax, top=True, right=True)
    return ax

def save_plot_png(fig, filename):
    """
    Save a Plotly figure as a high-resolution 300 DPI static PNG.
    """
    filepath = os.path.join(PNG_DIR, filename)
    try:
        fig.write_image(filepath, scale=2)
        print(f"Saved Plotly PNG chart: {filepath}")
    except Exception as e:
        print(f"Note: Plotly static export fallback for {filename}: {str(e)}")

def save_matplotlib_png(filename):
    """
    Save the current active Matplotlib/Seaborn plot to charts/png/ at 300 DPI.
    """
    filepath = os.path.join(PNG_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved Matplotlib/Seaborn 300 DPI PNG chart: {filepath}")

def save_plot_html(fig, filename):
    """
    Save an interactive Plotly figure as HTML into charts/html/
    """
    filepath = os.path.join(HTML_DIR, filename)
    fig.write_html(filepath)
    print(f"Saved HTML interactive chart: {filepath}")

def print_dataset_summary(df, name):
    """
    Print structural information, shape, null counts, and column data types for a dataset.
    """
    print(f"=== {name.upper()} OVERVIEW ===")
    print(f"Shape: {df.shape}")
    print(f"Total Missing Values: {df.isnull().sum().sum()}")
    print("Column Data Types & Unique Values:")
    for col in df.columns:
        print(f"  - {col:<25}: {str(df[col].dtype):<10} ({df[col].nunique()} unique)")
    print("-" * 50)
