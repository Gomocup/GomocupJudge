# GomocupJudge

GomocupJudge is a robust, distributed tournament manager and referee platform for Gomocup (the international computer Gomoku and Renju tournament). It coordinates matches between artificial intelligence (AI) engines, manages tournament tables, monitors resource restrictions, and computes ELO ratings.

---

## Architecture Overview

GomocupJudge is built as a distributed network:
- **Server**: Orchestrates matchmaking, rating computations, and remote configuration.
- **Client**: Connects to the server, runs the actual engine processes, monitors resource restrictions, and runs the referee logic.

For detailed usage, configuration, and developer guides on each component, please refer to:
- 📂 **[Tournament Server Documentation](file:///d:/Programming/CPP/Gomocup/Organization/GomocupJudge/server/README.md)**
- 📂 **[Match Client Documentation](file:///d:/Programming/CPP/Gomocup/Organization/GomocupJudge/client/README.md)**

---

## Directory Structure

```text
├── client/                 # Client code running matches & communicating with engines (see client/README.md)
├── server/                 # Tournament server code coordinating matches (see server/README.md)
├── wrapper/                # Experimental client connecting AIs to custom servers
│   └── client.py           # Wrapper client script (see wrapper/README.md)
├── wrapper21/              # Gomocup 2021 Experimental Client (Renju Caffe integration)
│   └── client.py           # Renju Caffe client wrapper (see wrapper21/README.md)
├── doc/                    # Documentation folder
│   └── GomocupProtocol.md  # Detailed Gomocup AI protocol specifications
├── test_zip_rules.py       # CLI tool to test engine rule compatibility of ZIP packages
└── README.md               # Main project documentation (this file)
```

---

## Installation & Prerequisites

Make sure you have **Python 3.8+** installed.

Install the necessary python dependencies:
```bash
pip install psutil paramiko
```
- `psutil` is required by the clients to monitor memory (USS) and CPU states of the engine child processes.
- `paramiko` is optionally used by the server to manage remote clients over SSH.

---

## Auxiliary Tools

### 1. Engine Rule Tester (`test_zip_rules.py`)
A verification CLI tool designed to test if an engine ZIP package complies with the Gomocup protocol and correctly supports rules (Freestyle, Fastgame, Standard, Renju, Caro).

For each format, the tool runs:
1. **Single-point checks**: Preloads specific boards to check next-move validity. If it fails, the format fails immediately, skipping self-play to save time.
2. **Self-play checks**: Launches a game between two instances of the engine from the opening `b2e2e3` to check for crashes or timeouts.

To run the tester:
```bash
python test_zip_rules.py <PATH_TO_ZIP_1> [<PATH_TO_ZIP_2> ...]
```
Examples:
```bash
# Test a single engine zip file
python test_zip_rules.py client/temp/engine/TITO14.zip

# Test multiple engines at once
python test_zip_rules.py client/temp/engine/TITO14.zip client/temp/engine/SWINE15.zip client/temp/engine/PISQ7.zip
```

### 2. Experimental Wrapper Clients
Lightweight scripts designed for participant AIs to connect directly to standard external servers or Renju Caffe platforms.

- **Standard Wrapper (`wrapper/client.py`):**
  ```bash
  python wrapper/client.py --host <HOST> --port <PORT> --key <KEY> --ai <AI_EXE_PATH>
  ```
- **2021 Renju Caffe Wrapper (`wrapper21/client.py`):**
  ```bash
  python wrapper21/client.py --host <HOST> --name <NAME> --key <KEY> --ai <AI_EXE_PATH>
  ```
