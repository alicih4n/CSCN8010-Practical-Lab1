import pandas as pd
import os

class InputSimulator:
    def __init__(self, data_path="../data/test_data_synthetic.csv"):
        self.data_path = os.path.join(os.path.dirname(__file__), data_path)
    
    def get_data(self):
        """
        Reads the CSV data and yields it row by row (as dicts).
        """
        if not os.path.exists(self.data_path):
            print(f"Warning: {self.data_path} does not exist.")
            return []
            
        df = pd.read_csv(self.data_path)
        return df.to_dict('records')
