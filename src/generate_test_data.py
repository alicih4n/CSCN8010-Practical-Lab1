
import json
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Author: Ali Cihan Ozdemir

def load_metadata(path='../models/model_metadata.json'):
    full_path = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Metadata file not found at {full_path}. Run 01_Model_Training.ipynb first.")
    with open(full_path, 'r') as f:
        return json.load(f)

def generate_data(output_file='../data/test_data_synthetic.csv', duration_seconds=600):
    try:
        metadata = load_metadata()
    except FileNotFoundError as e:
        print(e)
        return

    models = metadata['models']
    thresholds = metadata['thresholds']
    t_threshold = metadata['global_config']['T_seconds']

    # Generate Time Index
    # Start from an arbitrary future time
    start_time = datetime.now()
    time_index = [start_time + timedelta(seconds=i*2) for i in range(duration_seconds // 2)]
    df = pd.DataFrame({'time': time_index})
    df['seconds_from_start'] = np.arange(0, duration_seconds, 2)
    
    # Generate Baseline Data
    for axis, params in models.items():
        slope = params['slope']
        intercept = params['intercept']
        
        # Base signal
        noise_std = thresholds[axis]['std']
        noise = np.random.normal(0, noise_std, size=len(df))
        df[axis] = slope * df['seconds_from_start'] + intercept + noise
    
    # Inject Anomalies
    axes = list(models.keys())
    
    # 1. Inject ALERT (MinC < x < MaxC)
    target_axis = axes[0]
    min_c = thresholds[target_axis]['min_c']
    max_c = thresholds[target_axis]['max_c']
    
    # Inject for T + 2 seconds
    start_idx = 50
    duration_idx = int(t_threshold / 2) + 2
    for i in range(start_idx, start_idx + duration_idx):
        # Force value to be just above MinC
        base_val = models[target_axis]['slope'] * df.loc[i, 'seconds_from_start'] + models[target_axis]['intercept']
        df.loc[i, target_axis] = base_val + min_c + (0.1 * min_c)

    print(f"Injected ALERT on {target_axis} at index {start_idx} for {duration_idx} samples.")

    # 2. Inject ERROR (x > MaxC)
    target_axis = axes[1]
    max_c = thresholds[target_axis]['max_c']
    
    start_idx = 100
    duration_idx = int(t_threshold / 2) + 5
    for i in range(start_idx, start_idx + duration_idx):
        # Force value to be way above MaxC
        base_val = models[target_axis]['slope'] * df.loc[i, 'seconds_from_start'] + models[target_axis]['intercept']
        df.loc[i, target_axis] = base_val + max_c + (2.0 * max_c)

    print(f"Injected ERROR on {target_axis} at index {start_idx} for {duration_idx} samples.")
    
    # Save
    out_path = os.path.join(os.path.dirname(__file__), output_file)
    df.to_csv(out_path, index=False)
    print(f"Synthetic test data saved to {out_path}")

if __name__ == "__main__":
    generate_data()
