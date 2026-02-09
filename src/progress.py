from __future__ import annotations

import sys
from typing import Optional, List


class ProgressBar:
    
    def __init__(
        self,
        total: int,
        prefix: str = "",
        suffix: str = "",
        width: int = 50,
        fill: str = "█",
        empty: str = "░"
    ):
        
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.width = width
        self.fill = fill
        self.empty = empty
        self.current = 0
    
    def update(self, step: int = 1) -> None:
        """진행 상황 업데이트"""
        self.current += step
        self.render()
    
    def render(self) -> None:
        """프로그레스 바 렌더링"""
        if self.total == 0:
            return
        
        percent = min(100, int(100 * self.current / self.total))
        filled_width = int(self.width * self.current / self.total)
        
        bar = self.fill * filled_width + self.empty * (self.width - filled_width)
        
        output = f"\r{self.prefix} |{bar}| {percent}% {self.suffix}"
        
        sys.stdout.write(output)
        sys.stdout.flush()
        
        # 완료 시 줄바꿈
        if self.current >= self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()
    
    def finish(self) -> None:
        """진행 완료"""
        self.current = self.total
        self.render()


class StepProgress:
    
    def __init__(self, steps: List[str]):

        self.steps = steps
        self.current_step = 0
        self.total_steps = len(steps)
    
    def start_step(self, step_index: int) -> None:
        """단계 시작"""
        if 0 <= step_index < self.total_steps:
            self.current_step = step_index
            step_name = self.steps[step_index]
            print(f"\n[{step_index + 1}/{self.total_steps}] {step_name}")
    
    def finish_step(self) -> None:
        """현재 단계 완료"""
        if self.current_step < self.total_steps:
            step_name = self.steps[self.current_step]
            print(f"  ✓ {step_name} 완료")


class Spinner:
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "처리 중..."):

        self.message = message
        self.frame_index = 0
        self.running = False
    
    def tick(self) -> None:
        """스피너 업데이트"""
        frame = self.FRAMES[self.frame_index]
        sys.stdout.write(f"\r{frame} {self.message}")
        sys.stdout.flush()
        
        self.frame_index = (self.frame_index + 1) % len(self.FRAMES)
    
    def clear(self) -> None:
        """스피너 제거"""
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()


# 유틸리티 함수
def print_section_header(title: str, width: int = 60) -> None:
    """섹션 헤더 출력"""
    border = "=" * width
    print(f"\n{border}")
    print(f"{title:^{width}}")
    print(f"{border}")


def print_subsection_header(title: str, width: int = 60) -> None:
    """서브섹션 헤더 출력"""
    border = "-" * width
    print(f"\n{title}")
    print(border)


def print_summary_table(
    headers: List[str],
    rows: List[List[str]],
    column_widths: Optional[List[int]] = None
) -> None:
    
    if not rows:
        return
    
    # 컬럼 너비 계산
    if column_widths is None:
        column_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            column_widths.append(max_width + 2)
    
    # 헤더 출력
    header_line = " | ".join(
        header.ljust(width) for header, width in zip(headers, column_widths)
    )
    print(header_line)
    print("-" * len(header_line))
    
    # 데이터 행 출력
    for row in rows:
        row_line = " | ".join(
            str(cell).ljust(width) for cell, width in zip(row, column_widths)
        )
        print(row_line)


def print_key_value(key: str, value: str, indent: int = 2) -> None:
    """키-값 쌍 출력"""
    indent_str = " " * indent
    print(f"{indent_str}{key}: {value}")


def print_bullet_list(items: List[str], indent: int = 2, bullet: str = "•") -> None:
    """불릿 리스트 출력"""
    indent_str = " " * indent
    for item in items:
        print(f"{indent_str}{bullet} {item}")


def print_status(
    symbol: str,
    status: str,
    detail: str = "",
    color: Optional[str] = None
) -> None:

    if color:
        output = f"{color}{symbol} {status}"
        if detail:
            output += f": {detail}"
        output += "\033[0m"
    else:
        output = f"{symbol} {status}"
        if detail:
            output += f": {detail}"
    
    print(f"  {output}")


# 색상 상수
class Colors:
    """ANSI 색상 코드"""
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"