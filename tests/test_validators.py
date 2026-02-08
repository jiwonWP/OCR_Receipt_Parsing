"""
validators.py 모듈 단위 테스트
- validate_and_recover: 도메인 검증 및 실중량 복구
"""
import pytest
from src.validators import validate_and_recover, ValidationResult


# 도메인 검증 및 복구 함수 테스트
class TestValidateAndRecover:
    
    def test_all_valid_no_recovery(self):
        """모든 필드 정상, 복구 불필요"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5010,
        )
        
        assert result.is_valid is True
        assert result.net_weight_kg == 5010
        assert len(result.validation_errors) == 0
        assert len(result.imputation_notes) == 0
    
    def test_net_weight_imputation(self):
        """실중량 누락 -> 계산으로 복구"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=None,  
        )
        
        assert result.is_valid is True
        assert result.net_weight_kg == 5010  # 12480 - 7470
        assert len(result.validation_errors) == 0
        assert len(result.imputation_notes) == 1
        assert "imputed:net_weight=5010" in result.imputation_notes[0]
    
    def test_missing_required_field_date(self):
        """필수 필드 누락: 날짜"""
        result = validate_and_recover(
            date=None,
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5010,
        )
        
        assert result.is_valid is False
        assert "missing_required_field:date" in result.validation_errors
    
    def test_missing_required_field_vehicle_no(self):
        """필수 필드 누락: 차량번호"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no=None,  
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5010,
        )
        
        assert result.is_valid is False
        assert "missing_required_field:vehicle_no" in result.validation_errors
    
    def test_negative_gross_weight(self):
        """음수 총중량"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=-1000, 
            tare_weight_kg=7470,
            net_weight_kg=5010,
        )
        
        assert result.is_valid is False
        assert any("negative_weight:gross=" in e for e in result.validation_errors)
    
    def test_negative_net_weight(self):
        """음수 실중량"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=-100, 
        )
        
        assert result.is_valid is False
        assert any("negative_weight:net=" in e for e in result.validation_errors)
    
    def test_unrealistic_weight(self):
        """비현실적 중량 (100톤 초과)"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=150000, 
            tare_weight_kg=7470,
            net_weight_kg=5010,
        )
        
        assert result.is_valid is False
        assert any("unrealistic_weight:gross=" in e for e in result.validation_errors)
    
    def test_invalid_weight_relation_gross_less_than_tare(self):
        """총중량 < 차중량"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=5000,
            tare_weight_kg=7470,
            net_weight_kg=100,
        )
        
        assert result.is_valid is False
        assert any("invalid_weight_relation" in e for e in result.validation_errors)
    
    def test_weight_mismatch_outside_tolerance(self):
        """중량 관계 불일치 (허용 오차 초과)"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5500,  
        )
        
        assert result.is_valid is False
        assert any("weight_mismatch" in e for e in result.validation_errors)
    
    def test_weight_mismatch_within_tolerance(self):
        """중량 관계 허용 오차 내 (통과)"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5050,
        )
        
        assert result.is_valid is True
        assert result.net_weight_kg == 5050
    
    def test_recovery_by_candidates_net_missing(self):
        """후보 기반 실중량 복구 (gross, tare 고정 -> net 찾기)"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=14080,
            tare_weight_kg=13950,
            net_weight_kg=None,  
            weight_candidates_kg=[14080, 13950, 130],  
        )
        
        assert result.is_valid is True
        assert result.net_weight_kg == 130  
        assert len(result.imputation_notes) == 1
    
    def test_recovery_by_candidates_mismatch_repair(self):
        """후보 기반 중량 불일치 복구"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=14080,
            tare_weight_kg=13950,
            net_weight_kg=5000,  
            weight_candidates_kg=[14080, 13950, 130], 
        )
        
        # 복구 성공하면 valid
        assert result.is_valid is True
        assert result.net_weight_kg == 130
        assert len(result.imputation_notes) == 1
        assert "recovered:net=130" in result.imputation_notes[0]
    
    def test_no_candidates_no_recovery(self):
        """후보 없으면 복구 불가"""
        result = validate_and_recover(
            date="2026-02-02",
            time="09:12",
            vehicle_no="80구8713",
            gross_weight_kg=14080,
            tare_weight_kg=13950,
            net_weight_kg=5000, 
            weight_candidates_kg=None,  
        )
        
        assert result.is_valid is False
        assert any("weight_mismatch" in e for e in result.validation_errors)
    
    def test_optional_fields_can_be_none(self):
        """선택 필드는 None 허용 (시간, 중량)"""
        result = validate_and_recover(
            date="2026-02-02",
            time=None,  
            vehicle_no="80구8713",
            gross_weight_kg=None,  
            tare_weight_kg=None,
            net_weight_kg=None,
        )
        
        # 필수 필드만 있으면 valid
        assert result.is_valid is True
        assert result.net_weight_kg is None