# -*- coding: utf-8 -*-
"""
[프로젝트] 피의 양자정보공학과 (Blood in Quantum Info)
메인 모듈: 게임 루프, 현장 조사, 용의자 심문, 협력자 공조, 최종 보고서
작성자: 최선우
"""

import time
from game_data import GAME_TITLE, INTRO_BRIEFING, SCENE_SPOTS, SUSPECTS, COLLABORATORS, REPORT_DATA, EPILOGUE_TEXT, DEDUCTIONS
from game_system import (
    GameState, clear_screen, draw_header, draw_divider,
    print_slow, select_option, CYAN, YELLOW, GREEN, RED, WHITE, BOLD, RESET
)

def show_intro():
    clear_screen()
    draw_header(f"{GAME_TITLE} ─ 사건 브리핑")
    for line in INTRO_BRIEFING:
        print_slow(line)
    input(f"\n{CYAN}[Enter 키를 누르면 수사 본부로 이동합니다...]{RESET}")

def investigate_scene(state):
    while True:
        opts = [f"{s['name']} " + (f"{GREEN}[수색완료]{RESET}" if s["id"] in state.searched_spots else f"{YELLOW}[미수색]{RESET}") for s in SCENE_SPOTS]
        sel = select_option("사건 현장 조사 ─ 제2종합연구동 4층 특수실험실", opts)
        if sel == -1: break
        spot = SCENE_SPOTS[sel]
        clear_screen()
        draw_header(f"현장 정밀 감식 ─ {spot['name']}")
        print(f" {WHITE}{spot['desc']}{RESET}\n")
        inspection = select_option("현장 흔적 분석 ─ 가장 타당한 조사 방향은?", spot["choices"])
        if inspection == -1:
            continue
        if inspection == spot["answer"]:
            state.searched_spots.add(spot["id"])
            state.unlock_clue(spot["clue"])
        else:
            print(f"\n {RED}관찰만으로는 증거를 확정할 수 없습니다. 흔적과 사건 기록을 다시 살펴보십시오.{RESET}")
        draw_divider()
        input(f"\n{CYAN}[Enter 키를 누르면 현장 목록으로 돌아갑니다...]{RESET}")

def show_interrogation_log(suspect, entries, animate_last=False):
    clear_screen()
    draw_header(f"심문 대화 로그 ─ {suspect['name']}")
    for index, (speaker, reaction, text) in enumerate(entries):
        if speaker == "수사관":
            prefix = f" {CYAN}[수사관]{RESET} "
        else:
            prefix = f" {YELLOW}[{suspect['name']} / {reaction}]{RESET} "
        if animate_last and index == len(entries) - 1:
            print_slow(f"{prefix}{text}")
        else:
            print(f"{prefix}{text}")
    draw_divider()

def interrogate_suspect(state, sid):
    suspect = SUSPECTS[sid]
    dialogue_log = state.dialogue_logs[sid]
    while True:
        status = f"{GREEN}[알리바이 격파됨]{RESET}" if sid in state.broken_suspects else f"{RED}[알리바이 주장 중]{RESET}"
        opts, q_indices = [], []
        for idx, (title, _, req_clue, _) in enumerate(suspect["questions"]):
            if state.can_ask(req_clue):
                opts.append(f"[질문] {title}")
                q_indices.append((idx, True))
            else:
                opts.append(f"{RED}[잠김] 심화 질문 (관련 단서 필요){RESET}")
                q_indices.append((idx, False))

        confront_ready = state.can_confront(sid)
        if sid in state.broken_suspects:
            opts.append(f"{GREEN}[추궁완료] 거짓말 입증됨{RESET}")
        elif confront_ready:
            opts.append(f"{YELLOW}[모순추궁] 모순 추궁하기 (수집 단서 제시){RESET}")
        else:
            opts.append(f"{RED}[추궁불가] 결정적 반박 단서 미확보{RESET}")
        opts.append("[대화 로그] 지금까지의 문답 다시 보기")

        sel = select_option(f"심문실 ─ {suspect['name']} ({suspect['role']}) {status}", opts, subtitle=f"주장: \"{suspect['alibi']}\"")
        if sel == -1: break
        elif sel < len(q_indices):
            q_idx, unlocked = q_indices[sel]
            if not unlocked:
                clear_screen()
                print(f"\n {RED}단서가 부족합니다. 현장 조사나 협력자 면담을 먼저 진행하십시오.{RESET}")
                time.sleep(1.0)
            else:
                title, answer, _, reaction = suspect["questions"][q_idx]
                dialogue_log.append(("수사관", "질문", title))
                dialogue_log.append((suspect["name"], reaction, answer))
                show_interrogation_log(suspect, dialogue_log, animate_last=True)
                input(f"\n{CYAN}[Enter 키를 누르면 목록으로 돌아갑니다...]{RESET}")
        elif sel == len(q_indices):
            if sid in state.broken_suspects: continue
            if not confront_ready:
                clear_screen()
                print(f"\n {RED}용의자의 모순을 격파할 결정적인 물증을 아직 확보하지 못했습니다.{RESET}")
                time.sleep(1.0)
                continue
            clue_keys = list(state.clues.keys())
            clue_opts = [f"[단서] {state.clues[k]['name']}" for k in clue_keys]
            c_sel = select_option(f"단서 제시 ─ {suspect['name']}의 거짓말 반박", clue_opts, subtitle="주장에 모순되는 증거를 선택하십시오")
            if c_sel != -1:
                chosen = clue_keys[c_sel]
                clear_screen()
                draw_header(f"모순 격파 ─ {suspect['name']}")
                if chosen == suspect["break_clue"]:
                    print(f"\n{GREEN}{BOLD}      ★ [모순 격파! 알리바이 파쇄 성공!] ★{RESET}\n")
                    dialogue_log.append(("수사관", "증거 제시", f"{state.clues[chosen]['name']}을(를) 제시하며 알리바이의 모순을 지적했다."))
                    dialogue_log.append((suspect["name"], "동요", suspect["break_msg"].replace("\n", " ")))
                    show_interrogation_log(suspect, dialogue_log, animate_last=True)
                    state.broken_suspects.add(sid)
                else:
                    print(f"\n{RED}[추궁 실패: 제시한 단서와 용의자의 주장 사이에 모순이 없습니다]{RESET}\n")
                    dialogue_log.append(("수사관", "증거 제시", f"{state.clues[chosen]['name']}을(를) 제시했지만 주장과의 연결을 입증하지 못했다."))
                    dialogue_log.append((suspect["name"], "불쾌", "그게 제 알리바이와 무슨 상관이죠? 억지 부리지 마십시오."))
                    show_interrogation_log(suspect, dialogue_log, animate_last=True)
                input(f"\n{CYAN}[Enter 키를 누르면 심문실로 돌아갑니다...]{RESET}")
        elif sel == len(q_indices) + 1:
            if dialogue_log:
                show_interrogation_log(suspect, dialogue_log)
            else:
                clear_screen()
                draw_header(f"심문 대화 로그 ─ {suspect['name']}")
                print(" 아직 기록된 문답이 없습니다.")
                draw_divider()
            input(f"\n{CYAN}[Enter 키를 누르면 심문실로 돌아갑니다...]{RESET}")

def consult_collaborator(state, cid):
    collab = COLLABORATORS[cid]
    while True:
        opts = []
        for title, _, _, requirements in collab["dialogues"]:
            if all(state.has_clue(clue_id) for clue_id in requirements):
                opts.append(f"[업무] {title}")
            else:
                opts.append(f"[잠김] {title} (선행 단서 필요)")
        sel = select_option(f"공조 수사 ─ {collab['name']} ({collab['role']})", opts, subtitle=collab["brief"])
        if sel == -1: break
        title, text, unlock_c, requirements = collab["dialogues"][sel]
        clear_screen()
        draw_header(f"수사 브리핑 ─ {collab['name']}")
        if not all(state.has_clue(clue_id) for clue_id in requirements):
            print(f"\n {RED}관련 현장 증거가 부족합니다. 먼저 현장 단서부터 확보하십시오.{RESET}\n")
            input(f"\n{CYAN}[Enter 키를 누르면 공조 목록으로 돌아갑니다...]{RESET}")
            continue
        print(f" {CYAN}주제: {title}{RESET}\n")
        print_slow(f" {BOLD}{collab['name']}:{RESET} \"{text}\"")
        draw_divider()
        if unlock_c: state.unlock_clue(unlock_c)
        input(f"\n{CYAN}[Enter 키를 누르면 공조 목록으로 돌아갑니다...]{RESET}")

def deduction_board(state):
    while True:
        options = []
        for deduction in DEDUCTIONS:
            if not all(state.has_clue(clue_id) for clue_id in deduction["requires"]):
                options.append(f"[잠김] {deduction['title']} (필요 단서 미확보)")
            elif deduction["id"] in state.solved_deductions:
                options.append(f"[추리완료] {deduction['title']}")
            else:
                options.append(f"[증거 대조] {deduction['title']}")
        sel = select_option("수사 보드 ─ 증거를 연결해 가설을 세우십시오", options)
        if sel == -1: return
        deduction = DEDUCTIONS[sel]
        if not all(state.has_clue(clue_id) for clue_id in deduction["requires"]):
            print(f"\n {RED}이 추리를 진행할 증거가 아직 모이지 않았습니다.{RESET}")
            time.sleep(1.0)
            continue
        if deduction["id"] in state.solved_deductions:
            print(f"\n {GREEN}{deduction['result']}{RESET}")
            input(f"\n{CYAN}[Enter 키를 누르면 수사 보드로 돌아갑니다...]{RESET}")
            continue
        answer = select_option("추리 선택 ─ 정황에 가장 부합하는 가설은?", deduction["choices"])
        if answer == -1: continue
        clear_screen()
        if answer == deduction["answer"]:
            state.solved_deductions.add(deduction["id"])
            print(f"\n {GREEN}{BOLD}[추리 기록 추가]{RESET}\n\n {deduction['result']}")
        else:
            print(f"\n {RED}[가설 보류]{RESET}\n\n 증거 하나만으로 결론을 내릴 수 없습니다. 수첩의 단서를 다시 대조하십시오.")
        input(f"\n{CYAN}[Enter 키를 누르면 수사 보드로 돌아갑니다...]{RESET}")

def submit_final_report(state):
    clear_screen()
    draw_header("최종 송치 보고서 작성 (검찰 영장 청구)")
    print(f" {YELLOW}* 사건의 모든 정황과 단서를 종합하여 법적 보고서를 작성합니다.{RESET}\n")
    if len(state.solved_deductions) < len(DEDUCTIONS):
        print(f" {RED}증거 대조 추리가 남아 있습니다. 수사 보드에서 가설을 먼저 검증하십시오.{RESET}\n")
        input(f"\n{CYAN}[Enter 키를 누르면 수사 본부로 돌아갑니다...]{RESET}")
        return False
    if len(state.broken_suspects) < 1:
        print(f" {RED}경고: 용의자들의 알리바이를 충분히 격파하지 않은 상태입니다!{RESET}\n")

    c_sel = select_option("보고서 [1/4] ─ 진범 지목", REPORT_DATA["culprits"])
    if c_sel == -1: return False
    m_sel = select_option("보고서 [2/4] ─ 범행 동기", REPORT_DATA["motives"])
    if m_sel == -1: return False
    t_sel = select_option("보고서 [3/4] ─ 범행 수법 및 트릭", REPORT_DATA["methods"])
    if t_sel == -1: return False
    e_sel = select_option("보고서 [4/4] ─ 스모킹 건(결정적 증거)", REPORT_DATA["evidences"])
    if e_sel == -1: return False

    clear_screen()
    draw_header("검찰 영장 심사 및 국과수 대조 중...")
    for _ in range(5):
        time.sleep(0.2)
        print(" ■■■■", end="", flush=True)
    print("\n")

    if c_sel == 0 and m_sel == 1 and t_sel == 1 and e_sel == 1:
        clear_screen()
        print(f"\n{GREEN}{'=' * 60}{RESET}")
        print(f"{GREEN}{BOLD}   ★★★ [사건 완벽 해결] 긴급 구속영장이 정식 발부되었습니다! ★★★{RESET}")
        print(f"{GREEN}{'=' * 60}{RESET}\n")
        for line in EPILOGUE_TEXT:
            print_slow(line, delay=0.015)
        input(f"\n{CYAN}[Enter 키를 누르면 게임을 종료합니다. 수고하셨습니다!]{RESET}")
        return True
    else:
        clear_screen()
        print(f"\n{RED}{'=' * 60}{RESET}\n{RED}{BOLD}     [영장 기각] 보고서에 논리적 오류가 존재합니다.{RESET}\n{RED}{'=' * 60}{RESET}\n")
        print(f" {YELLOW}기각 사유 검토:{RESET}")
        if c_sel != 0: print(" - 지목된 피의자는 알리바이가 소명되었거나 인과관계가 결여되어 있습니다.")
        if m_sel != 1: print(" - 피해자의 찢긴 논문 서류 및 피해 정황과 부합하지 않는 동기입니다.")
        if t_sel != 1: print(" - 부검 소견(질식사) 및 크론탭 포렌식 기록과 수법이 충돌합니다.")
        if e_sel != 1: print(" - 제시한 증거는 피의자의 범행을 직접 입증하기에 부족합니다.")
        draw_divider()
        input(f"\n{CYAN}[Enter 키를 누르면 수사 본부로 복귀합니다...]{RESET}")
        return False

def main():
    state = GameState()
    show_intro()
    while True:
        menu_opts = [
            "[현장 조사] 사건 현장 조사 (제2종합연구동 4층 특수실험실 수색)",
            "[용의 심문] 용의자 4인 심문실 (박도현, 이수빈, 정민우, 서지훈)",
            "[협력 공조] 수사 협력자 공조 (강태식 반장 & 한예원 팀장)",
            f"[수사 수첩] 수사 수첩 열기 (증거 DB {len(state.clues)}건 확인)",
            "[증거 대조 추리] 수사 보드에서 단서를 연결하고 가설 검증",
            "[최종 보고] 최종 송치 보고서 작성 (진범 지목 및 사건 해결)",
            "[사건 안내] 사건 브리핑 다시 보기"
        ]
        sel = select_option(f"{GAME_TITLE} ─ 현장 특별수사본부", menu_opts, subtitle="활동할 수사 항목을 선택하십시오", allow_cancel=True)
        if sel == -1:
            clear_screen()
            print(f"\n {YELLOW}수사를 중단하고 게임을 종료합니다.{RESET}\n")
            break
        elif sel == 0: investigate_scene(state)
        elif sel == 1:
            while True:
                s_opts = [f"{s['name']} ({s['role']})" for s in SUSPECTS.values()]
                s_sel = select_option("용의자 심문실 ─ 대상 선택", s_opts)
                if s_sel == -1: break
                interrogate_suspect(state, str(s_sel + 1))
        elif sel == 2:
            while True:
                c_opts = [f"{c['name']} ({c['role']})" for c in COLLABORATORS.values()]
                c_sel = select_option("수사 협력자 공조 ─ 대상 선택", c_opts)
                if c_sel == -1: break
                consult_collaborator(state, str(c_sel + 1))
        elif sel == 3: state.show_notebook()
        elif sel == 4: deduction_board(state)
        elif sel == 5:
            if submit_final_report(state): break
        elif sel == 6: show_intro()

if __name__ == "__main__":
    main()
