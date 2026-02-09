from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터"""
    
    COLORS = {
        'DEBUG': '\033[36m',      
        'INFO': '\033[32m',       
        'WARNING': '\033[33m',    
        'ERROR': '\033[31m',    
        'CRITICAL': '\033[35m',  
        'RESET': '\033[0m',      
    }
    
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(
    name: str = "ocr_pipeline",
    log_dir: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_color: bool = True
) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) 
    logger.handlers.clear() 
    
    # 1) 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    if enable_color:
        console_format = "%(levelname)s | %(message)s"
        console_formatter = ColoredFormatter(console_format)
    else:
        console_format = "%(levelname)-8s | %(message)s"
        console_formatter = logging.Formatter(console_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 2) 파일 핸들러
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명: pipeline_YYYYMMDD_HHMMSS.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(file_level)
        
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"로그 파일: {log_file}")
    
    return logger


def get_logger(name: str = "ocr_pipeline") -> logging.Logger:

    return logging.getLogger(name)



# 로그 헬퍼 함수
class LogContext:
    
    def __init__(self, logger: logging.Logger, message: str, level: int = logging.INFO):
 
        self.logger = logger
        self.message = message
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        """컨텍스트 진입"""
        self.start_time = datetime.now()
        self.logger.log(self.level, f"▶ {self.message} 시작...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log(self.level, f"✓ {self.message} 완료 ({elapsed:.2f}초)")
        else:
            self.logger.error(f"✗ {self.message} 실패 ({elapsed:.2f}초): {exc_val}")
        
        return False


def log_step(logger: logging.Logger, message: str, level: int = logging.INFO):

    return LogContext(logger, message, level)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str = ""
) -> None:

    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        logger.error(f"{context}: {error_type} - {error_msg}")
    else:
        logger.error(f"{error_type}: {error_msg}")
    
    logger.debug("스택 트레이스:", exc_info=True)