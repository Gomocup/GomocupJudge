import requests
import argparse
import json
import time
from queue import Queue, Empty
from threading import Thread
import subprocess, shlex
import sys


class engine(object):
    def __init__(self, ai, moves, cando, timeleft):
        self.process = subprocess.Popen(
            shlex.split(ai),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=1,
            close_fds="posix" in sys.builtin_module_names,
            cwd=".",
        )

        def enqueue_output(out, q):
            for line in iter(out.readline, b""):
                q.put(line)
            out.close()

        self.queue = Queue()
        queuethread = Thread(
            target=enqueue_output, args=(self.process.stdout, self.queue)
        )
        queuethread.daemon = True
        queuethread.start()
        self.boarded = False
        self.write("START 15\n")
        self.write("INFO timeout_turn 5400000\n")
        self.write("INFO timeout_match 5400000\n")
        self.write("INFO max_memory 0\n")
        self.write("INFO game_type 1\n")
        self.write("INFO rule 1\n")
        self.write("INFO folder .\n")
        self.write("INFO time_left " + str(timeleft) + "\n")
        if "move-3" in cando or "swap" in cando:
            self.write("SWAP2BOARD\n")
            for m in moves:
                self.write(str(m[0]) + "," + str(m[1]) + "\n")
        else:
            self.write("BOARD\n")
            for i in range(len(moves)):
                m = moves[i]
                self.write(
                    str(m[0])
                    + ","
                    + str(m[1])
                    + ","
                    + str(1 + (len(moves) - i) % 2)
                    + "\n"
                )
            self.boarded = True
        self.write("DONE\n")

    def move(self, moves, cando, timeleft):
        self.write("INFO time_left " + str(timeleft) + "\n")
        if "swap" in cando:
            self.write("SWAP2BOARD\n")
            for m in moves:
                self.write(str(m[0]) + "," + str(m[1]) + "\n")
            self.write("DONE\n")
        elif self.boarded:
            self.write("TURN " + str(moves[-1][0]) + "," + str(moves[-1][1]) + "\n")
        else:
            self.write("BOARD\n")
            for i in range(len(moves)):
                m = moves[i]
                self.write(
                    str(m[0])
                    + ","
                    + str(m[1])
                    + ","
                    + str(1 + (len(moves) - i) % 2)
                    + "\n"
                )
            self.boarded = True
            self.write("DONE\n")

    def write(self, msg):
        # print("==>", msg)
        self.process.stdin.write(msg.encode())
        self.process.stdin.flush()

    def read(self):
        try:
            buf = self.queue.get_nowait().decode()
        except Empty:
            return None
        else:
            return buf

    def stop(self):
        self.write("END\n")


class client(object):
    def __init__(self, host, name, key, ai):
        self.host = host
        self.name = name
        self.key = key
        self.ai = ai
        self.board = {}
        self.msgs = {}

    def listen(self):

        while True:
            while True:
                try:
                    resp = requests.get(self.host + "game_bot/" + self.key + "/")
                    break
                except:
                    print("reconnecting (get) ...")
            games = json.loads(resp.text)
            for game in games:
                g = games[game]
                if g["game_ended"]:
                    if game in self.board:
                        self.board[game].stop()
                        del self.board[game]
            for game in list(self.board.keys()):
                if not game in games.keys():
                    self.board[game].stop()
                    del self.board[game]
            for game in games:
                g = games[game]
                if self.name == g["player_1"]["username"]:
                    timeleft = g["player_1"]["time_turn_left"]
                else:
                    timeleft = g["player_2"]["time_turn_left"]
                timeleft *= 1000
                if (self.name == g["player_1"]["username"] and not g["swapped"]) or (
                    self.name == g["player_2"]["username"] and g["swapped"]
                ):
                    m = 0
                else:
                    m = 1

                if len(g["moves"]) % 2 == m:
                    if game not in self.board:
                        self.board[game] = engine(
                            self.ai, g["moves"], g["can_do"], timeleft
                        )
                        self.msgs[game] = ""
                    else:
                        self.board[game].move(g["moves"], g["can_do"], timeleft)

                    while True:
                        msg = self.board[game].read()
                        if msg is not None:
                            self.msgs[game] += msg
                            if "\n" in self.msgs[game]:
                                self.msgs[game] = self.msgs[game].split("\n")
                                msg = self.msgs[game][0].strip()
                                self.msgs[game] = "\n".join(self.msgs[game][1:])
                                if (
                                    msg.startswith("MESSAGE")
                                    or msg.startswith("DEBUG")
                                    or msg.startswith("ERROR")
                                    or msg.startswith("SUGGEST")
                                    or msg.startswith("UNKNOWN")
                                    or msg.startswith("OK")
                                ):
                                    print(msg)
                                else:
                                    msg = msg.lower()
                                    if msg == "swap":
                                        move = "swap"
                                    else:
                                        move = msg.split()
                                        print(msg)
                                        for i in range(len(move)):
                                            x, y = move[i].split(",")
                                            move[i] = chr(ord("a") + int(x)) + str(
                                                int(y) + 1
                                            )
                                        move = ",".join(move)
                                    print(self.key, game, move)
                                    while True:
                                        try:
                                            resp = requests.post(
                                                self.host + "submit_move_bot/",
                                                data={
                                                    "bot_key": self.key,
                                                    "game_id": game,
                                                    "action": move,
                                                },
                                            )
                                            break
                                        except:
                                            print("reconnecting (post) ...")
                                    print(resp.text)
                                    break

                        time.sleep(0.1)

                assert len(self.board) <= 1  # for Gomocup 2021

            time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(
        description="Gomocup Experimental Tournament Client"
    )
    parser.add_argument("--host", dest="host", action="store", required=True)
    parser.add_argument("--name", dest="name", action="store", required=True)
    parser.add_argument("--key", dest="key", action="store", required=True)
    parser.add_argument("--ai", dest="ai", action="store", required=True)
    args = parser.parse_args()
    while True:
        try:
            wrapper = client(host=args.host, name=args.name, key=args.key, ai=args.ai)
            wrapper.listen()
        except:
            print("restarting after crash...")

        try:
            for game in list(wrapper.board.keys()):
                wrapper.board[game].stop()
                del wrapper.board[game]
        except:
            pass


if __name__ == "__main__":
    main()
