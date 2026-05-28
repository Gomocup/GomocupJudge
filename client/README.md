# GomocupJudge Match Client

The GomocupJudge Client is a referee agent that receives matches from the server, runs the actual engine processes, monitors resource restrictions, and enforces Gomocup game protocols.

---

## Command Line Usage

Run the client using the following format:
```bash
python client.py --host <HOST> --port <PORT> --dir <WORK_DIR> [--debug] [--rule <RULE>] [--blacklist <LIST>]
```

- `--host`: Host IP address of the tournament server.
- `--port`: Host port of the tournament server (typically `50007`).
- `--dir`: Local working directory to execute engines and store matches.
- `--debug`: Optional flag. If provided, writes raw packet and process logs to `log.txt` under `<WORK_DIR>`.
- `--rule`: Optional. Configures special referee rules (e.g. `swap2`).
- `--blacklist`: Optional. Comma-separated list of engine MD5s to bypass.

Example:
```bash
python client.py --host localhost --port 50007 --dir C:\GomocupJudgeClient
```

---

## Directory Management

Under the specified `--dir` directory, the client automatically manages the following structure:
- **`<WORK_DIR>/engine/`**: Stores downloaded engine binaries (`.zip` or `.exe` format) indexed by the server.
- **`<WORK_DIR>/match/<ENGINE_MD5>/`**: The extraction directory where zip packages are unpacked and executed during matches.
- **`<WORK_DIR>/match/folder/<ENGINE_MD5>/`**: Persistent workspace directory allocated for the engine to save logs or learning tables (limited to 70MB).

---

## Executable Suffix Selection Logic

When executing an engine package containing multiple files, the client intelligently selects the best binary inside `<WORK_DIR>/match/<ENGINE_MD5>/` using the following scoring logic:

1. **Protocol Preference**:
   Executables starting with `pbrain` (new protocol) are prioritized over non-`pbrain` executables (old protocol). If any `pbrain` executable exists, non-`pbrain` ones are ignored.

2. **Suffix Matching**:
   Filenames are parsed for a suffix matching the rule and board size of the match:
   - `_{rule}-{size}`: Exact match for both rule and size (e.g., `_standard-15`). **Score: 4**
   - `_{rule}`: Matches the rule (e.g., `_standard`). **Score: 3**
   - `_{size}`: Matches the board size (e.g., `_15`). **Score: 2**
   - Generic (no rule/size suffix). **Score: 1**
   - Mismatched (specifies a different rule/size). **Score: 0**

3. **Fallback Match**:
   If the maximum compatibility score is `0` (all executables specify different rules/sizes than current match), they are treated as generic (Score: `1`) to allow running the engine as a fallback.

4. **OS Architecture Match**:
   Checks whether the system architecture matches the executable name:
   - On 64-bit OS: prefers files with `"64"` in the filename.
   - On 32-bit OS: prefers files without `"64"` in the filename.

The candidate with the highest tuple score `(compatibility_score, arch_match)` is selected and executed.

---

## Process Sandboxing & Monitoring

To maintain fair play, the client restricts resources using the `psutil` library:
- **Disallowing Pondering**: When it is the opponent's turn, the client suspends the engine's child process group (`suspend()`) to prevent it from consuming background CPU cycles. The process is resumed (`resume()`) when it's their turn to think.
- **Time Limits (TLE)**: Measures execution duration per move and per match. Exceeding `<TIMEOUT_TURN>` + `<TOLERANCE>` triggers a `RuntimeError("TLE")`.
- **Memory Limits (MLE)**: Sums the unique set size (USS) memory usage of the engine and all its child processes. Exceeding the memory limit triggers a `RuntimeError("MLE")`.
- **Disk Limits (FLE)**: Monitors the storage size of the persistent folder under `<WORK_DIR>/match/folder/<ENGINE_MD5>/`. Exceeding 70MB triggers a `RuntimeError("FLE")`.
