from __future__ import annotations

import re

# 날짜
# 예시:2026-02-04 / 2026.02.04 / 2026/2/4 / 26-2-4
DATE_PATTERN = re.compile(
    r"\b(?P<y>\d{2,4})[.\-\/](?P<m>\d{1,2})[.\-\/](?P<d>\d{1,2})\b"
)

# 시간
# 예시: 09:12 / 9:12 / 09:12:33 / 9:12:33
TIME_PATTERN = re.compile(
    r"\b(?P<h>\d{1,2}):(?P<min>\d{2})(?::(?P<s>\d{2}))?\b"
)

# 무게
# kg 주변 숫자를 후보로 수집.(kg이 실제로 붙은 경우 위주)
# 예시: 12,340 kg / 12340kg / 12340 KG / 12 340 kg 
WEIGHT_KG_PATTERN = re.compile(
    r"(?P<num>\d[\d,\s]*\d|\d)\s*(?P<unit>kg|KG|Kg|kG)\b"
)

# 차량번호
# 차량번호는 케이스가 많아 완벽한 정규식보다 후보를 넓게 수집하는 휴리스틱 패턴 사용
# 예시: 12가3456 / 123가4567 / 서울12가3456 
VEHICLE_NO_PATTERN = re.compile(
    r"\b(?:[가-힣]{1,4}\s*)?(?P<prefix>\d{2,3})\s*(?P<hangul>[가-힣])\s*(?P<suffix>\d{4})\b"
)
# 숫자만 있는 단순 형태도 후보로 수집
VEHICLE_NO_SIMPLE = re.compile(r"\b\d{4}\b")

# 라벨 기반 추출 
# 라벨 토큰 고정해둬 extractor에서 사용
LABEL_TOKENS = {
    # 무게
    "gross_weight": ["총중량", "총 중량", "총  중량"],
    "tare_weight": ["차중량", "차 중량", "공차", "공 차", "공차중량"],
    "net_weight": ["실중량", "실 중량", "적재중량", "적 재 중량"],

    # 날짜/시간
    "date": ["일자", "날짜", "DATE"],
    "time": ["시간", "TIME"],

    # 차량 번호
    "vehicle_no": ["차량번호", "차량 번호", "차 번", "차량No", "차량 NO"],
}

def find_all(pattern: re.Pattern, text: str):
    return list(pattern.finditer(text)) # 모든 매칭 결과 반환
