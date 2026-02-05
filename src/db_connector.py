import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnector:
    """
    Handles connections to the PostgreSQL database (Neon.tech).
    """
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables. Please check your .env file.")

    def get_connection(self):
        """
        Returns a raw psycopg2 connection object.
        """
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def get_engine(self):
        """
        Returns a SQLAlchemy engine for use with Pandas.
        """
        try:
            engine = create_engine(self.db_url)
            return engine
        except Exception as e:
            print(f"Error creating SQLAlchemy engine: {e}")
            raise
