
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from db_connector import DatabaseConnector
from sqlalchemy import text

# Author: Ali Cihan Ozdemir

class AlertSystem:
    def __init__(self, metadata_path='../models/model_metadata.json'):
        self.metadata_path = os.path.join(os.path.dirname(__file__), metadata_path)
        self.load_metadata()
        self.connector = DatabaseConnector()
        self.engine = self.connector.get_engine()
        self.ensure_log_table_exists()
        
        # State tracking for continuous violations
        # Format: {'axis_name': {'start_time': datetime, 'type': 'min_c'|'max_c'}}
        self.active_violations = {} 

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

    def check_stream(self, row):
        """
        row: dict or series containing 'time', 'seconds_from_start', 'axis_1'...'axis_8'
        """
        if not self.metadata: return

        current_time = pd.to_datetime(row['time'])
        seconds = row['seconds_from_start']
        
        alerts = []

        for axis, params in self.thresholds.items():
            if axis not in row: continue
            
            observed = row[axis]
            predicted = self.predict(axis, seconds)
            residual = observed - predicted
            abs_res = abs(residual)
            
            mean_res = params['mean'] # Usually close to 0
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
            
            if violation_type:
                if state_key not in self.active_violations:
                    # New violation started
                    self.active_violations[state_key] = {
                        'start_time': current_time,
                        'type': violation_type,
                        'max_severity': violation_type # Track if it escalated to ERROR
                    }
                else:
                    # Ongoing violation
                    # Check duration
                    start_time = self.active_violations[state_key]['start_time']
                    duration = (current_time - start_time).total_seconds()
                    
                    # Update severity if escalated
                    if violation_type == 'ERROR':
                        self.active_violations[state_key]['max_severity'] = 'ERROR'
                    
                    if duration >= self.T_seconds:
                        # Threshold met! But we only log once per event? 
                        # Or continuously? Prompt: "Log every detected Alert and Error event"
                        # "An event triggers ONLY if..."
                        # I'll log it when it ENDS or periodically?
                        # Usually you alert immediately once T is crossed.
                        # I will add a flag 'alerted' to avoid spamming every second.
                        if not self.active_violations[state_key].get('alerted'):
                            severity = self.active_violations[state_key]['max_severity']
                            msg = f"{severity} detected on {axis}. Variance {abs_res:.2f} > Threshold for {duration:.1f}s"
                            print(msg)
                            self.log_event(severity, axis, start_time, current_time, duration, msg)
                            self.active_violations[state_key]['alerted'] = True
            else:
                # Violation ended
                if state_key in self.active_violations:
                    # It was active, now it stopped.
                    # Verify if we should log the "End" of the event if it was valid?
                    # For now, just clear state.
                    del self.active_violations[state_key]

    def log_event(self, event_type, axis, start_time, end_time, duration, message):
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

    def run_simulation(self, stream_data):
        print("Running simulation...")
        for row in stream_data:
            self.check_stream(row)
        print("Simulation complete.")
