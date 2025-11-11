import os
from typing import Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    db_name: str


pg_config = DBConfig(
    host = os.getenv("DWH_HOST"),
    port = os.getenv("DWH_PORT"),
    user = os.getenv("DWH_USER"),
    password = os.getenv("DWH_PASSWORD"),
    db_name = os.getenv("DWH_DB"),
)


class PGConnection:
    def __init__(self, config: DBConfig):
        self.host = config.host
        self.port = config.port
        self.user = config.user
        self.password = config.password
        self.db_name = config.db_name
        self.engine = None

    def __get_connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
    
    def create_engine(self) -> None:
        connection_string = self.__get_connection_string()
        self.engine = create_engine(
            connection_string,
            poolclass=NullPool
        )

    def execute_query(self, query: str) -> Optional[Tuple]:
        """Контекстный менеджер для connection"""
        if not self.engine:
            self.create_engine()
        
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query))
                if result.returns_rows:
                    return result.fetchall()
                conn.commit()
            finally:
                self.close_engine()

    def close_engine(self) -> None:
        if self.engine:
            self.engine.dispose()
            

def get_pg_connect() -> PGConnection:
    return PGConnection(config=pg_config)
