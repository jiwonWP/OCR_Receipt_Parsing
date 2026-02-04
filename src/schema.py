from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class RawDocument:
    """
    Loader의 출력 모델.
    - raw_text는 OCR 원문 그대로 보존해야 하므로 Loader/Preprocessor 어디에서도 덮어쓰지 않는다.
    """
    source_path: str
    raw_text: str
    meta: Dict = field(default_factory=dict)


@dataclass
class PreprocessedDocument:
    """
    Preprocessor의 출력 모델.
    - normalized_text: 전처리 결과 텍스트
    - applied_rules: 실제로 텍스트를 바꾼 규칙만 기록(감사 로그)
    - warnings: doc_seq/raw_tail 같은 '애매함' 발견 시 기록(삭제/확정 대신 보존)
    """
    raw_text: str
    normalized_text: str
    applied_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
