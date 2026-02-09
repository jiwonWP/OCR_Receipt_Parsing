import pytest
from pathlib import Path
import tempfile
import csv

from src.output_formatters import (
    FileNamingConvention,
    format_preprocess_log,
    format_extract_log,
    format_candidates_output,
    format_resolved_output,
    format_parsed_output,
    format_csv_row,
    write_summary_csv,
    get_output_files,
)


class TestFileNamingConvention:
    """파일명 규칙 테스트"""
    
    def test_preprocess_raw(self):
        """원문 파일명"""
        assert FileNamingConvention.preprocess_raw("sample_01") == "sample_01_raw.txt"
    
    def test_preprocess_normalized(self):
        """정규화 파일명"""
        assert FileNamingConvention.preprocess_normalized("sample_01") == "sample_01_normalized.txt"
    
    def test_preprocess_log(self):
        """전처리 로그 파일명"""
        assert FileNamingConvention.preprocess_log("sample_01") == "sample_01_preprocess_log.json"
    
    def test_extract_candidates(self):
        """후보 목록 파일명"""
        assert FileNamingConvention.extract_candidates("sample_01") == "sample_01_candidates.json"
    
    def test_extract_log(self):
        """추출 로그 파일명"""
        assert FileNamingConvention.extract_log("sample_01") == "sample_01_extract_log.json"
    
    def test_resolve_result(self):
        """후보 선택 결과 파일명"""
        assert FileNamingConvention.resolve_result("sample_01") == "sample_01_resolved.json"
    
    def test_parse_result(self):
        """파싱 결과 파일명"""
        assert FileNamingConvention.parse_result("sample_01") == "sample_01_parsed.json"
    
    def test_summary_csv(self):
        """요약 CSV 파일명"""
        assert FileNamingConvention.summary_csv() == "summary.csv"

# 출력 포맷팅 함수 테스트
class TestFormatFunctions:
    
    def test_format_preprocess_log(self):
        """전처리 로그 포맷"""
        result = format_preprocess_log(
            source="sample_01.json",
            applied_rules=["rule1", "rule2"],
            warnings=["warning1"],
            raw_line_count=45,
            normalized_line_count=38
        )
        
        assert result["source"] == "sample_01.json"
        assert result["applied_rules"] == ["rule1", "rule2"]
        assert result["warnings"] == ["warning1"]
        assert result["raw_line_count"] == 45
        assert result["normalized_line_count"] == 38
    
    def test_format_extract_log(self):
        """추출 로그 포맷"""
        summary = {
            "total": 10,
            "by_field": {"date": 3},
            "by_method": {"label": 5}
        }
        
        result = format_extract_log(
            source="sample_01.json",
            warnings=[],
            candidate_summary=summary
        )
        
        assert result["source"] == "sample_01.json"
        assert result["warnings"] == []
        assert result["candidate_summary"]["total"] == 10
    
    def test_format_candidates_output(self):
        """후보 목록 출력 포맷"""
        candidates = [
            {"field": "date", "value_raw": "2026-02-02"}
        ]
        
        result = format_candidates_output(
            source="sample_01.json",
            candidates=candidates
        )
        
        assert result["source"] == "sample_01.json"
        assert result["candidates"] == candidates
    
    def test_format_resolved_output(self):
        """후보 선택 결과 포맷"""
        resolved_fields = {
            "date_raw": "2026-02-02",
            "time_raw": "09:12"
        }
        evidence = {"date": {"selected_value": "2026-02-02"}}
        
        result = format_resolved_output(
            source="sample_01.json",
            resolved_fields=resolved_fields,
            evidence=evidence,
            warnings=[]
        )
        
        assert result["source"] == "sample_01.json"
        assert result["resolved_fields"]["date_raw"] == "2026-02-02"
        assert result["evidence"]["date"]["selected_value"] == "2026-02-02"
    
    def test_format_parsed_output(self):
        """파싱 결과 포맷"""
        result = format_parsed_output(
            source="sample_01.json",
            date="2026-02-02",
            time="09:12",
            vehicle_no="8713",
            gross_weight_kg=12480,
            tare_weight_kg=7470,
            net_weight_kg=5010,
            parse_warnings=[],
            validation_errors=[],
            imputation_notes=[],
            is_valid=True
        )
        
        assert result["source"] == "sample_01.json"
        assert result["date"] == "2026-02-02"
        assert result["time"] == "09:12"
        assert result["vehicle_no"] == "8713"
        assert result["gross_weight_kg"] == 12480
        assert result["is_valid"] is True

# CSV 포맷팅 함수 테스트
class TestCSVFormatting:
    
    def test_format_csv_row(self):
        """CSV 행 포맷"""
        parsed_data = {
            "source": "sample_01.json",
            "date": "2026-02-02",
            "time": "09:12",
            "vehicle_no": "8713",
            "gross_weight_kg": 12480,
            "tare_weight_kg": 7470,
            "net_weight_kg": 5010,
            "is_valid": True,
            "validation_errors": [],
            "parse_warnings": ["warning1"],
            "imputation_notes": ["note1", "note2"]
        }
        
        row = format_csv_row("sample_01.json", parsed_data)
        
        assert row["filename"] == "sample_01.json"
        assert row["date"] == "2026-02-02"
        assert row["time"] == "09:12"
        assert row["vehicle_no"] == "8713"
        assert row["gross_weight_kg"] == "12480"
        assert row["is_valid"] == "TRUE"
        assert row["validation_errors"] == ""
        assert row["parse_warnings"] == "warning1"
        assert row["imputation_notes"] == "note1; note2"
    
    def test_format_csv_row_with_none(self):
        """None 값 처리"""
        parsed_data = {
            "source": "sample_01.json",
            "date": None,
            "time": None,
            "vehicle_no": None,
            "gross_weight_kg": None,
            "tare_weight_kg": None,
            "net_weight_kg": None,
            "is_valid": False,
            "validation_errors": ["error1"],
            "parse_warnings": [],
            "imputation_notes": []
        }
        
        row = format_csv_row("sample_01.json", parsed_data)
        
        assert row["date"] == ""
        assert row["time"] == ""
        assert row["vehicle_no"] == ""
        assert row["is_valid"] == "FALSE"
        assert row["validation_errors"] == "error1"
    
    def test_write_summary_csv(self):
        """CSV 파일 쓰기"""
        rows = [
            {
                "filename": "sample_01.json",
                "date": "2026-02-02",
                "time": "09:12",
                "vehicle_no": "8713",
                "gross_weight_kg": "12480",
                "tare_weight_kg": "7470",
                "net_weight_kg": "5010",
                "is_valid": "TRUE",
                "validation_errors": "",
                "parse_warnings": "",
                "imputation_notes": ""
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            write_summary_csv(output_path, rows)
            
            # 파일 존재 확인
            assert output_path.exists()
            
            # 내용 확인
            with output_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_rows = list(reader)
                
                assert len(csv_rows) == 1
                assert csv_rows[0]["filename"] == "sample_01.json"
                assert csv_rows[0]["date"] == "2026-02-02"
    
    def test_write_summary_csv_empty(self):
        """빈 리스트 처리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            write_summary_csv(output_path, [])
            
            assert not output_path.exists()

# 출력 파일 목록 반환 함수 테스트
class TestGetOutputFiles:
    
    def test_get_output_files(self):
        """산출물 목록 반환"""
        files = get_output_files("sample_01")
        
        assert len(files) == 7
        assert "sample_01_raw.txt" in files
        assert "sample_01_normalized.txt" in files
        assert "sample_01_preprocess_log.json" in files
        assert "sample_01_candidates.json" in files
        assert "sample_01_extract_log.json" in files
        assert "sample_01_resolved.json" in files
        assert "sample_01_parsed.json" in files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])