from __future__ import annotations

import traceback
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


# 커스텀 예외 클래스
class PipelineError(Exception):
    """파이프라인 기본 예외"""
    pass


class FileReadError(PipelineError):
    """파일 읽기 실패"""
    pass


class PreprocessError(PipelineError):
    """전처리 단계 실패"""
    pass


class ExtractError(PipelineError):
    """추출 단계 실패"""
    pass


class ResolveError(PipelineError):
    """후보 선택 단계 실패"""
    pass


class ValidationError(PipelineError):
    """검증 실패"""
    pass


class OutputError(PipelineError):
    """출력 생성 실패"""
    pass


# 에러 정보 데이터 클래스
@dataclass
class ErrorInfo:
    error_type: str
    error_message: str
    context: str
    traceback_str: Optional[str] = None
    recoverable: bool = False
    recovery_action: Optional[str] = None


# 에러 핸들러
class ErrorHandler:
    
    def __init__(self, logger=None):
        self.logger = logger
        self.errors: List[ErrorInfo] = []
    
    def handle_error(
        self,
        error: Exception,
        context: str = "",
        recoverable: bool = False,
        recovery_action: Optional[str] = None
    ) -> ErrorInfo:

        error_info = ErrorInfo(
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            traceback_str=traceback.format_exc(),
            recoverable=recoverable,
            recovery_action=recovery_action
        )
        
        self.errors.append(error_info)
        
        if self.logger:
            if recoverable:
                self.logger.warning(f"복구 가능한 에러 [{context}]: {error_info.error_type} - {error_info.error_message}")
                if recovery_action:
                    self.logger.info(f"  복구 액션: {recovery_action}")
            else:
                self.logger.error(f"치명적 에러 [{context}]: {error_info.error_type} - {error_info.error_message}")
                self.logger.debug(f"스택 트레이스:\n{error_info.traceback_str}")
        
        return error_info
    
    def get_error_summary(self) -> Dict[str, Any]:
        """에러 요약 정보 반환"""
        total_errors = len(self.errors)
        recoverable_count = sum(1 for e in self.errors if e.recoverable)
        critical_count = total_errors - recoverable_count
        
        error_types = {}
        for error in self.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        return {
            "total": total_errors,
            "recoverable": recoverable_count,
            "critical": critical_count,
            "by_type": error_types,
        }
    
    def has_critical_errors(self) -> bool:
        """치명적 에러가 있는지 확인"""
        return any(not e.recoverable for e in self.errors)
    
    def clear_errors(self) -> None:
        """에러 목록 초기화"""
        self.errors.clear()
    
    def generate_error_report(self) -> str:
        """에러 리포트 생성"""
        if not self.errors:
            return "에러 없음"
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append("에러 리포트")
        lines.append("="*60)
        
        summary = self.get_error_summary()
        lines.append(f"\n총 에러: {summary['total']}개")
        lines.append(f"  - 복구 가능: {summary['recoverable']}개")
        lines.append(f"  - 치명적: {summary['critical']}개")
        
        lines.append(f"\n에러 유형별:")
        for error_type, count in summary['by_type'].items():
            lines.append(f"  - {error_type}: {count}개")
        
        lines.append("\n상세 내역:")
        lines.append("-"*60)
        
        for i, error in enumerate(self.errors, 1):
            lines.append(f"\n[{i}] {error.error_type}")
            lines.append(f"  컨텍스트: {error.context}")
            lines.append(f"  메시지: {error.error_message}")
            
            if error.recoverable:
                lines.append(f"  상태: 복구 가능")
                if error.recovery_action:
                    lines.append(f"  복구 액션: {error.recovery_action}")
            else:
                lines.append(f"  상태: 치명적")
            
            if error.traceback_str:
                tb_lines = error.traceback_str.strip().split("\n")
                if len(tb_lines) > 5:
                    lines.append(f"  스택 트레이스: (마지막 3줄)")
                    for line in tb_lines[-3:]:
                        lines.append(f"    {line}")
                else:
                    lines.append(f"  스택 트레이스:")
                    for line in tb_lines:
                        lines.append(f"    {line}")
        
        lines.append("\n" + "="*60)
        
        return "\n".join(lines)


# 에러 복구 유틸리티
def safe_execute(
    func,
    *args,
    default=None,
    error_handler: Optional[ErrorHandler] = None,
    context: str = "",
    **kwargs
):

    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.handle_error(
                error=e,
                context=context or f"함수 실행: {func.__name__}",
                recoverable=True,
                recovery_action=f"기본값 반환: {default}"
            )
        return default


def retry_on_error(
    func,
    *args,
    max_retries: int = 3,
    error_handler: Optional[ErrorHandler] = None,
    context: str = "",
    **kwargs
):

    last_error = None
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            
            if error_handler:
                error_handler.handle_error(
                    error=e,
                    context=f"{context} (시도 {attempt + 1}/{max_retries})",
                    recoverable=(attempt < max_retries - 1),
                    recovery_action=f"재시도 {attempt + 2}/{max_retries}" if attempt < max_retries - 1 else None
                )
            
            if attempt == max_retries - 1:
                raise last_error
    
    raise last_error