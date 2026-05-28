# GomocupJudge Tournament Server

The GomocupJudge Server is the centralized coordinator for tournaments. It reads the tournament configuration, manages connected match clients, compiles game records, uploads results, and calculates player ELO ratings using BayesElo.

---

## Command Line Usage

Run the server with the following format:
```bash
python server.py <TOURNAMENT_NAME> <PORT>
```

- `<TOURNAMENT_NAME>`: The name of the tournament configuration file (without `.txt` extension) located in the `server/tournament/` directory.
- `<PORT>`: The TCP port to bind and listen on for incoming client connections (typically `50007`).

Example:
```bash
python server.py example 50007
```

---

## Tournament Configuration File

The tournament parameters are loaded from `server/tournament/<TOURNAMENT_NAME>.txt`. It is formatted as a key-value properties file.

### Sample Configuration:
```text
name=gomocup2017
board=20
rule=0
opening=gomocup2017openings
engines=pbrain-swine,pbrain-yixin,pbrain-pela
engine_ratings=0,0,0
rating_diff=0
tournament=1
time_turn=30000
time_match=180000
tolerance=1000
memory=367001600
real_time_pos=1
real_time_message=1
upload_ratio=1.0
upload_offline_result=0
remote=my_remote_server
```

### Config Key Descriptions:
- **`name`**: The tournament session folder name under `result/`.
- **`board`**: Grid size of the board (e.g., `15` or `20`).
- **`rule`**: Gomocup game rule bitmask:
  - `0`: Freestyle
  - `1`: Standard (exactly 5 in a row)
  - `4`: Renju
  - `8`: Caro
- **`opening`**: Name of the opening template file (e.g. `gomocup2017openings.txt`) under the `server/opening/` directory.
- **`engines`**: Comma-separated list of engine identifiers (MD5 names) participating in the tournament.
- **`engine_ratings`**: Comma-separated initial rating points for the engines (matches order of `engines`).
- **`tournament`**: If `1`, runs a round-robin tournament; if `0`, coordinates custom pairings.
- **`time_turn`**: Turn time limit in milliseconds.
- **`time_match`**: Match time limit in milliseconds.
- **`tolerance`**: Grace period tolerance in milliseconds for engine lag.
- **`memory`**: Engine RAM limit in bytes.
- **`real_time_pos`**: `1` to report real-time move coordinates to the server, `0` to wait until match end.
- **`real_time_message`**: `1` to stream engine debug/message outputs live, `0` to keep them local.
- **`upload_ratio`**: SSH upload frequency ratio.
- **`upload_offline_result`**: Upload offline result backups.
- **`remote`**: Remote upload profile configuration filename located in the `server/remote/` folder.

---

## BayesElo Rating System

The server integrates with **`bayeselo.exe`** (compiled from Remi Coulom's C++ BayesElo implementation in the `BayesElo/` folder) to calculate ELO ratings after matches complete:
- Saves game logs in PGN/Gomocup format.
- Automatically invokes `bayeselo` to calculate rating distributions.
- Updates player ratings dynamically during tournament runs.

---

## Log & Result Outputs

All outputs for a running tournament are saved in the `server/result/<TOURNAMENT_NAME>/` directory:
- **`log.txt`**: Main server transaction and matchmaking log.
- **`netlog.txt`**: Network sockets transmission log.
- **`state.txt`**: Saved serialization state of the active tournament (allows resuming after interruption).
- **`result.txt`**: Running rating calculations and ELO stats.
- **`message.txt`**: Debug messages received from client engines.
