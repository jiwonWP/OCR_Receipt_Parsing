import pytest
from src.schemas import (
    validate_preprocess_log,
    validate_candidates_output,
    validate_resolved_output,
    validate_parsed_output,
    get_empty_preprocess_log,
    get_empty_extract_log,
    get_empty_resolved_output,
    get_empty_parsed_output,
)

# 스키마 검증 함수 테스트
class TestValidationFunctions:
    
    def test_validate_preprocess_log_valid(self):
        """유효한 전처리 로그"""
        data = {
            "source": "test.json",
            "applied_rules": ["rule1"],
            "warnings": [],
            "raw_line_count": 10,
            "normalized_line_count": 8
        }
        
        assert validate_preprocess_log(data) is True
    
    def test_validate_preprocess_log_missing_field(self):
        """필수 필드 누락"""
        data = {
            "source": "test.json",
            "applied_rules": ["rule1"],
            # warnings 누락
            "raw_line_count": 10,
            "normalized_line_count": 8
        }
        
        assert validate_preprocess_log(data) is False
    
    def test_validate_candidates_output_valid(self):
        """유효한 후보 출력"""
        data = {
            "source": "test.json",
            "candidates": [
                {
                    "field": "date",
                    "value_raw": "2026-02-02",
                    "method": "label",
                    "score": 90,
                    "source_line": "날짜: 2026-02-02"
                }
            ]
        }
        
        assert validate_candidates_output(data) is True
    
    def test_validate_candidates_output_missing_source(self):
        """source 필드 누락"""
        data = {
            "candidates": []
        }
        
        assert validate_candidates_output(data) is False
    
    def test_validate_candidates_output_invalid_candidate(self):
        """후보 필수 필드 누락"""
        data = {
            "source": "test.json",
            "candidates": [
                {
                    "field": "date",
                    # value_raw 누락
                    "method": "label",
                    "score": 90,
                    "source_line": "날짜: 2026-02-02"
                }
            ]
        }
        
        assert validate_candidates_output(data) is False
    
    def test_validate_resolved_output_valid(self):
        """유효한 후보 선택 결과"""
        data = {
            "source": "test.json",
            "resolved_fields": {},
            "evidence": {},
            "warnings": []
        }
        
        assert validate_resolved_output(data) is True
    
    def test_validate_resolved_output_missing_field(self):
        """필수 필드 누락"""
        data = {
            "source": "test.json",
            "resolved_fields": {},
            # evidence 누락
            "warnings": []
        }
        
        assert validate_resolved_output(data) is False
    
    def test_validate_parsed_output_valid(self):
        """유효한 파싱 결과"""
        data = {
            "source": "test.json",
            "date": "2026-02-02",
            "time": "09:12",
            "vehicle_no": "8713",
            "gross_weight_kg": 12480,
            "tare_weight_kg": 7470,
            "net_weight_kg": 5010,
            "parse_warnings": [],
            "validation_errors": [],
            "imputation_notes": [],
            "is_valid": True
        }
        
        assert validate_parsed_output(data) is True
    
    def test_validate_parsed_output_missing_field(self):
        """필수 필드 누락"""
        data = {
            "source": "test.json",
            "date": "2026-02-02",
            # time 누락
            "vehicle_no": "8713",
            "gross_weight_kg": 12480,
            "tare_weight_kg": 7470,
            "net_weight_kg": 5010,
            "parse_warnings": [],
            "validation_errors": [],
            "imputation_notes": [],
            "is_valid": True
        }
        
        assert validate_parsed_output(data) is False

# 출력 템플릿 함수 테스트
class TestEmptyTemplates:
    
    def test_get_empty_preprocess_log(self):
        """빈 전처리 로그 템플릿"""
        result = get_empty_preprocess_log("test.json")
        
        assert result["source"] == "test.json"
        assert result["applied_rules"] == []
        assert result["warnings"] == []
        assert result["raw_line_count"] == 0
        assert result["normalized_line_count"] == 0
        
        # 스키마 검증 통과
        assert validate_preprocess_log(result) is True
    
    def test_get_empty_extract_log(self):
        """빈 추출 로그 템플릿"""
        result = get_empty_extract_log("test.json")
        
        assert result["source"] == "test.json"
        assert result["warnings"] == []
        assert result["candidate_summary"]["total"] == 0
    
    def test_get_empty_resolved_output(self):
        """빈 후보 선택 출력 템플릿"""
        result = get_empty_resolved_output("test.json")
        
        assert result["source"] == "test.json"
        assert result["resolved_fields"]["date_raw"] is None
        assert result["evidence"] == {}
        assert result["warnings"] == []
        
        # 스키마 검증 통과
        assert validate_resolved_output(result) is True
    
    def test_get_empty_parsed_output(self):
        """빈 파싱 결과 출력 템플릿"""
        result = get_empty_parsed_output("test.json")
        
        assert result["source"] == "test.json"
        assert result["date"] is None
        assert result["time"] is None
        assert result["vehicle_no"] is None
        assert result["gross_weight_kg"] is None
        assert result["tare_weight_kg"] is None
        assert result["net_weight_kg"] is None
        assert result["parse_warnings"] == []
        assert result["validation_errors"] == []
        assert result["imputation_notes"] == []
        assert result["is_valid"] is False
        
        # 스키마 검증 통과
        assert validate_parsed_output(result) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])