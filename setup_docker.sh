# 1. 기존 컨테이너 중지
echo ""
echo "📦 1단계: 기존 컨테이너 중지 중..."
docker-compose down

echo ""
echo "📦 2단계: 컨테이너 빌드 중..."
docker-compose build

echo ""
echo "📦 3단계: 컨테이너 실행 중..."
docker-compose up -d

echo ""
echo "📦 4단계: 데이터베이스 접속 중..."
docker exec -it bitriever-postgres psql -U bitriever_host -d bitriever_db

echo ""
echo "📦 5단계: 데이터베이스 접속 완료"