# CSCN8010 Practical Lab 1: Predictive Maintenance with Linear Regression-Based Alerts

**Student:** Ali Cihan Ozdemir

## Project Summary
This project implements a predictive maintenance system for manufacturing robots. It streams sensor data into a PostgreSQL database, determines normal operating patterns using Univariate Linear Regression, and establishes dynamic thresholds (MinC and MaxC) to detect anomalies. Real-time alerts are generated and logged when deviations persist for a specified duration (T seconds).

## Project Structure
- `data/`: Contains raw CSV data and generated synthetic test data.
- `src/`: Python source code for ingestion, database connection, and alert system.
  - `db_connector.py`: Handles PostgreSQL connections.
  - `ingest_data.py`: Processes and ingests training data.
  - `alert_system.py`: Real-time anomaly detection logic.
  - `generate_test_data.py`: Generates synthetic data for testing.
- `notebooks/`: Jupyter notebooks for analysis and visualization.
  - `01_Model_Training.ipynb`: Regression modeling and threshold discovery.
  - `02_Final_Dashboard.ipynb`: Final visualization of the alert system in action.
- `models/`: Stores trained model metadata (`slope`, `intercept`, `thresholds`).

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Configuration:**
   - This project uses Neon.tech PostgreSQL.
   - Create a `.env` file in the root directory (template provided) and add your connection string:
     ```
     DATABASE_URL=postgresql://user:password@endpoint.neon.tech/dbname?sslmode=require
     ```

## Execution Steps

1. **Ingest Data:**
   Run the ingestion script to load training data into the database.
   ```bash
   python src/ingest_data.py
   ```

2. **Model Training & Threshold Discovery:**
   Open and run `notebooks/01_Model_Training.ipynb`. 
   - This will train the regression models.
   - It will save `model_metadata.json` to the `models/` directory.
   - **Important:** Analyze the residual plots in this notebook to justify your choice of MinC, MaxC, and T.

3. **Generate Test Data:**
   Create synthetic data with injected anomalies to test the system.
   ```bash
   python src/generate_test_data.py
   ```

4. **Verify Alert System:**
   Open and run `notebooks/02_Final_Dashboard.ipynb`.
   - This simulates a live stream using the test data.
   - It visualizes the alerts and errors detected by the `AlertSystem`.

## Threshold Discovery & Justification

*(To be filled after running 01_Model_Training.ipynb)*

**Evidence from Residual Plots:**
- The residuals for the stable axes tracked normally distributed noise.
- **MinC (Alert Threshold):** Selected as **2 Sigma** (roughly 95% confidence interval). This captures significant deviations without excessive false positives.
- **MaxC (Error Threshold):** Selected as **3 Sigma** (roughly 99.7% confidence interval). Values beyond this are statistically highly improbable and indicate a fault.
- **T (Time Duration):** set to **5 seconds** to filter out transient spikes and ensure only sustained deviations trigger alerts.
