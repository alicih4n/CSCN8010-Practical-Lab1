
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from db_connector import DatabaseConnector
from sqlalchemy import text

# Author: Ali Cihan Ozdemir

import matplotlib.pyplot as plt

class AlertSystem:
    def __init__(self, metadata_path='../models/model_metadata.json'):
        self.metadata_path = os.path.join(os.path.dirname(__file__), metadata_path)
        self.load_metadata()
        self.connector = DatabaseConnector()
        self.engine = self.connector.get_engine()
        self.ensure_log_table_exists()
        
        # State tracking for continuous violations
        self.active_violations = {} 
        # Visualization history
        self.history = []
        self.events = []

    def load_metadata(self):
        if not os.path.exists(self.metadata_path):
            print(f"Warning: Metadata file not found at {self.metadata_path}. Alert System will not function correctly until training is run.")
            self.metadata = None
            return

        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.models = self.metadata['models']
        self.thresholds = self.metadata['thresholds']
        self.T_seconds = self.metadata['global_config']['T_seconds']
        print(f"Metadata loaded. T_seconds={self.T_seconds}")

    def ensure_log_table_exists(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50),
            axis VARCHAR(50),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds FLOAT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()

    def predict(self, axis, time_seconds):
        if not self.metadata: return 0
        slope = self.models[axis]['slope']
        intercept = self.models[axis]['intercept']
        return slope * time_seconds + intercept

    def check_stream(self, row, verbose=False):
        """
        row: dict or series containing 'time', 'seconds_from_start', 'axis_1'...'axis_8'
        """
        if not self.metadata: return

        # Store for plotting
        self.history.append(row)

        current_time = pd.to_datetime(row['time'])
        seconds = row['seconds_from_start']
        
        for axis, params in self.thresholds.items():
            if axis not in row: continue
            
            observed = row[axis]
            predicted = self.predict(axis, seconds)
            residual = observed - predicted
            abs_res = abs(residual)
            
            # Thresholds
            min_c = params['min_c']
            max_c = params['max_c']
            
            # Determine current violation level
            violation_type = None
            if abs_res > max_c:
                violation_type = 'ERROR'
            elif abs_res > min_c:
                violation_type = 'ALERT'
            
            # State Management
            state_key = axis
            status_msg = "Normal"
            duration = 0.0
            
            if violation_type:
                if state_key not in self.active_violations:
                    # New violation started
                    self.active_violations[state_key] = {
                        'start_time': current_time,
                        'type': violation_type,
                        'max_severity': violation_type # Track if it escalated to ERROR
                    }
                    status_msg = f"{violation_type} Started"
                else:
                    # Ongoing violation
                    start_time = self.active_violations[state_key]['start_time']
                    duration = (current_time - start_time).total_seconds()
                    status_msg = f"{violation_type} Ongoing ({duration:.1f}s)"
                    
                    # Update severity if escalated
                    if violation_type == 'ERROR':
                        self.active_violations[state_key]['max_severity'] = 'ERROR'
                    
                    if duration >= self.T_seconds:
                        status_msg = f"{violation_type} PERSISTED > {self.T_seconds}s -> LOG EVENT"
                        if not self.active_violations[state_key].get('alerted'):
                            severity = self.active_violations[state_key]['max_severity']
                            msg = f"{severity} detected on {axis}. Variance {abs_res:.2f} > Threshold for {duration:.1f}s"
                            print(msg)
                            self.log_event(severity, axis, start_time, current_time, duration, msg)
                            self.active_violations[state_key]['alerted'] = True
            else:
                # Violation ended
                if state_key in self.active_violations:
                    status_msg = "Violation Ended"
                    del self.active_violations[state_key]
            
            if verbose and (violation_type or status_msg != "Normal"):
                print(f"[{current_time.time()}] {axis}: Val={observed:.2f} | Res={abs_res:.2f} | {status_msg}")

    def log_event(self, event_type, axis, start_time, end_time, duration, message):
        # Store internally for plotting
        self.events.append({
            'event_type': event_type,
            'axis': axis,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'message': message
        })

        sql = """
        INSERT INTO maintenance_logs (event_type, axis, start_time, end_time, duration_seconds, message)
        VALUES (:event_type, :axis, :start_time, :end_time, :duration, :message)
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql), {
                    "event_type": event_type,
                    "axis": axis,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "message": message
                })
                conn.commit()
        except Exception as e:
            print(f"Failed to log event: {e}")

    def run_simulation(self, stream_data, verbose=False):
        print("Running simulation...")
        self.history = [] # Reset history
        self.events = []  # Reset events
        for row in stream_data:
            self.check_stream(row, verbose=verbose)
        print("Simulation complete.")

    def plot_results(self):
        if not self.history:
            print("No history to plot. Run simulation first.")
            return

        df = pd.DataFrame(self.history)
        df['time'] = pd.to_datetime(df['time'])
        
        # Identify axes with events
        axes_with_events = set(e['axis'] for e in self.events)
        if not axes_with_events:
            print("No events detected to visualize.")
            axes = ['axis_1'] # Default
        else:
            axes = list(axes_with_events)

        plt.figure(figsize=(15, 6 * len(axes)))
        
        for i, axis in enumerate(axes):
            plt.subplot(len(axes), 1, i+1)
            
            # Plot raw data
            plt.plot(df['time'], df[axis], label=f'{axis} Signal', color='blue', alpha=0.6)
            
            # Plot Threshold Tunnel
            slope = self.models[axis]['slope']
            intercept = self.models[axis]['intercept']
            seconds = df['seconds_from_start']
            predicted = slope * seconds + intercept
            
            min_c = self.thresholds[axis]['min_c']
            max_c = self.thresholds[axis]['max_c']
            
            plt.plot(df['time'], predicted, 'k--', label='Baseline', alpha=0.4)
            plt.fill_between(df['time'], predicted - min_c, predicted + min_c, color='green', alpha=0.1, label='Normal Space')
            plt.fill_between(df['time'], predicted - max_c, predicted + max_c, color='yellow', alpha=0.05, label='Alert Space')
            
            # Highlight Events
            for event in self.events:
                if event['axis'] == axis:
                    color = 'red' if event['event_type'] == 'ERROR' else 'orange'
                    plt.axvspan(event['start_time'], event['end_time'], color=color, alpha=0.3, label=f"{event['event_type']}")
            
            # Clean up duplicate labels
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys())
            
            plt.title(f"Anomaly Detection: {axis}")
            plt.xlabel("Time")
            plt.ylabel("Sensor Value")
            
        plt.tight_layout()
        plt.show()
