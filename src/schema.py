from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class RawDocument:
    """
    Loader의 출력 모델
    - raw_text는 OCR 원문 그대로 보존해야 하므로 Loader/Preprocessor 어디에서도 덮어쓰지 않는다.
    """
    source_path: str
    raw_text: str
    meta: Dict = field(default_factory=dict)


@dataclass
class PreprocessedDocument:
    """
    Preprocessor의 출력 모델
    - normalized_text: 전처리 결과 텍스트
    - applied_rules: 실제로 텍스트를 바꾼 규칙만 기록(감사 로그)
    - warnings: doc_seq/raw_tail 같은 '애매함' 발견 시 기록(삭제/확정 대신 보존)
    """
    raw_text: str
    normalized_text: str
    applied_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class ExtractionMetadata:
    """
    필드별 추출 근거 메타데이터
    - field: 어떤 필드인지
    - strategy_used: 어떤 추출 전략이 사용되었는지
    - raw_match: 추출에 사용된 원문 매칭 문자열
    - normalized_match: 추출에 사용된 정규화 후 매칭 문자열
    - source_line_index: 근거가 된 원문 라인 인덱스 (0-based)
    - confidence: 추출 신뢰도 (0.0 ~ 1.0)        
    - is_imputed: 값이 추출된 것이 아니라 복구/계산된 것인지 여부
    - notes: 추가 설명 또는 이력 기록
    """
    field: str
    strategy_used: str 
    raw_match: str = ""
    normalized_match: str = ""
    source_line_index: int = -1
    confidence: float = 1.0
    is_imputed: bool = False
    notes: str = ""

@dataclass
class Candidate:
    """
    Extractor가 "후보"를 수집하기 위한 최소 단위.
    - field: 어떤 필드 후보인지(예: "date", "time", "gross_weight_kg", "vehicle_no")
    - value_raw: 추출된 값(원문/정규화 전 문자열 그대로)
    - source_line: 근거가 되는 원문 라인(디버깅/감사 목적)
    - method: "label" | "pattern" (라벨 기반 우선, 패턴은 fallback)
    - score: 후보 우선순위(라벨>패턴 같은 단순 정책부터 시작)
    """
    field: str
    value_raw: str
    source_line: str
    method: str
    score: int = 0
    meta: Dict = field(default_factory=dict)


@dataclass
class ExtractedCandidates:
    """
    Extractor의 출력 모델
    - raw_text / normalized_text는 그대로 보존(파이프라인 추적용)
    - candidates: 필드별 후보 리스트(확정 전 상태)
    - warnings: 추출 단계에서의 애매함(예: 라벨 미발견, 패턴 과다 매칭 등)
    """
    raw_text: str
    normalized_text: str
    candidates: List[Candidate] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """
    의미가 확정된 최종 파싱 결과를 표현하는 모델
    - 실패하거나 애매한 경우는 warnings / errors에 반드시 기록
    """
    date: Optional[str] = None           # YYYY-MM-DD
    time: Optional[str] = None           # HH:MM
    vehicle_no: Optional[str] = None

    gross_weight_kg: Optional[int] = None
    tare_weight_kg: Optional[int] = None
    net_weight_kg: Optional[int] = None

    parse_warnings: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    imputation_notes: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)