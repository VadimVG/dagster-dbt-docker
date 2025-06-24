import os
from sqlalchemy import create_engine, text


class PostgreDatabaseConnector:
    def __init__(
        self,
        host: str = os.getenv("DWH_HOST"),
        port: int = os.getenv("DWH_PORT"),
        user: str = os.getenv("DWH_USER"),
        password: str = os.getenv("DWH_PASSWORD"),
        db_name: str = os.getenv("DWH_DB"),
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name

    def __enter__(self):
        self.engine = create_engine(f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "engine"):
            self.engine.dispose()

    def execute_query(self, query: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()