"""
Export Utilities

This module provides functions for exporting Reddit data to various formats.
"""

import pandas as pd
import json
import os
from typing import List, Dict, Any
from datetime import datetime

def export_to_csv(df: pd.DataFrame, filename: str, directory: str = 'exports') -> str:
    """
    Export DataFrame to CSV file.
    
    Args:
        df: DataFrame to export
        filename: Base filename (without extension)
        directory: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.csv"
    filepath = os.path.join(directory, full_filename)
    
    # Export to CSV
    df.to_csv(filepath, index=False)
    
    return filepath

def export_to_json(data: Dict[str, Any], filename: str, directory: str = 'exports') -> str:
    """
    Export data to JSON file.
    
    Args:
        data: Data to export
        filename: Base filename (without extension)
        directory: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.json"
    filepath = os.path.join(directory, full_filename)
    
    # Export to JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)
    
    return filepath

def export_to_excel(df_dict: Dict[str, pd.DataFrame], filename: str, directory: str = 'exports') -> str:
    """
    Export multiple DataFrames to a single Excel file with multiple sheets.
    
    Args:
        df_dict: Dictionary mapping sheet names to DataFrames
        filename: Base filename (without extension)
        directory: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.xlsx"
    filepath = os.path.join(directory, full_filename)
    
    # Export to Excel
    with pd.ExcelWriter(filepath) as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return filepath

def save_figure(fig, filename: str, directory: str = 'exports', format: str = 'png') -> str:
    """
    Save a matplotlib figure to a file.
    
    Args:
        fig: Matplotlib figure to save
        filename: Base filename (without extension)
        directory: Directory to save the file in
        format: File format (png, jpg, pdf, etc.)
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.{format}"
    filepath = os.path.join(directory, full_filename)
    
    # Save figure
    fig.savefig(filepath, format=format, dpi=300, bbox_inches='tight')
    
    return filepath 