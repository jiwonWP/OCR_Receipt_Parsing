"""
config.py 모듈 단위 테스트
- ValidationPolicy: 검증 정책
- LabelTokens: 라벨 토큰
- Patterns: 정규식 패턴
- PreprocessRules: 전처리 규칙 순서
"""
import pytest
import re
from src.config import ValidationPolicy, LabelTokens, Patterns, PreprocessRules, Constants



class TestValidationPolicy:    
    def test_min_tolerance(self):
        # 최소 허용 오차 (10kg)
        # 작은 값에서는 MIN_TOLERANCE_KG 적용
        tolerance = ValidationPolicy.get_tolerance(100) 
        assert tolerance == 10
    
    def test_percentage_tolerance(self):
        # 비율 허용 오차 (2%)
        # 큰 값에서는 TOLERANCE_PERCENT 적용
        tolerance = ValidationPolicy.get_tolerance(1000) 
        assert tolerance == 20
    
    def test_large_value_tolerance(self):
        # 큰 값에 대한 허용 오차
        tolerance = ValidationPolicy.get_tolerance(10000)  
        assert tolerance == 200
    
    def test_required_fields(self):
        assert "date" in ValidationPolicy.REQUIRED_FIELDS
        assert "vehicle_no" in ValidationPolicy.REQUIRED_FIELDS
    
    def test_max_realistic_weight(self):
        assert ValidationPolicy.MAX_REALISTIC_WEIGHT_KG == 100000 


# 라벨 토큰 테스트 
class TestLabelTokens:
    
    def test_gross_weight_tokens(self):
        # 총중량 라벨 토큰
        assert "총중량" in LabelTokens.GROSS_WEIGHT
        assert "총 중량" in LabelTokens.GROSS_WEIGHT
    
    def test_tare_weight_tokens(self):
        # 차중량 라벨 토큰
        assert "차중량" in LabelTokens.TARE_WEIGHT
        assert "공차" in LabelTokens.TARE_WEIGHT
        assert "공차중량" in LabelTokens.TARE_WEIGHT
    
    def test_net_weight_tokens(self):
        # 실중량 라벨 토큰
        assert "실중량" in LabelTokens.NET_WEIGHT
        assert "적재중량" in LabelTokens.NET_WEIGHT
    
    def test_date_tokens(self):
        # 날짜 라벨 토큰
        assert "일자" in LabelTokens.DATE
        assert "날짜" in LabelTokens.DATE
    
    def test_vehicle_no_tokens(self):
        # 차량번호 라벨 토큰
        assert "차량번호" in LabelTokens.VEHICLE_NO
        assert "차량 번호" in LabelTokens.VEHICLE_NO
        assert "차량No" in LabelTokens.VEHICLE_NO
    
    def test_as_dict(self):
        # 딕셔너리 형태 반환
        label_dict = LabelTokens.as_dict()
        assert "gross_weight" in label_dict
        assert "tare_weight" in label_dict
        assert "net_weight" in label_dict
        assert "date" in label_dict
        assert "vehicle_no" in label_dict



# 정규식 패턴 테스트 
class TestPatterns:
    """정규식 패턴 테스트"""
    
    def test_date_pattern_standard(self):
        """날짜 패턴 - 표준 형식"""
        match = Patterns.DATE.search("2026-02-04")
        assert match is not None
        assert match.group("y") == "2026"
        assert match.group("m") == "02"
        assert match.group("d") == "04"
    
    def test_date_pattern_slash(self):
        """날짜 패턴 - 슬래시 구분자"""
        match = Patterns.DATE.search("2026/02/04")
        assert match is not None
    
    def test_date_pattern_dot(self):
        """날짜 패턴 - 점 구분자"""
        match = Patterns.DATE.search("2026.02.04")
        assert match is not None
    
    def test_time_pattern(self):
        """시간 패턴"""
        match = Patterns.TIME.search("09:12")
        assert match is not None
        assert match.group("h") == "09"
        assert match.group("min") == "12"
    
    def test_time_pattern_with_seconds(self):
        """시간 패턴 - 초 포함"""
        match = Patterns.TIME.search("09:12:33")
        assert match is not None
        assert match.group("s") == "33"
    
    def test_weight_kg_pattern(self):
        """중량 패턴"""
        match = Patterns.WEIGHT_KG.search("12,340 kg")
        assert match is not None
        assert match.group("num") == "12,340"
        assert match.group("unit") in ["kg", "KG"]
    
    def test_vehicle_no_pattern(self):
        """차량번호 패턴"""
        match = Patterns.VEHICLE_NO.search("80구8713")
        assert match is not None
        assert match.group("prefix") == "80"
        assert match.group("hangul") == "구"
        assert match.group("suffix") == "8713"


# 전처리 규칙 테스트
class TestPreprocessRules:
    
    def test_execution_order_defined(self):
        assert len(PreprocessRules.EXECUTION_ORDER) > 0
        assert PreprocessRules.COLLAPSED_WHITESPACE in PreprocessRules.EXECUTION_ORDER
        assert PreprocessRules.STANDARDIZED_LABELS in PreprocessRules.EXECUTION_ORDER
    
    def test_whitespace_first(self):
        assert PreprocessRules.EXECUTION_ORDER[0] == PreprocessRules.COLLAPSED_WHITESPACE
    
    def test_all_rules_in_order(self):
        expected_rules = [
            PreprocessRules.COLLAPSED_WHITESPACE,
            PreprocessRules.NORMALIZED_PUNCTUATION_SPACING,
            PreprocessRules.NORMALIZED_CHARACTER_VISUAL_NOISE,
            PreprocessRules.STANDARDIZED_LABELS,
            PreprocessRules.CONVERTED_KOREAN_TIME,
            PreprocessRules.MERGED_SPLIT_NUMBERS,
            PreprocessRules.SPLIT_DATE_SUFFIX,
            PreprocessRules.PRESERVED_AMBIGUOUS_TAIL,
            PreprocessRules.SPLIT_VEHICLE_TAIL_KEYWORD,
            PreprocessRules.NORMALIZED_COORDINATES,
            PreprocessRules.REMOVED_SYMBOL_LINES,
        ]
        assert PreprocessRules.EXECUTION_ORDER == expected_rules


# 상수 테스트
class TestConstants:
    
    def test_max_weight_normalization_iterations(self):
        """중량 정규화 최대 반복"""
        assert Constants.MAX_WEIGHT_NORMALIZATION_ITERATIONS == 10
    
    def test_label_bonus_score(self):
        """라벨 가산점"""
        assert Constants.LABEL_BONUS_SCORE == 15
    
    def test_encoding(self):
        """기본 인코딩"""
        assert Constants.DEFAULT_ENCODING == "utf-8"
    
    def test_json_indent(self):
        """JSON 들여쓰기"""
        assert Constants.JSON_INDENT == 2