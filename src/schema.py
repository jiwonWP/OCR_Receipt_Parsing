from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

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



class ParseResult(BaseModel):
    """
      의미가 확정된 최종 파싱 결과를 표현하는 모델
    - 실패하거나 애매한 경우는 warnings / errors에 반드시 기록
    """

    # 기본 식별 정보   
    date: Optional[str] = Field(
        None, description="계근 일자 (ISO 형식: YYYY-MM-DD)"
    )
    time: Optional[str] = Field(
        None, description="계근 시간 (HH:MM)"
    )
    vehicle_no: Optional[str] = Field(
        None, description="차량 번호"
    )

    # 중량 정보
    gross_weight_kg: Optional[int] = Field(
        None, description="총중량 (kg)"
    )
    tare_weight_kg: Optional[int] = Field(
        None, description="공차중량 (kg)"
    )
    net_weight_kg: Optional[int] = Field(
        None, description="실중량 (kg)"
    )

    # 파싱/검증 상태
    parse_warnings: List[str] = Field(
        default_factory=list,
        description="정규화/파싱 과정에서 발생한 경고"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="비즈니스 규칙 위반 등 치명적 검증 오류"
    )

    # 근거
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="각 필드가 어떤 후보로부터 확정되었는지에 대한 근거 정보"
    )