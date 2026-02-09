import pytest
from src.normalizers import normalize_weight_kg, normalize_time, normalize_date


# 중량 정규화 함수 테스트
class TestNormalizeWeightKg:
    
    def test_simple_integer(self):
        """단순 정수 입력"""
        assert normalize_weight_kg("12340") == 12340
        assert normalize_weight_kg("5010") == 5010
    
    def test_comma_separated(self):
        """천단위 콤마 포함"""
        assert normalize_weight_kg("12,340") == 12340
        assert normalize_weight_kg("5,010") == 5010
        assert normalize_weight_kg("1,234,567") == 1234567
    
    def test_with_kg_suffix(self):
        """kg 접미사 포함"""
        assert normalize_weight_kg("12340 kg") == 12340
        assert normalize_weight_kg("12,340kg") == 12340
        assert normalize_weight_kg("12,340 KG") == 12340
        assert normalize_weight_kg("12,340 Kg") == 12340
    
    def test_with_parentheses(self):
        """괄호로 감싸진 경우"""
        assert normalize_weight_kg("(12,340)") == 12340
        assert normalize_weight_kg("(12340 kg)") == 12340
        assert normalize_weight_kg("(12,340 kg)") == 12340
    
    def test_ocr_space_separated(self):
        """OCR 공백 분리 (천단위)"""
        assert normalize_weight_kg("12 340") == 12340
        assert normalize_weight_kg("5 010") == 5010
        assert normalize_weight_kg("1 234 567") == 1234567
    
    def test_mixed_format(self):
        """복합 형식"""
        assert normalize_weight_kg("  12,340 kg  ") == 12340
        # 전처리 단계에서 "12 340 kg" -> "12,340 kg"로 변환됨
        # normalizer는 이미 변환된 형태를 받음
        assert normalize_weight_kg("(12,340 kg)") == 12340
        assert normalize_weight_kg("12,340 kg") == 12340
    
    def test_multiple_numbers_prefer_comma(self):
        """여러 숫자가 있을 때 콤마 포함 우선"""
        # "02:07 13,460 kg" -> 13460 선택 (콤마 포함)
        assert normalize_weight_kg("02:07 13,460 kg") == 13460
    
    def test_multiple_numbers_prefer_longest(self):
        """여러 숫자 중 콤마 없으면 가장 긴 것 선택"""
        assert normalize_weight_kg("02 13 7560 kg") == 7560
    
    def test_none_input(self):
        """None 입력"""
        assert normalize_weight_kg(None) is None
    
    def test_empty_string(self):
        """빈 문자열"""
        assert normalize_weight_kg("") is None
        assert normalize_weight_kg("   ") is None
    
    def test_no_digits(self):
        """숫자가 없는 경우"""
        assert normalize_weight_kg("kg") is None
        assert normalize_weight_kg("중량") is None
        assert normalize_weight_kg("N/A") is None
    
    def test_zero_weight(self):
        """0 중량"""
        assert normalize_weight_kg("0") == 0
        assert normalize_weight_kg("0 kg") == 0


# 시간 정규화 함수 테스트
class TestNormalizeTime:
    
    def test_standard_hhmm(self):
        """표준 HH:MM 형식"""
        assert normalize_time("09:12") == "09:12"
        assert normalize_time("23:59") == "23:59"
        assert normalize_time("00:00") == "00:00"
    
    def test_single_digit_hour_minute(self):
        """1자리 시/분 -> 0 패딩"""
        assert normalize_time("9:12") == "09:12"
        assert normalize_time("9:5") == "09:05"
        assert normalize_time("1:1") == "01:01"
    
    def test_with_spaces_around_colon(self):
        """콜론 주변 공백"""
        assert normalize_time("09 : 12") == "09:12"
        assert normalize_time("9 :5") == "09:05"
    
    def test_korean_format(self):
        """한글 시간 형식 (11시 33분)"""
        assert normalize_time("11시 33분") == "11:33"
        assert normalize_time("9시 5분") == "09:05"
        assert normalize_time("11시33분") == "11:33"
    
    def test_korean_no_minute_char(self):
        """'분' 생략 (11시 33)"""
        assert normalize_time("11시 33") == "11:33"
    
    def test_with_parentheses(self):
        """괄호로 감싸진 경우"""
        assert normalize_time("(09:12)") == "09:12"
        assert normalize_time("(11시 33분)") == "11:33"
    
    def test_invalid_hour(self):
        """유효하지 않은 시간 (24시 이상)"""
        assert normalize_time("25:00") is None
        assert normalize_time("24:00") is None 
    
    def test_invalid_minute(self):
        """유효하지 않은 분 (60분 이상)"""
        assert normalize_time("09:60") is None
        assert normalize_time("09:99") is None
    
    def test_none_input(self):
        """None 입력"""
        assert normalize_time(None) is None
    
    def test_empty_string(self):
        """빈 문자열"""
        assert normalize_time("") is None
        assert normalize_time("   ") is None
    
    def test_no_time_pattern(self):
        """시간 패턴이 없는 경우"""
        assert normalize_time("시간") is None
        assert normalize_time("12340") is None


# normalize_date 테스트 (날짜 정규화)

class TestNormalizeDate:
    
    def test_standard_iso_format(self):
        """표준 ISO 형식 (YYYY-MM-DD)"""
        date, warn = normalize_date("2026-02-02")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_single_digit_month_day(self):
        """1자리 월/일 -> 0 패딩"""
        date, warn = normalize_date("2026-2-4")
        assert date == "2026-02-04"
        assert warn is None
    
    def test_slash_separator(self):
        """슬래시 구분자 (YYYY/MM/DD)"""
        date, warn = normalize_date("2026/02/02")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_dot_separator(self):
        """점 구분자 (YYYY.MM.DD)"""
        date, warn = normalize_date("2026.02.02")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_mixed_separators(self):
        """혼합 구분자"""
        date, warn = normalize_date("2026.02-02")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_compact_yyyymmdd(self):
        """압축 형식 (YYYYMMDD)"""
        date, warn = normalize_date("20260202")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_with_suffix_tail(self):
        """날짜 뒤 suffix (doc_seq 형태)"""
        date, warn = normalize_date("2026-02-02-00004")
        assert date == "2026-02-02"
        assert warn == "ambiguous_date_tail"
    
    def test_with_doc_seq_tag(self):
        """전처리 결과 doc_seq 태그 포함"""
        date, warn = normalize_date("2026-02-02 doc_seq:00004")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_with_raw_tail_tag(self):
        """전처리 결과 raw_tail 태그 포함"""
        date, warn = normalize_date("2026-02-02 raw_tail:0016")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_with_parentheses(self):
        """괄호로 감싸진 경우"""
        date, warn = normalize_date("(2026-02-02)")
        assert date == "2026-02-02"
        assert warn is None
    
    def test_invalid_month(self):
        """유효하지 않은 월 (13월 이상)"""
        date, warn = normalize_date("2026-13-01")
        assert date is None
        assert warn == "date_parse_failed"
    
    def test_invalid_day(self):
        """유효하지 않은 일 (32일 이상)"""
        date, warn = normalize_date("2026-02-32")
        assert date is None
        assert warn == "date_parse_failed"
    
    def test_invalid_leap_year(self):
        """윤년이 아닌 해의 2월 29일"""
        date, warn = normalize_date("2025-02-29")
        assert date is None
        assert warn == "date_parse_failed"
    
    def test_valid_leap_year(self):
        """윤년의 2월 29일"""
        date, warn = normalize_date("2024-02-29")
        assert date == "2024-02-29"
        assert warn is None
    
    def test_none_input(self):
        """None 입력"""
        date, warn = normalize_date(None)
        assert date is None
        assert warn == "date_parse_failed"
    
    def test_empty_string(self):
        """빈 문자열"""
        date, warn = normalize_date("")
        assert date is None
        assert warn == "date_parse_failed"
    
    def test_no_date_pattern(self):
        """날짜 패턴이 없는 경우"""
        date, warn = normalize_date("날짜")
        assert date is None
        assert warn == "date_parse_failed"