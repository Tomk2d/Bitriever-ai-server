from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import importlib
from utils.router_utils import register_routers
from database.database_connection import db
from utils.app_initializer import initialize_app
import logging
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("🚀 애플리케이션 시작 중...")

    try:
        # 애플리케이션 초기화 (암호화 시스템 포함)
        initialize_app()

        # 데이터베이스 연결 테스트
        if db.test_connection():
            logger.info("✅ 데이터베이스 연결 성공")

            # 테이블 생성
            db.create_tables()
            logger.info("✅ 데이터베이스 테이블 생성 완료")
        else:
            logger.error("❌ 데이터베이스 연결 실패")
            raise Exception("데이터베이스 연결에 실패했습니다")

    except Exception as e:
        logger.error(f"❌ 애플리케이션 초기화 실패: {e}")
        raise

    logger.info("✅ 애플리케이션 시작 완료")

    yield

    # 종료 시
    logger.info("🛑 애플리케이션 종료 중...")


app = FastAPI(
    title="BIT Diary API",
    description="암호화폐 투자 지원을 위한 API",
    version="0.1.1",
    lifespan=lifespan,
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 자동 라우터 등록
register_routers(app)


@app.get("/")
async def root():
    return {"message": "Bitriever API", "version": "0.1.1"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
