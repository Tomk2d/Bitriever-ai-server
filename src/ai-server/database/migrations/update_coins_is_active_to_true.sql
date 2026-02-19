-- coins 테이블의 is_active가 NULL인 모든 코인을 True로 업데이트

-- 방법 1: NULL인 것만 True로 업데이트
UPDATE coins 
SET is_active = TRUE 
WHERE is_active IS NULL;

-- 방법 2: 모든 코인을 True로 업데이트 (NULL이든 False든 상관없이)
-- UPDATE coins 
-- SET is_active = TRUE;

-- 업데이트 후 확인
-- SELECT COUNT(*) as total_coins FROM coins;
-- SELECT COUNT(*) as active_coins FROM coins WHERE is_active = TRUE;
-- SELECT COUNT(*) as inactive_coins FROM coins WHERE is_active = FALSE;
-- SELECT COUNT(*) as null_coins FROM coins WHERE is_active IS NULL;

