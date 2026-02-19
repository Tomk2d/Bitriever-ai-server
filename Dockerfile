# Build/run stage — Poetry로 의존성 설치 후 uvicorn 실행
FROM python:3.11-slim

WORKDIR /app

# kiwipiepy 빌드에 필요 (CMake + C++ 컴파일러)
RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# 의존성: poetry export 후 pip로 설치 (kiwipiepy 빌드 시 numpy가 필요해 격리 없이 설치)
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir numpy \
    && poetry export -f requirements.txt --without-hashes --only main -o requirements.txt \
    && pip install --no-cache-dir --no-build-isolation -r requirements.txt

# 소스 복사
COPY src ./src

WORKDIR /app/src/ai-server
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
