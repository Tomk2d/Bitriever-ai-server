import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()


class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        if not all([self.host, self.port, self.database, self.username, self.password]):
            raise ValueError(
                "필수 데이터베이스 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요."
            )

        self.database_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

        self.engine = create_engine(
            self.database_url, echo=False, pool_size=5, max_overflow=10
        )

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        self.Base = declarative_base()

    def get_session(self):
        """return db session"""
        return self.SessionLocal()

    def create_tables(self):
        """create all tables"""
        # 모델들을 명시적으로 import하여 순서 보장
        import model.Users
        import model.ExchangeCredentials
        import model.Coins
        import model.TradingHistories
        import model.Assets
        import model.CoinHoldingsPast
        import model.CoinPricesDay
        import model.TradeEvaluationResult

        self.Base.metadata.create_all(bind=self.engine)

    def test_connection(self):
        """db connection test"""
        try:
            with self.engine.connect() as connection:
                from sqlalchemy import text

                result = connection.execute(text("SELECT 1"))
                print("Successfully connected to PostgreSQL!")
                return True
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            return False


db = DatabaseConnection()
