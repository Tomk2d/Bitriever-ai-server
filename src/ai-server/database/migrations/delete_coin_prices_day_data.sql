-- coin_prices_day 테이블의 모든 데이터 삭제

-- 방법 1: 모든 데이터 삭제 (권장)
DELETE FROM coin_prices_day;

-- 방법 2: 특정 코인만 삭제
-- DELETE FROM coin_prices_day WHERE market_code = 'KRW-BTC';

-- 방법 3: 특정 기간만 삭제
-- DELETE FROM coin_prices_day WHERE candle_date_time_utc >= '2020-01-01' AND candle_date_time_utc < '2021-01-01';

-- 삭제 후 확인
-- SELECT COUNT(*) FROM coin_prices_day;


