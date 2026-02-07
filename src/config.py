"""
OCR 파싱 파이프라인 설정 및 정책 상수
"""
from __future__ import annotations
import re
from typing import Dict, List

# ============================================================================
# 검증 정책 (Validator)
# ============================================================================

class ValidationPolicy:
    """도메인 검증 정책"""
    
    # 중량 오차 허용 범위
    MIN_TOLERANCE_KG = 10  # 최소 허용 오차 (kg)
    TOLERANCE_PERCENT = 0.02  # 허용 오차 비율 (2%)
    
    # 중량 범위
    MAX_REALISTIC_WEIGHT_KG = 100000  # 비현실적 중량 상한 (100톤)
    
    # 필수 필드
    REQUIRED_FIELDS = ["date", "vehicle_no"]
    
    @staticmethod
    def get_tolerance(expected: int) -> int:
        """
        오차 허용 범위 계산
        +,-10kg 또는 +,-2% 중 큰 값
        """
        return max(
            ValidationPolicy.MIN_TOLERANCE_KG,
            int(expected * ValidationPolicy.TOLERANCE_PERCENT)
        )


# ============================================================================
# 라벨 토큰 (Extractor)
# ============================================================================

class LabelTokens:
    """OCR 텍스트에서 필드를 식별하기 위한 라벨 토큰"""
    
    # 중량
    GROSS_WEIGHT = ["총중량", "총 중량", "총  중량"]
    TARE_WEIGHT = ["차중량", "차 중량", "공차", "공 차", "공차중량"]
    NET_WEIGHT = ["실중량", "실 중량", "적재중량", "적 재 중량"]
    
    # 날짜/시간
    DATE = ["일자", "날짜", "DATE"]
    TIME = ["시간", "TIME"]
    
    # 차량번호
    VEHICLE_NO = ["차량번호", "차량 번호", "차 번", "차량No", "차량 NO"]
    
    @classmethod
    def as_dict(cls) -> Dict[str, List[str]]:
        """딕셔너리 형태로 반환 (하위 호환성)"""
        return {
            "gross_weight": cls.GROSS_WEIGHT,
            "tare_weight": cls.TARE_WEIGHT,
            "net_weight": cls.NET_WEIGHT,
            "date": cls.DATE,
            "time": cls.TIME,
            "vehicle_no": cls.VEHICLE_NO,
        }


# ============================================================================
# 정규식 패턴 (Extractor / Normalizer)
# ============================================================================

class Patterns:
    """OCR 텍스트 파싱을 위한 정규식 패턴"""
    
    # 날짜 패턴
    # 예: 2026-02-04 / 2026.02.04 / 2026/2/4 / 26-2-4
    DATE = re.compile(
        r"\b(?P<y>\d{2,4})[.\-\/](?P<m>\d{1,2})[.\-\/](?P<d>\d{1,2})\b"
    )
    
    # 시간 패턴
    # 예: 09:12 / 9:12 / 09:12:33 / 9:12:33
    TIME = re.compile(
        r"\b(?P<h>\d{1,2}):(?P<min>\d{2})(?::(?P<s>\d{2}))?\b"
    )
    
    # 중량 패턴 (kg 단위)
    # 예: 12,340 kg / 12340kg / 12340 KG / 12 340 kg
    WEIGHT_KG = re.compile(
        r"(?<![:\d])(?P<num>\d[\d,\s]*\d|\d)\s*(?P<unit>kg|KG|Kg|kG)\b"
    )
    
    # 차량번호 패턴 (전형적 형태)
    # 예: 12가3456 / 123가4567 / 서울12가3456
    VEHICLE_NO = re.compile(
        r"\b(?:[가-힣]{1,4}\s*)?(?P<prefix>\d{2,3})\s*(?P<hangul>[가-힣])\s*(?P<suffix>\d{4})\b"
    )
    
    # 차량번호 패턴 (단순 4자리 - fallback)
    VEHICLE_NO_SIMPLE = re.compile(r"\b\d{4}\b")


# ============================================================================
# 전처리 규칙 순서 (Preprocessor)
# ============================================================================

class PreprocessRules:
    """전처리 규칙 적용 순서 및 규칙명 상수"""
    
    # 규칙명 상수
    COLLAPSED_WHITESPACE = "collapsed_whitespace"
    NORMALIZED_PUNCTUATION_SPACING = "normalized_punctuation_spacing"
    NORMALIZED_CHARACTER_VISUAL_NOISE = "normalized_character_visual_noise"
    STANDARDIZED_LABELS = "standardized_labels"
    CONVERTED_KOREAN_TIME = "converted_korean_time_to_colon_format"
    MERGED_SPLIT_NUMBERS = "merged_split_numbers_before_kg"
    SPLIT_DATE_SUFFIX = "split_date_suffix_to_doc_seq"
    PRESERVED_AMBIGUOUS_TAIL = "preserved_ambiguous_date_tail_as_raw_tail"
    SPLIT_VEHICLE_TAIL_KEYWORD = "split_vehicle_tail_keyword_as_category"
    NORMALIZED_COORDINATES = "normalized_coordinates"
    REMOVED_SYMBOL_LINES = "removed_symbol_only_lines"
    
    # 적용 순서 (preprocess_spec.md 명세 순서)
    EXECUTION_ORDER = [
        COLLAPSED_WHITESPACE,
        NORMALIZED_PUNCTUATION_SPACING,
        NORMALIZED_CHARACTER_VISUAL_NOISE,
        STANDARDIZED_LABELS,
        CONVERTED_KOREAN_TIME,
        MERGED_SPLIT_NUMBERS,
        SPLIT_DATE_SUFFIX,
        PRESERVED_AMBIGUOUS_TAIL,
        SPLIT_VEHICLE_TAIL_KEYWORD,
        NORMALIZED_COORDINATES,
        REMOVED_SYMBOL_LINES,
    ]


# ============================================================================
# 기타 상수
# ============================================================================

class Constants:
    """기타 파이프라인 상수"""
    
    # Normalizer
    MAX_WEIGHT_NORMALIZATION_ITERATIONS = 10  # 중량 정규화 최대 반복
    
    # Extractor
    LABEL_BONUS_SCORE = 15  # 라벨 토큰이 같은 줄에 있을 때 가산점
    
    # 파일 출력
    DEFAULT_ENCODING = "utf-8"
    JSON_INDENT = 2