# -*- coding: utf-8 -*-
"""
[프로젝트] 피의 양자정보공학과
시스템 모듈: UI 연출, 타이핑 효과, 상태 관리, 트리거 검사, 수사 수첩
작성자: 최선우
"""

import os
import sys
import time
from game_data import CLUES_DB, SUSPECTS

# Windows 콘솔 인코딩 및 ANSI 활성화
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
if hasattr(sys.stdin, 'reconfigure'):
    try: sys.stdin.reconfigure(encoding='utf-8')
    except Exception: pass
os.system('')

RESET, BOLD = "\033[0m", "\033[1m"
CYAN, YELLOW, GREEN, RED, WHITE, GRAY = "\033[96m", "\033[93m", "\033[92m", "\033[91m", "\033[97m", "\033[90m"

try:
    import msvcrt
except ImportError:
    msvcrt = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(title):
    print(f"\n{CYAN}{'=' * 60}{RESET}")
    print(f" {BOLD}{WHITE}> {title}{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}\n")

def draw_divider():
    print(f"{GRAY}{'-' * 60}{RESET}")

def print_slow(text, delay=0.04):
    skip = False
    for ch in text:
        if not skip and msvcrt and msvcrt.kbhit():
            msvcrt.getch()
            skip = True
        sys.stdout.write(ch)
        sys.stdout.flush()
        if not skip:
            time.sleep(0.22 if ch in ('.', '!', '?') else delay)
    print()

def select_option(title, options, subtitle=None, allow_cancel=True):
    while True:
        clear_screen()
        draw_header(title)
        if subtitle:
            print(f" {YELLOW}* {subtitle}{RESET}\n")
        for i, opt in enumerate(options, start=1):
            print(f"  {CYAN}[{i}]{RESET} {opt}")
        if allow_cancel:
            print(f"  {GRAY}[0] 이전으로 돌아가기{RESET}")
        draw_divider()

        try:
            choice = input(f" {BOLD}선택 번호 입력 >> {RESET}").strip()
            if allow_cancel and choice == '0':
                return -1
            if choice.isdigit():
                val = int(choice)
                if 1 <= val <= len(options):
                    return val - 1
            print(f" {RED}올바른 번호를 입력하세요.{RESET}")
            time.sleep(0.5)
        except (KeyboardInterrupt, EOFError):
            return -1

class GameState:
    def __init__(self):
        self.clues = {}
        self.broken_suspects = set()
        self.searched_spots = set()
        self.solved_deductions = set()
        self.dialogue_logs = {suspect_id: [] for suspect_id in SUSPECTS}
        self.unlock_clue("c_autopsy", quiet=True)

    def has_clue(self, clue_id):
        return clue_id in self.clues

    def unlock_clue(self, clue_id, quiet=False):
        if clue_id and clue_id in CLUES_DB and clue_id not in self.clues:
            self.clues[clue_id] = CLUES_DB[clue_id]
            if not quiet:
                print(f" {YELLOW}{BOLD}★ [새로운 단서 획득: {self.clues[clue_id]['name']}] ★{RESET}")
                print(f" {GRAY}  {self.clues[clue_id]['desc']}{RESET}\n")

    def can_ask(self, required_clue):
        # 트리거 검사 시스템: 단서 요구 조건 충족 여부 확인
        return required_clue is None or self.has_clue(required_clue)

    def can_confront(self, suspect_id):
        # 용의자 추궁은 관련 결정적 단서를 모았을 때만 활성화
        s = SUSPECTS.get(suspect_id)
        return s and self.has_clue(s["break_clue"])

    def show_notebook(self):
        while True:
            opts = [
                f"[증거 DB] 수집된 핵심 단서 ({len(self.clues)}/{len(CLUES_DB)}건)",
                "[인물 정보] 용의자 4인 신상 및 알리바이 현황",
                "[사건 개요] 사건 기본 개요 및 현장 정보"
            ]
            sel = select_option("수사 수첩 (INVESTIGATION NOTEBOOK)", opts)
            if sel == -1: break
            clear_screen()
            if sel == 0:
                draw_header(f"수사 수첩 ─ 증거 데이터베이스 ({len(self.clues)}건)")
                for idx, (cid, item) in enumerate(self.clues.items(), start=1):
                    print(f" {CYAN}[단서 {idx}] {YELLOW}{BOLD}{item['name']}{RESET}")
                    print(f"   {WHITE}{item['desc']}{RESET}\n")
            elif sel == 1:
                draw_header("수사 수첩 ─ 용의자 4인 현황")
                for sid, s in SUSPECTS.items():
                    status = f"{GREEN}[알리바이 격파됨]{RESET}" if sid in self.broken_suspects else f"{RED}[알리바이 주장 중]{RESET}"
                    print(f" - {WHITE}{BOLD}{s['name']}{RESET} ({s['role']}) : {status}")
                    print(f"   주장: \"{s['alibi']}\"\n")
            elif sel == 2:
                draw_header("수사 수첩 ─ 사건 개요")
                print(f" - 사건명: XX대학교 양자정보공학과 주임교수 살인사건")
                print(f" - 피해자: 강성훈 교수 (52세) / 사인: 액체질소 누출로 인한 산소결핍 질식사")
                print(f" - 현장상태: 카드키로 잠긴 밀실, 산소 비상 센서 수동 차단됨")
            draw_divider()
            input(f"\n{CYAN}[Enter 키를 누르면 수첩 메뉴로 돌아갑니다...]{RESET}")
