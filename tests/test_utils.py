"""
utils.py 모듈 단위 테스트
- format_weight_kg: 중량 포맷팅
- summarize_candidates: 후보 요약 통계
- compute_weight_relation_summary: 중량 관계식 요약
"""
import pytest
from src.utils import (
    format_weight_kg,
    summarize_candidates,
    compute_weight_relation_summary,
)


# 중량 포맷팅 함수 테스트
class TestFormatWeightKg:
    
    def test_format_simple_integer(self):
        """단순 정수 포맷팅"""
        assert format_weight_kg(12340) == "12,340 kg"
        assert format_weight_kg(5010) == "5,010 kg"
    
    def test_format_large_number(self):
        """큰 숫자 포맷팅"""
        assert format_weight_kg(1234567) == "1,234,567 kg"
    
    def test_format_zero(self):
        """0 포맷팅"""
        assert format_weight_kg(0) == "0 kg"
    
    def test_format_none(self):
        """None 입력"""
        assert format_weight_kg(None) == "(없음)"
    
    def test_format_string_number(self):
        """문자열 숫자 입력"""
        assert format_weight_kg("12340") == "12,340 kg"
    
    def test_format_invalid_value(self):
        """유효하지 않은 값"""
        result = format_weight_kg("invalid")
        assert result == "invalid"  # str(value) 반환


# 후보 요약 통계 함수 테스트
class TestSummarizeCandidates:
    
    def test_empty_candidates(self):
        """빈 후보 리스트"""
        result = summarize_candidates([])
        
        assert result["counts"]["total"] == 0
        assert result["counts"]["by_field"] == {}
        assert result["counts"]["by_method"] == {}
        assert result["top_by_field"] == {}
    
    def test_single_candidate(self, sample_candidates_list):
        """단일 필드 후보"""
        candidates = [sample_candidates_list[0]] 
        result = summarize_candidates(candidates)
        
        assert result["counts"]["total"] == 1
        assert result["counts"]["by_field"]["date"] == 1
        assert result["counts"]["by_method"]["label"] == 1
    
    def test_multiple_fields(self, sample_candidates_list):
        """여러 필드 후보"""
        result = summarize_candidates(sample_candidates_list)
        
        assert result["counts"]["total"] == 5
        assert result["counts"]["by_field"]["date"] == 2
        assert result["counts"]["by_field"]["gross_weight_kg"] == 1
        assert result["counts"]["by_field"]["tare_weight_kg"] == 1
        assert result["counts"]["by_field"]["net_weight_kg"] == 1
    
    def test_method_count(self, sample_candidates_list):
        """방법별 카운트"""
        result = summarize_candidates(sample_candidates_list)
        
        assert result["counts"]["by_method"]["label"] == 4
        assert result["counts"]["by_method"]["pattern"] == 1
    
    def test_top_by_field_sorting(self):
        """필드별 상위 후보 정렬 (score 내림차순)"""
        candidates = [
            {"field": "date", "value_raw": "2026-02-01", "method": "pattern", "score": 5, "source_line": "line1"},
            {"field": "date", "value_raw": "2026-02-02", "method": "label", "score": 10, "source_line": "line2"},
            {"field": "date", "value_raw": "2026-02-03", "method": "pattern", "score": 3, "source_line": "line3"},
        ]
        result = summarize_candidates(candidates)
        
        top_dates = result["top_by_field"]["date"]
        assert len(top_dates) == 3
        assert top_dates[0]["value_raw"] == "2026-02-02" 
        assert top_dates[1]["value_raw"] == "2026-02-01"  
        assert top_dates[2]["value_raw"] == "2026-02-03"
    
    def test_top_by_field_limit_3(self):
        """필드별 상위 3개만 반환"""
        candidates = [
            {"field": "weight", "value_raw": f"{i}", "method": "pattern", "score": i, "source_line": ""}
            for i in range(10, 0, -1)  
        ]
        result = summarize_candidates(candidates)
        
        top_weights = result["top_by_field"]["weight"]
        assert len(top_weights) == 3  
        assert top_weights[0]["value_raw"] == "10" 


# 중량 관계식 요약 함수 테스트
class TestComputeWeightRelationSummary:
    
    def test_exact_match(self):
        """정확히 일치하는 경우"""
        result = compute_weight_relation_summary(
            gross=12480,
            tare=7470,
            net=5010
        )
        assert "12,480 - 7,470 = 5,010 [일치]" == result
    
    def test_mismatch(self):
        """불일치하는 경우"""
        result = compute_weight_relation_summary(
            gross=12480,
            tare=7470,
            net=5500  # 실제는 5010이어야 함
        )
        assert "12,480 - 7,470 = 5,500 [불일치 (계산=5,010kg)]" == result
    
    def test_gross_none(self):
        """총중량 None"""
        result = compute_weight_relation_summary(
            gross=None,
            tare=7470,
            net=5010
        )
        assert result == "(중량 정보 불완전)"
    
    def test_tare_none(self):
        """차중량 None"""
        result = compute_weight_relation_summary(
            gross=12480,
            tare=None,
            net=5010
        )
        assert result == "(중량 정보 불완전)"
    
    def test_net_none(self):
        """실중량 None"""
        result = compute_weight_relation_summary(
            gross=12480,
            tare=7470,
            net=None
        )
        assert result == "(중량 정보 불완전)"
    
    def test_all_none(self):
        """모두 None"""
        result = compute_weight_relation_summary(
            gross=None,
            tare=None,
            net=None
        )
        assert result == "(중량 정보 불완전)"
    
    def test_invalid_type(self):
        """유효하지 않은 타입"""
        result = compute_weight_relation_summary(
            gross="invalid",
            tare=7470,
            net=5010
        )
        assert result == "(중량 계산 실패)"