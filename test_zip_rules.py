import sys
import os
import zipfile
import shutil
import platform
import argparse
import traceback

# Add client folder to python path to import modules directly
CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "client"))
sys.path.append(CLIENT_DIR)

from ai_match import ai_match
from old_protocol import old_protocol
from new_protocol import new_protocol
from utility import *


def select_executable(extracted_dir, rule, board_size, is_os_64bit):
    # Find all .exe files recursively
    all_exes = []
    for root, dirs, files in os.walk(extracted_dir):
        for f in files:
            if f.lower().endswith(".exe"):
                all_exes.append(os.path.join(root, f))

    if not all_exes:
        return None, None

    if len(all_exes) == 1:
        fname = all_exes[0]
        protocol = "new" if os.path.basename(fname).lower().startswith("pbrain") else "old"
        return fname, protocol

    # Filter based on protocol preference: prefer pbrain (new) over non-pbrain (old)
    exe_list = []
    has_pbrain = False
    for fname in all_exes:
        basename = os.path.basename(fname)
        if basename.lower().startswith("pbrain"):
            if has_pbrain:
                exe_list += [fname]
            else:
                exe_list = [fname]
                has_pbrain = True
        else:
            if not has_pbrain:
                exe_list += [fname]

    # Map target rule and size
    if rule & 4:
        target_rule = "renju"
    elif rule & 8:
        target_rule = "caro"
    elif rule & 1:
        target_rule = "standard"
    else:
        target_rule = "freestyle"
    target_size = str(board_size)

    valid_rules = ["freestyle", "standard", "renju", "caro"]
    valid_sizes = ["15", "20"]

    def get_file_rule_size(path):
        base = os.path.splitext(os.path.basename(path))[0].lower()
        # Strip 64-bit suffix if present at the end
        if base.endswith("_64"):
            base = base[:-3]
        elif base.endswith("-64"):
            base = base[:-3]
        elif base.endswith("64"):
            base = base[:-2]

        # Check _{rule}-{size}
        for r in valid_rules:
            for s in valid_sizes:
                suffix = f"_{r}-{s}"
                if base.endswith(suffix):
                    return r, s
        # Check _{rule}
        for r in valid_rules:
            suffix = f"_{r}"
            if base.endswith(suffix):
                return r, None
        # Check _{size}
        for s in valid_sizes:
            suffix = f"_{s}"
            if base.endswith(suffix):
                return None, s
        return None, None

    def score_candidate(path):
        fname = os.path.basename(path)
        file_rule, file_size = get_file_rule_size(path)
        if file_rule is not None and file_rule != target_rule:
            compat = 0
        elif file_size is not None and file_size != target_size:
            compat = 0
        else:
            if file_rule == target_rule and file_size == target_size:
                compat = 4
            elif file_rule == target_rule:
                compat = 3
            elif file_size == target_size:
                compat = 2
            else:
                compat = 1
        arch_match = (is_os_64bit and "64" in fname) or (
            not is_os_64bit and "64" not in fname
        )
        return compat, arch_match

    candidates_with_scores = []
    for fname in exe_list:
        score = score_candidate(fname)
        candidates_with_scores.append((score, fname))

    # If the maximum compatibility is 0, fall back to treating them all as generic (compat = 1)
    max_compat = max(score[0] for score, fname in candidates_with_scores)
    if max_compat == 0:
        candidates_with_scores = []
        for fname in exe_list:
            basename = os.path.basename(fname)
            arch_match = (is_os_64bit and "64" in basename) or (
                not is_os_64bit and "64" not in basename
            )
            candidates_with_scores.append(((1, arch_match), fname))

    # Sort by score: compatibility_score (descending), arch_match (descending)
    candidates_with_scores.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
    selected_exe = candidates_with_scores[0][1]

    protocol = "new" if os.path.basename(selected_exe).lower().startswith("pbrain") else "old"
    return selected_exe, protocol


def run_self_play(selected_exe, protocol, rule, board_size, timeout_turn, timeout_match, temp_folder):
    folder_1 = os.path.join(temp_folder, "f1")
    folder_2 = os.path.join(temp_folder, "f2")
    os.makedirs(folder_1, exist_ok=True)
    os.makedirs(folder_2, exist_ok=True)
    
    opening = str_to_pos("b2e2e3")
    cmd = selected_exe.replace("\\", "/")
    working_dir = os.path.dirname(selected_exe)
    
    try:
        game = ai_match(
            board_size=board_size,
            opening=opening,
            cmd_1=cmd,
            cmd_2=cmd,
            protocol_1=protocol,
            protocol_2=protocol,
            timeout_turn_1=timeout_turn,
            timeout_turn_2=timeout_turn,
            timeout_match_1=timeout_match,
            timeout_match_2=timeout_match,
            max_memory_1=350 * 1024 * 1024,
            max_memory_2=350 * 1024 * 1024,
            game_type=1,
            rule=rule,
            folder_1=folder_1,
            folder_2=folder_2,
            working_dir_1=working_dir,
            working_dir_2=working_dir,
            tolerance=1000,
            settings={},
            special_rule="",
        )
        msg, psq, result, endby = game.play()
        if endby in (0, 1):
            return True, f"Completed normally (result={result}, endby={endby})"
        elif endby == 2:
            return False, "Timeout (TLE)"
        elif endby == 3:
            return False, "Illegal move coordinate"
        else:
            return False, f"Engine crash (endby={endby})"
    except Exception as e:
        return False, f"Crash/Exception: {str(e)}"


def build_board(seq, board_size):
    board = [[(0, 0) for _ in range(board_size)] for _ in range(board_size)]
    next_player_idx = len(seq) % 2
    for idx, (x, y) in enumerate(seq):
        move_player_idx = idx % 2
        color = 1 if (move_player_idx == next_player_idx) else 2
        board[x][y] = (idx + 1, color)
    return board


def run_rule_check(selected_exe, protocol, rule, board_size, timeout_turn, timeout_match, temp_folder, sequence_str, rule_type):
    seq = str_to_pos(sequence_str)
    board = build_board(seq, board_size)
    cmd = selected_exe.replace("\\", "/")
    working_dir = os.path.dirname(selected_exe)
    folder = os.path.join(temp_folder, "check_persistent")
    os.makedirs(folder, exist_ok=True)
    
    try:
        if protocol == "old":
            engine = old_protocol(
                cmd=cmd,
                board=board,
                timeout_turn=timeout_turn,
                timeout_match=timeout_match,
                max_memory=350 * 1024 * 1024,
                game_type=1,
                rule=rule,
                folder=folder,
                working_dir=working_dir,
            )
        else:
            engine = new_protocol(
                cmd=cmd,
                board=board,
                timeout_turn=timeout_turn,
                timeout_match=timeout_match,
                max_memory=350 * 1024 * 1024,
                game_type=1,
                rule=rule,
                folder=folder,
                working_dir=working_dir,
            )
            
        msg, x, y = engine.start()
        engine.clean()
        
        def pos_to_coord(x, y):
            col_letter = chr(ord('a') + x)
            row_num = str(y + 1)
            return col_letter + row_num
            
        actual_move_str = pos_to_coord(x, y)
        
        # Rule validation checks
        if rule_type == "all":
            allowed = [(6, 7), (11, 7)]  # g8, l8
            passed = (x, y) in allowed
            expected_desc = "g8 or l8"
        elif rule_type == "standard_specific":
            allowed = [(5, 7), (9, 7)]  # f8, j8
            passed = (x, y) in allowed
            expected_desc = "f8 or j8"
        elif rule_type == "renju_specific":
            forbidden = (6, 8)  # g9
            passed = (x, y) != forbidden
            expected_desc = "not g9"
        elif rule_type == "caro_specific":
            allowed = [(5, 4), (5, 5), (5, 9), (5, 10)]  # f5, f6, f10, f11
            passed = (x, y) in allowed
            expected_desc = "f5, f6, f10, or f11"
        else:
            return False, f"Unknown rule type check: {rule_type}"
            
        if passed:
            return True, f"Move {actual_move_str} matches expected '{expected_desc}'"
        else:
            return False, f"Move {actual_move_str} did not match expected '{expected_desc}'"
            
    except Exception as e:
        return False, f"Rule check failed with exception: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Gomocup Engine ZIP Rule Tester")
    parser.add_argument("zip_path", help="Path to the engine .zip file to test")
    args = parser.parse_args()

    zip_path = os.path.abspath(args.zip_path)
    if not os.path.isfile(zip_path):
        print(f"Error: ZIP file not found at {zip_path}")
        sys.exit(1)

    print("==================================================")
    print("Gomocup Engine ZIP Rule Tester")
    print("==================================================")
    print(f"Testing Archive: {os.path.basename(zip_path)}")
    
    # Establish a workspace-safe temporary extraction directory
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(workspace_dir, "test_temp_extracted")
    
    # Clean up any existing temp directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        print("Extracting ZIP archive...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
            
        is_os_64bit = platform.machine().endswith("64")
        
        FORMATS = [
            {
                "name": "Freestyle",
                "rule": 0,
                "board_size": 20,
                "timeout_turn": 30000,
                "timeout_match": 180000,
                "checks": [
                    ("h8h9i8i9j8j9k8k9", "all")
                ]
            },
            {
                "name": "Fastgame",
                "rule": 0,
                "board_size": 20,
                "timeout_turn": 5000,
                "timeout_match": 100000,
                "checks": [
                    ("h8h9i8i9j8j9k8k9", "all")
                ]
            },
            {
                "name": "Standard",
                "rule": 1,
                "board_size": 15,
                "timeout_turn": 30000,
                "timeout_match": 180000,
                "checks": [
                    ("h8h9i8i9j8j9k8k9", "all"),
                    ("h8h9i8h10g8h11j13h12g14h14i15", "standard_specific")
                ]
            },
            {
                "name": "Renju",
                "rule": 4,
                "board_size": 15,
                "timeout_turn": 30000,
                "timeout_match": 180000,
                "checks": [
                    ("h8h9i8i9j8j9k8k9", "all"),
                    ("h8h9i7i9h10i6i11i12", "renju_specific")
                ]
            },
            {
                "name": "Caro",
                "rule": 8,
                "board_size": 15,
                "timeout_turn": 30000,
                "timeout_match": 180000,
                "checks": [
                    ("h8h9i8i9j8j9k8k9", "all"),
                    ("h8f8g8f9i8f7j8l8", "caro_specific")
                ]
            }
        ]
        
        results = {}
        
        for fmt in FORMATS:
            name = fmt["name"]
            rule = fmt["rule"]
            board_size = fmt["board_size"]
            timeout_turn = fmt["timeout_turn"]
            timeout_match = fmt["timeout_match"]
            
            print(f"\n--- Testing format: {name} (Rule {rule}, Size {board_size}) ---")
            
            # Select executable for this specific rule/size combination
            exe_path, protocol = select_executable(temp_dir, rule, board_size, is_os_64bit)
            if not exe_path:
                print(f"Result for {name}: FAILED (No executable found or selected for this format)")
                results[name] = (False, "No matching executable found")
                continue
                
            print(f"Selected executable: {os.path.basename(exe_path)} (Protocol: {protocol})")
            
            # 1. Specific rule-understanding checks
            rule_checks_passed = True
            rule_check_msg = ""
            for seq_str, check_type in fmt["checks"]:
                print(f"Checking position rule: {seq_str} ({check_type})...")
                chk_passed, chk_msg = run_rule_check(
                    exe_path, protocol, rule, board_size, timeout_turn, timeout_match, temp_dir, seq_str, check_type
                )
                print(f"Check status: {'PASSED' if chk_passed else 'FAILED'} ({chk_msg})")
                if not chk_passed:
                    rule_checks_passed = False
                    rule_check_msg = chk_msg
                    break
                    
            if not rule_checks_passed:
                results[name] = (False, f"Rule check failed: {rule_check_msg}")
                continue

            # 2. Self-play match
            print("Running self-play game...")
            sp_passed, sp_msg = run_self_play(
                exe_path, protocol, rule, board_size, timeout_turn, timeout_match, temp_dir
            )
            print(f"Self-play status: {'PASSED' if sp_passed else 'FAILED'} ({sp_msg})")
            
            if not sp_passed:
                results[name] = (False, f"Self-play failed: {sp_msg}")
                continue
                
            results[name] = (True, "All tests passed")
                
        print("\n==================================================")
        print("Final Test Results Report")
        print("==================================================")
        for fmt in FORMATS:
            name = fmt["name"]
            passed, desc = results.get(name, (False, "Not run"))
            status = "PASSED" if passed else "FAILED"
            print(f"{name:<15}: {status:<8} ({desc})")
        print("==================================================")
        
    except Exception as e:
        print("\nAn error occurred during testing:")
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Done.")

if __name__ == "__main__":
    main()
