
import pandas as pd
import numpy as np
import os
from sqlalchemy import text
from db_connector import DatabaseConnector

# Author: Ali Cihan Ozdemir

def clean_column_names(df):
    """
    Renames columns to be database-friendly (snake_case).
    Axis #1 -> axis_1
    """
    new_columns = {}
    for col in df.columns:
        if col.startswith("Axis #"):
            # Extract number
            num = col.replace("Axis #", "")
            new_columns[col] = f"axis_{num}"
        elif col == "Time":
            new_columns[col] = "time"
        else:
            new_columns[col] = col.lower().replace(" ", "_")
    return df.rename(columns=new_columns)

def process_data(file_path):
    print(f"Reading {file_path}...")
    df = pd.read_csv(file_path)
    
    # Rename columns
    df = clean_column_names(df)
    
    # Convert time to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Calculate seconds from start (useful for regression)
    start_time = df['time'].min()
    df['seconds_from_start'] = (df['time'] - start_time).dt.total_seconds()

    # Process Axis 1 to 8
    axes = [f"axis_{i}" for i in range(1, 9)]
    
    for axis in axes:
        if axis in df.columns:
            # Min-Max Normalization
            min_val = df[axis].min()
            max_val = df[axis].max()
            if max_val - min_val != 0:
                df[f"{axis}_minmax"] = (df[axis] - min_val) / (max_val - min_val)
            else:
                df[f"{axis}_minmax"] = 0.0
            
            # Z-Score Standardization
            mean_val = df[axis].mean()
            std_val = df[axis].std()
            if std_val != 0:
                df[f"{axis}_std"] = (df[axis] - mean_val) / std_val
            else:
                df[f"{axis}_std"] = 0.0
    
    # Keep only relevant columns: time, seconds_from_start, and axis_1..8 (raw, minmax, std)
    keep_cols = ['time', 'seconds_from_start']
    for axis in axes:
        if axis in df.columns:
            keep_cols.append(axis)
            keep_cols.append(f"{axis}_minmax")
            keep_cols.append(f"{axis}_std")
            
    return df[keep_cols]

def ingest_to_db(df, table_name="training_data"):
    connector = DatabaseConnector()
    engine = connector.get_engine()
    
    print(f"Ingesting {len(df)} rows into table '{table_name}'...")
    
    # Using 'replace' to drop table if exists and recreate it
    # This is appropriate for a lab/setup script.
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    print("Ingestion complete.")

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "../data/RMBR4-2_export_test.csv")
    
    try:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            exit(1)
            
        processed_df = process_data(file_path)
        ingest_to_db(processed_df)
        
    except Exception as e:
        print(f"An error occurred: {e}")
