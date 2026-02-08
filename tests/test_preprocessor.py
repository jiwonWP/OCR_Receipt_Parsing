"""
preprocessor.py 모듈 단위 테스트
- 전처리 규칙별 정규화 함수 테스트
- preprocess() 통합 테스트
"""
import pytest
from src.preprocessor import (
    normalize_whitespace,
    normalize_punctuation_spacing,
    normalize_label_variants,
    normalize_korean_time_format,
    normalize_number_grouping_before_unit,
    normalize_date_suffix,
    normalize_datetime_trailing_garbage,
    normalize_vehicle_value_noise,
    normalize_line_noise,
    preprocess,
)


# 공백 정규화 테스트
class TestNormalizeWhitespace:
    
    def test_collapse_multiple_spaces(self):
        """연속 공백 축소"""
        result = normalize_whitespace("hello    world")
        assert result.text == "hello world"
        assert result.changed is True
    
    def test_trim_line_spaces(self):
        """라인 좌우 공백 제거"""
        result = normalize_whitespace("  hello  \n  world  ")
        assert result.text == "hello\nworld"
        assert result.changed is True
    
    def test_tab_to_space(self):
        """탭을 공백으로 변환"""
        result = normalize_whitespace("hello\t\tworld")
        assert result.text == "hello world"
        assert result.changed is True

# 구두점 공백 정규화 테스트
class TestNormalizePunctuationSpacing:
    
    def test_colon_spacing(self):
        """콜론 주변 공백 제거"""
        result = normalize_punctuation_spacing("02 : 13")
        assert result.text == "02:13"
        assert result.changed is True
    
    def test_comma_spacing(self):
        """콤마 주변 공백 제거"""
        result = normalize_punctuation_spacing("37.7, 126.8")
        assert result.text == "37.7,126.8"
        assert result.changed is True
    
    def test_parentheses_spacing(self):
        """괄호 주변 공백 제거"""
        result = normalize_punctuation_spacing("( 09:09 )")
        assert result.text == "(09:09)"
        assert result.changed is True

# 라벨 표준화 테스트
class TestNormalizeLabelVariants:
    
    def test_date_label(self):
        """날짜 라벨 통일"""
        result = normalize_label_variants("날 짜: 2026-02-02")
        assert "날짜:" in result.text
        assert result.changed is True
    
    def test_vehicle_no_label(self):
        """차량번호 라벨 통일"""
        result = normalize_label_variants("차량 번호: 80구8713")
        assert "차량번호:" in result.text
        assert result.changed is True
        
        result = normalize_label_variants("차량 No.: 80구8713")
        assert "차량번호:" in result.text
    
    def test_weight_labels(self):
        """중량 라벨 통일"""
        result = normalize_label_variants("총 중 량: 12,480 kg")
        assert "총중량:" in result.text
        
        result = normalize_label_variants("공차 중량: 7,470 kg")
        assert "차중량:" in result.text
        
        result = normalize_label_variants("실 중 량: 5,010 kg")
        assert "실중량:" in result.text

# 한글 시간 정규화 테스트
class TestNormalizeKoreanTimeFormat:
    
    def test_korean_time(self):
        """한글 시간 -> 콜론 형식"""
        result = normalize_korean_time_format("11시 33분")
        assert result.text == "11:33"
        assert result.changed is True
    
    def test_single_digit_padding(self):
        """1자리 분 -> 0 패딩"""
        result = normalize_korean_time_format("9시 5분")
        assert result.text == "09:05"
        assert result.changed is True

# 숫자 결합 테스트
class TestNormalizeNumberGroupingBeforeUnit:
    
    def test_merge_split_numbers(self):
        """공백 분리된 숫자 결합"""
        result = normalize_number_grouping_before_unit("5 900 kg")
        assert result.text == "5,900 kg"
        assert result.changed is True
    
    def test_multiple_groups(self):
        """여러 그룹 결합"""
        result = normalize_number_grouping_before_unit("13 460 kg")
        assert result.text == "13,460 kg"
        assert result.changed is True
    
    def test_preserve_non_kg_numbers(self):
        """kg 앞이 아닌 숫자는 유지"""
        result = normalize_number_grouping_before_unit("02 : 13")
        # kg가 없으므로 변경 없음
        assert result.changed is False

# 날짜 suffix 분리 테스트
class TestNormalizeDateSuffix:
    
    def test_split_date_suffix(self):
        """날짜 뒤 suffix 분리"""
        result = normalize_date_suffix("2026-02-02-00004")
        assert "2026-02-02 doc_seq:00004" == result.text
        assert result.changed is True
        assert "found_date_suffix_doc_seq" in result.warnings

# 날짜 뒤 불명확 숫자 보존 테스트
class TestNormalizeDatetimeTrailingGarbage:

    def test_preserve_ambiguous_tail(self):
        """날짜 뒤 애매한 숫자 raw_tail로 보존"""
        result = normalize_datetime_trailing_garbage("2026-02-02 0016")
        assert "2026-02-02 raw_tail:0016" == result.text
        assert result.changed is True
        assert "found_ambiguous_date_tail" in result.warnings
    
    def test_do_not_touch_valid_timestamp(self):
        """정상 timestamp는 변경 안함"""
        result = normalize_datetime_trailing_garbage("2026-02-02 05:37:55")
        assert result.text == "2026-02-02 05:37:55"
        assert result.changed is False

# 차량번호 값 오염 분리 테스트
class TestNormalizeVehicleValueNoise:
    
    def test_split_vehicle_category(self):
        """차량번호에 붙은 입고/출고 분리"""
        result = normalize_vehicle_value_noise("차량번호: 5405 입고")
        assert "차량번호: 5405 구분:입고" in result.text
        assert result.changed is True

# 의미 없는 라인 제거 테스트
class TestNormalizeLineNoise:
    
    def test_remove_empty_lines(self):
        """빈 라인 제거"""
        result = normalize_line_noise("hello\n\n\nworld")
        assert result.text == "hello\nworld"
        assert result.changed is True
    
    def test_remove_symbol_only_lines(self):
        """기호만 있는 라인 제거"""
        result = normalize_line_noise("hello\n·····\nworld")
        assert result.text == "hello\nworld"
        assert result.changed is True


# 전처리 통합 함수 테스트
class TestPreprocess:
    
    def test_preprocess_raw_ocr_text(self, sample_raw_ocr_text):
        result = preprocess(sample_raw_ocr_text)
        
        # 원문 보존
        assert result.raw_text == sample_raw_ocr_text
        
        # 정규화 텍스트 생성
        assert result.normalized_text != sample_raw_ocr_text
        
        # 적용된 규칙 기록
        assert len(result.applied_rules) > 0
        
        # 정규화 확인
        assert "날 짜" not in result.normalized_text
        assert "날짜" in result.normalized_text
        
        assert "02 : 07" not in result.normalized_text 
        assert "02:07" in result.normalized_text
        
        assert "13 460 kg" not in result.normalized_text  
        assert "13,460 kg" in result.normalized_text
    
    def test_applied_rules_tracking(self):
        text = "날 짜: 2026-02-02    \n차량 번호: 80구8713"
        result = preprocess(text)
        
        # 공백 정규화 적용
        assert "collapsed_whitespace" in result.applied_rules
        
        # 라벨 표준화 적용
        assert "standardized_labels" in result.applied_rules
    
    def test_warnings_generation(self):
        text = "날짜: 2026-02-02-00004"
        result = preprocess(text)
        
        # doc_seq 발견 경고
        assert "found_date_suffix_doc_seq" in result.warnings
    
    def test_no_change_no_rule_applied(self):
        text = "hello world"
        result = preprocess(text)
        
        # 이미 정규화된 텍스트는 대부분 규칙 적용 안됨
        # 단, normalize_whitespace는 항상 적용될 수 있음 (trim 등)
        assert result.normalized_text == text or "collapsed_whitespace" in result.applied_rules