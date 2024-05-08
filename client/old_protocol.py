import subprocess, shlex
import copy
import time
import psutil
import os
from threading import Timer
from utility import *


class old_protocol(object):
    def __init__(
        self,
        cmd,
        board,
        timeout_turn=30 * 1000,
        timeout_match=180 * 1000,
        max_memory=350 * 1024 * 1024,
        game_type=1,
        rule=0,
        folder="./",
        working_dir="./",
        tolerance=1000,
    ):
        self.cmd = cmd
        self.board = copy.deepcopy(board)
        self.timeout_turn = timeout_turn
        self.timeout_match = timeout_match
        self.max_memory = max_memory
        self.game_type = game_type
        self.rule = rule
        self.folder = folder
        self.working_dir = working_dir
        self.tolerance = tolerance
        self.timeused = 0

        self.vms_memory = 0

        self.color = 1
        self.piece = {}
        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j][0] != 0:
                    self.piece[board[i][j][0]] = (i, j)

    def run(self):
        timeout_sec = (
            self.tolerance
            + min((self.timeout_match - self.timeused), self.timeout_turn)
        ) / 1000.0
        start = time.time()
        proc = subprocess.Popen(
            shlex.split(self.cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.working_dir,
            shell=False,
        )
        try:
            pp = psutil.Process(proc.pid)
            m = 0
            ds = list(pp.children(recursive=True))
            ds = ds + [pp]
            for d in ds:
                try:
                    m += d.memory_full_info().uss
                except:
                    pass
            self.vms_memory = max(self.vms_memory, m)
        except:
            pass

        def kill_proc(p):
            _pp = psutil.Process(p.pid)
            for pp in _pp.children(recursive=True):
                pp.kill()
            _pp.kill()

        timer = Timer(timeout_sec, kill_proc, [proc])
        try:
            timer.start()
            proc.communicate()
        finally:
            timer.cancel()
        end = time.time()
        self.timeused += int(max(0, end - start - 0.01) * 1000)
        if end - start >= timeout_sec:
            raise RuntimeError("TLE")
        if self.vms_memory > self.max_memory:
            raise RuntimeError("MLE")
        if get_dir_size(self.folder) > 70 * 1024 * 1024:
            raise RuntimeError("FLE")

    def write_plocha(self):
        f = open(os.path.join(self.working_dir, "PLOCHA.DAT"), "w")
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j][1] == 0:
                    f.write("-")
                elif self.board[i][j][1] == 1:
                    f.write("x")
                elif self.board[i][j][1] == 2:
                    f.write("o")
                elif self.board[i][j][1] == 3:
                    f.write("#")
            f.write("\n")
        f.close()

    def write_tah(self):
        f = open(os.path.join(self.working_dir, "TAH.DAT"), "w")
        if self.color == 1:
            f.write("x\n")
        else:
            f.write("o\n")
        f.close()

    def write_info(self):
        f = open(os.path.join(self.working_dir, "INFO.DAT"), "w")
        f.write("max_memory " + str(self.max_memory) + "\n")
        f.write("timeout_match " + str(self.timeout_match) + "\n")
        f.write("timeout_turn " + str(self.timeout_turn) + "\n")
        f.write("game_type " + str(self.game_type) + "\n")
        f.write("rule " + str(self.rule) + "\n")
        f.write("folder " + str(self.folder) + "\n")
        f.close()

    def write_timeouts(self):
        f = open(os.path.join(self.working_dir, "TIMEOUTS.DAT"), "w")
        f.write(str(self.timeout_turn) + "\n")
        f.write(str(self.timeout_match - self.timeused) + "\n")
        f.close()

    def write_msg(self):
        f = open(os.path.join(self.working_dir, "MSG.DAT"), "w")
        f.close()

    def read_msg(self):
        f = open(os.path.join(self.working_dir, "MSG.DAT"), "r")
        msg = f.read()
        f.close()
        return msg

    def read_tah(self):
        f = open(os.path.join(self.working_dir, "TAH.DAT"), "r")
        l = f.readline().strip().split(",")
        f.close()
        return int(l[1]), int(l[0])

    def turn(self, x, y):
        self.piece[len(self.piece) + 1] = (x, y)
        self.board[x][y] = (len(self.piece), 3 - self.color)
        return self.start()

    def start(self):
        self.write_plocha()
        self.write_tah()
        self.write_info()
        self.write_timeouts()
        self.write_msg()
        self.run()
        msg = self.read_msg()
        x, y = self.read_tah()
        self.piece[len(self.piece) + 1] = (x, y)
        self.board[x][y] = (len(self.piece), self.color)
        return msg, x, y

    def clean(self):
        os.remove(os.path.join(self.working_dir, "MSG.DAT"))
        os.remove(os.path.join(self.working_dir, "TAH.DAT"))
        os.remove(os.path.join(self.working_dir, "TIMEOUTS.DAT"))
        os.remove(os.path.join(self.working_dir, "INFO.DAT"))
        os.remove(os.path.join(self.working_dir, "PLOCHA.DAT"))


def main():
    engine = old_protocol(
        cmd="C:/Kai/git/GomocupJudge/engine/pisq7.exe",
        board=[[(0, 0) for i in range(20)] for j in range(20)],
        timeout_turn=1000,
        timeout_match=100000,
        max_memory=350 * 1024 * 1024,
        game_type=1,
        rule=0,
        folder="C:/Kai/git/GomocupJudge/tmp",
        working_dir="C:/Kai/git/GomocupJudge/engine",
        tolerance=1000,
    )

    msg, x, y = engine.start()

    print(msg, x, y)

    engine.clean()


if __name__ == "__main__":
    main()
