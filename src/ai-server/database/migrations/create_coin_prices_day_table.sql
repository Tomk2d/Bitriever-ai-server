-- 일봉 캔들 데이터 저장 테이블
-- 테이블명: coin_prices_day

CREATE TABLE IF NOT EXISTS coin_prices_day (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER NOT NULL,
    market_code VARCHAR(20) NOT NULL,
    candle_date_time_utc TIMESTAMP NOT NULL,
    candle_date_time_kst TIMESTAMP NOT NULL,
    opening_price NUMERIC(20, 8) NOT NULL,
    high_price NUMERIC(20, 8) NOT NULL,
    low_price NUMERIC(20, 8) NOT NULL,
    trade_price NUMERIC(20, 8) NOT NULL,
    timestamp BIGINT NOT NULL,
    candle_acc_trade_price NUMERIC(30, 8) NOT NULL,
    candle_acc_trade_volume NUMERIC(30, 8) NOT NULL,
    prev_closing_price NUMERIC(20, 8) NOT NULL,
    change_price NUMERIC(20, 8) NOT NULL,
    change_rate NUMERIC(20, 8) NOT NULL,
    converted_trade_price NUMERIC(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    FOREIGN KEY (coin_id) REFERENCES coins(id) ON DELETE CASCADE,
    
    -- 중복 방지를 위한 유니크 제약조건
    UNIQUE(market_code, candle_date_time_utc)
);

-- 인덱스 생성
-- coin_id 인덱스 (코인 ID로 단일 조회 시 사용)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_coin_id 
ON coin_prices_day(coin_id);

-- coin_id + candle_date_time_utc 복합 인덱스 (가장 일반적인 조회 패턴)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_coin_id_date_utc 
ON coin_prices_day(coin_id, candle_date_time_utc);

-- coin_id + candle_date_time_kst 복합 인덱스 (한국 시간 기준 조회)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_coin_id_date_kst 
ON coin_prices_day(coin_id, candle_date_time_kst);

-- market_code와 candle_date_time_utc 복합 인덱스 (market_code로 조회하는 경우)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_market_date 
ON coin_prices_day(market_code, candle_date_time_utc);

-- market_code 단일 인덱스 (특정 코인 조회 시 사용)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_market 
ON coin_prices_day(market_code);

-- candle_date_time_utc 인덱스 (날짜 범위 조회 시 사용)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_date_utc 
ON coin_prices_day(candle_date_time_utc);

-- candle_date_time_kst 인덱스 (한국 시간 기준 조회 시 사용)
CREATE INDEX IF NOT EXISTS idx_coin_prices_day_date_kst 
ON coin_prices_day(candle_date_time_kst);

-- 코멘트 추가
COMMENT ON TABLE coin_prices_day IS '업비트 일봉 캔들 데이터 저장 테이블';
COMMENT ON COLUMN coin_prices_day.coin_id IS '코인 ID (coins 테이블의 id를 참조)';
COMMENT ON COLUMN coin_prices_day.market_code IS '거래쌍 코드 (예: KRW-BTC), coins.market_code와 매칭';
COMMENT ON COLUMN coin_prices_day.candle_date_time_utc IS '캔들 구간의 시작 시각 (UTC 기준)';
COMMENT ON COLUMN coin_prices_day.candle_date_time_kst IS '캔들 구간의 시작 시각 (KST 기준)';
COMMENT ON COLUMN coin_prices_day.opening_price IS '시가';
COMMENT ON COLUMN coin_prices_day.high_price IS '고가';
COMMENT ON COLUMN coin_prices_day.low_price IS '저가';
COMMENT ON COLUMN coin_prices_day.trade_price IS '종가';
COMMENT ON COLUMN coin_prices_day.timestamp IS '해당 캔들의 마지막 틱이 저장된 시각의 타임스탬프 (ms)';
COMMENT ON COLUMN coin_prices_day.candle_acc_trade_price IS '해당 캔들 동안의 누적 거래 금액';
COMMENT ON COLUMN coin_prices_day.candle_acc_trade_volume IS '해당 캔들 동안의 누적 거래된 디지털 자산의 수량';
COMMENT ON COLUMN coin_prices_day.prev_closing_price IS '전일 종가 (UTC 0시 기준)';
COMMENT ON COLUMN coin_prices_day.change_price IS '전일 종가 대비 가격 변화';
COMMENT ON COLUMN coin_prices_day.change_rate IS '전일 종가 대비 가격 변화율';
COMMENT ON COLUMN coin_prices_day.converted_trade_price IS '종가 환산 가격 (선택적)';

