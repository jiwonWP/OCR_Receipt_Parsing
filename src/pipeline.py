from __future__ import annotations
from typing import Tuple

from .loader import load_ocr_json
from .preprocessor import preprocess
from .extractor import extract_candidates
from .schema import PreprocessedDocument, ExtractedCandidates


def run_preprocess_pipeline(input_path: str) -> PreprocessedDocument:
    # Loader -> Preprocessor 파이프라인 실행
    raw_doc = load_ocr_json(input_path)
    preprocessed = preprocess(raw_doc.raw_text)
    return preprocessed

def run_extract_pipeline(input_path: str) -> ExtractedCandidates:
    # Loader -> Preprocessor -> Extractor 파이프라인 실행
    preprocessed = run_preprocess_pipeline(input_path)
    extracted = extract_candidates(preprocessed)
    return extracted


def run_full_pipeline(input_path: str) -> Tuple[PreprocessedDocument, ExtractedCandidates]:
    # 전처리 산출물 + 후보 수집 산출물을 함께 반환
    preprocessed = run_preprocess_pipeline(input_path)
    extracted = extract_candidates(preprocessed)
    return preprocessed, extracted