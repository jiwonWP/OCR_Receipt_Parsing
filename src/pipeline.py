from .loader import load_ocr_json
from .preprocessor import preprocess
from .schema import PreprocessedDocument


def run_preprocess_pipeline(input_path: str) -> PreprocessedDocument:
    # Loader -> Preprocessor 파이프라인 실행
    raw_doc = load_ocr_json(input_path)
    preprocessed = preprocess(raw_doc.raw_text)
    return preprocessed
