import re
from dataclasses import dataclass
from typing import Callable, List

from .schema import PreprocessedDocument


@dataclass
class RuleResult:
    text: str
    changed: bool
    warnings: List[str]


def _apply_rule(
    text: str,
    rule_name: str,
    fn: Callable[[str], RuleResult], # 정규화 함수
    applied_rules: List[str], # 적용된 규칙 기록용 리스트
    warnings: List[str],   # 경고 기록용 리스트
) -> str:
    
    before = text
    result = fn(text)
    
    # 규칙이 실제로 텍스트를 변경한 경우에만 적용 기록에 추가
    if result.changed and before != result.text:
        applied_rules.append(rule_name)

    warnings.extend(result.warnings)

    return result.text


def normalize_whitespace(text: str) -> RuleResult:
    """
    - 탭/연속 공백을 단일 공백으로 축소
    - 각 라인의 좌우 공백 trim
    - 개행 구조 유지
    """
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        line2 = re.sub(r"[ \t]+", " ", line).strip()
        new_lines.append(line2)
    new_text = "\n".join(new_lines)
    return RuleResult(text=new_text, changed=(new_text != text), warnings=[])


def normalize_punctuation_spacing(text: str) -> RuleResult:
    """
    - 시간 콜론 주변 공백 제거:  '02 : 13' -> '02:13'
    - 콤마 주변 공백 제거(좌표 등): '37.7, 126.8' -> '37.7,126.8'
    - 괄호 주변 공백 제거: '( 09:09 )' -> '(09:09)'
    """
    t = text
    t = re.sub(r"\s*:\s*", ":", t)
    t = re.sub(r"\s*,\s*", ",", t)
    t = re.sub(r"\s*\(\s*", "(", t)
    t = re.sub(r"\s*\)\s*", ")", t)
    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_character_visual_noise(text: str) -> RuleResult:
    """
    숫자와 시각적으로 유사한 문자 보정
    - 날짜/시간/중량 근처에서만 O->0, I/l->1 치환
    """
    warnings = []
    t = text
    changed = False
    
    # 날짜 패턴 내 O -> 0 치환
    def fix_date(m: re.Match) -> str:
        corrected = m.group(0).replace('O', '0').replace('o', '0')
        if corrected != m.group(0):
            changed= True
            if "found_visual_noise_correction" not in warnings:  
                warnings.append("found_visual_noise_correction")
        return corrected
    
    t = re.sub(r'\d{4}[-./][O\do]{1,2}[-./][O\do]{1,2}', fix_date, t)
    
    # kg 근처 숫자 내 O -> 0, I/l -> 1 치환
    def fix_weight(m: re.Match) -> str:
        nonlocal changed
        num = m.group('num')
        corrected = num.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1')
        if corrected != num:
            changed = True
            if "found_visual_noise_correction" not in warnings:
                warnings.append("found_visual_noise_correction")
        return corrected + ' ' + m.group('unit')
    
    t = re.sub(r'(?P<num>[\dOolI,\s]+)\s*(?P<unit>kg|KG)', fix_weight, t)
    
    return RuleResult(text=t, changed=changed, warnings=warnings)


def normalize_label_variants(text: str) -> RuleResult:
    """
    라벨 내부 공백/깨짐을 표준 라벨로 통일한다.
    - '날 짜' -> '날짜'
    - '총 중 량' -> '총중량'
    - '실 중 량' -> '실중량'
    - '차량 No.' -> '차량번호'
    """
    t = text

    # 날짜
    t = re.sub(r"날\s*짜", "날짜", t)
    t = re.sub(r"계량\s*일자", "날짜", t)
    t = re.sub(r"일\s*시", "날짜", t)

    # 차량번호
    t = re.sub(r"차량\s*번호", "차량번호", t)
    t = re.sub(r"차번호", "차량번호", t)
    t = re.sub(r"차량\s*No\.?", "차량번호", t)

    # 중량 (공차중량/차중량은 '차중량'으로 통일)
    t = re.sub(r"총\s*중\s*량", "총중량", t)
    t = re.sub(r"공차\s*중량", "차중량", t)
    t = re.sub(r"차\s*중\s*량", "차중량", t)
    t = re.sub(r"실\s*중\s*량", "실중량", t)

    # 구분
    t = re.sub(r"구\s*분", "구분", t)

    # 계량횟수
    t = re.sub(r"계량\s*횟수", "계량횟수", t)

    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_korean_time_format(text: str) -> RuleResult:
    """
    한글 시간 '11시 33분' -> '11:33' 로 통일
    - 1자리 분은 0 패딩: '11시 3분' -> '11:03'
    """
    def repl(m: re.Match) -> str:
        hh = int(m.group(1))
        mm = int(m.group(2))
        return f"{hh:02d}:{mm:02d}"

    t = re.sub(r"(\d{1,2})\s*시\s*(\d{1,2})\s*분", repl, text)
    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_number_grouping_before_unit(text: str) -> RuleResult:
    """
    OCR에서 천 단위 콤마가 공백으로 깨지는 문제를 'kg' 근처에서만 결합
    예) '5 900 kg' -> '5,900 kg'
    모든 숫자 공백 결합은 위험하므로 'kg' 앞에서만 처리
    """
    t = text
    pattern = re.compile(r"(\d{1,3})\s+(\d{3})\s*(kg)")
    while True:
        new_t = pattern.sub(r"\1,\2 \3", t)
        if new_t == t:
            break
        t = new_t

    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_date_suffix(text: str) -> RuleResult:
    """
    날짜가 'YYYY-MM-DD-00004'처럼 suffix가 붙는 경우 분리+보존한다.
    - '2026-02-02-00004' -> '2026-02-02 doc_seq:00004'
    """
    warnings = []
    t, n = re.subn(r"(\d{4}-\d{2}-\d{2})-(\d+)", r"\1 doc_seq:\2", text)
    if n > 0:
        warnings.append("found_date_suffix_doc_seq")
    return RuleResult(text=t, changed=(t != text), warnings=warnings)


def normalize_datetime_trailing_garbage(text: str) -> RuleResult:
    """
    날짜 뒤에 붙은 콜론 없는 숫자 꼬리(0016, 5 등)를 시간으로 확정하지 않고 raw_tail로 보존한다.
    - '2026-02-02 0016' -> '2026-02-02 raw_tail:0016'
    정상 timestamp(콜론 포함)는 변경하지 않음
    """
    warnings = []

    # (?!:) 만으로는 '05:37:55' 같은 시간 문자열이 숫자로 매칭될 수 있음
    # 공백 뒤 1~4자리 숫자 + (공백/줄끝) 형태의 숫자 단독 토큰만 raw_tail 처리
    def repl(m: re.Match) -> str:
        warnings.append("found_ambiguous_date_tail")
        return f"{m.group(1)} raw_tail:{m.group(2)}"

    # 날짜 + 공백 + (1~4자리 숫자) + (줄끝 또는 공백) / 단, 바로 뒤에 ':'가 오면 제외
    t = re.sub(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,4})(?=\s|$)(?!:)", repl, text)

    return RuleResult(text=t, changed=(t != text), warnings=warnings)


def normalize_vehicle_value_noise(text: str) -> RuleResult:
    #차량번호 값에 '입고/출고'가 붙는 값 -> 구분 라벨로 분리

    t = re.sub(r"(차량번호\s*:\s*)(\S+)\s*(입고|출고)", r"\1\2 구분:\3", text)
    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_coordinates(text: str) -> RuleResult:
    """
    좌표를 'lat,lon' 형태로 통일
    예) '37.718114, 126.844940' -> '37.718114,126.844940'
    """
    t = re.sub(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", r"\1,\2", text)
    return RuleResult(text=t, changed=(t != text), warnings=[])


def normalize_line_noise(text: str) -> RuleResult:
    """
    의미 없는 기호-only 라인을 제거
    - 공백 제거 후 길이 0 / '·' 또는 ',' 반복 특수문자만 존재
    """
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        compact = re.sub(r"\s+", "", line)
        if compact == "":
            continue
        if re.fullmatch(r"[·,]+", compact):
            continue
        new_lines.append(line)
    new_text = "\n".join(new_lines)
    return RuleResult(text=new_text, changed=(new_text != text), warnings=[])


def preprocess(raw_text: str) -> PreprocessedDocument:

    applied_rules: List[str] = []
    warnings: List[str] = []

    t = raw_text

    # 정규화 규칙 적용 
    t = _apply_rule(t, "collapsed_whitespace", normalize_whitespace, applied_rules, warnings)
    t = _apply_rule(t, "normalized_punctuation_spacing", normalize_punctuation_spacing, applied_rules, warnings)
    t = _apply_rule(t, "normalized_character_visual_noise", normalize_character_visual_noise, applied_rules, warnings)
    
    t = _apply_rule(t, "standardized_labels", normalize_label_variants, applied_rules, warnings)
    t = _apply_rule(t, "converted_korean_time_to_colon_format", normalize_korean_time_format, applied_rules, warnings)
    t = _apply_rule(t, "merged_split_numbers_before_kg", normalize_number_grouping_before_unit, applied_rules, warnings)
    t = _apply_rule(t, "split_date_suffix_to_doc_seq", normalize_date_suffix, applied_rules, warnings)
    t = _apply_rule(t, "preserved_ambiguous_date_tail_as_raw_tail", normalize_datetime_trailing_garbage, applied_rules, warnings)
    t = _apply_rule(t, "split_vehicle_tail_keyword_as_category", normalize_vehicle_value_noise, applied_rules, warnings)
    t = _apply_rule(t, "normalized_coordinates", normalize_coordinates, applied_rules, warnings)
    t = _apply_rule(t, "removed_symbol_only_lines", normalize_line_noise, applied_rules, warnings)

    return PreprocessedDocument(
        raw_text=raw_text,
        normalized_text=t,
        applied_rules=applied_rules,
        warnings=warnings,
    )