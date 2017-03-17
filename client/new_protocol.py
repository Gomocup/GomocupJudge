import subprocess
import copy
import time

class new_protocol(object):
    def __init__(self,
                 cmd,
                 board,
                 timeout_turn = 30*1000,
                 timeout_match = 180*1000,
                 max_memory = 350*1024*1024,
                 game_type = 1,
                 rule = 0,
                 folder = "./",
                 working_dir = "./",
                 tolerance = 1000):
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

        self.color = 1
        self.piece = {}
        for i in xrange(len(board)):
            for j in xrange(len(board[i])):
                if board[i][j][0] != 0:
                    self.piece[board[i][j][0]] = (i,j)

        self.process = subprocess.Popen(cmd,
                                        shell=False,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        cwd=self.working_dir)
        self.process.stdin.write("START " + str(len(self.board)) + "\n")
        self.process.stdin.write("INFO timeout_turn " + str(self.timeout_turn) + "\n")
        self.process.stdin.write("INFO timeout_match " + str(self.timeout_match) + "\n")
        self.process.stdin.write("INFO max_memory " + str(self.max_memory) + "\n")
        self.process.stdin.write("INFO game_type " + str(self.game_type) + "\n")
        self.process.stdin.write("INFO rule " + str(self.rule) + "\n")
        self.process.stdin.write("INFO folder " + str(self.folder) + "\n")

    def wait(self):
        msg = ''
        x, y = -1, -1
        timeout_sec = (self.tolerance + min((self.timeout_match - self.timeused), self.timeout_turn)) / 1000.
        start = time.time()
        while True:
            buf = self.process.stdout.readline()
            if time.time() - start > timeout_sec:
                break
            if buf == "":
                time.sleep(0.01)
            else:
                if buf.lower().startswith("message"):
                    msg += buf
                else:
                    try:
                        x, y = buf.split(",")
                        x, y = int(x), int(y)
                        break
                    except:
                        pass
        end = time.time()
        self.timeused += (max(0, end-start-0.01))*1000

        self.piece[len(self.piece)+1] = (x,y)
        self.board[x][y] = (len(self.piece), self.color)
        return msg, x, y
        
    def turn(self, x, y):
        self.piece[len(self.piece)+1] = (x,y)
        self.board[x][y] = (len(self.piece), 3 - self.color)

        self.process.stdin.write("INFO time_left " + str(self.timeout_match - self.timeused) + "\n")
        self.process.stdin.write("TURN " + str(x) + "," + str(y) + "\n")

        return self.wait()

    def start(self):
        self.process.stdin.write("INFO time_left " + str(self.timeout_match - self.timeused) + "\n")
        self.process.stdin.write("BOARD\n")
        for i in xrange(1, len(self.piece)+1):
            self.process.stdin.write(str(self.piece[i][0]) + "," + str(self.piece[i][1]) + "," + str(self.board[self.piece[i][0]][self.piece[i][1]][1]) + "\n")
        self.process.stdin.write("DONE\n")

        return self.wait()

    def clean(self):
        self.process.stdin.write("END\n")
        time.sleep(0.5)
        if self.process.poll() is None:
            self.process.kill()


def main():
    engine = new_protocol(
        cmd = "C:/Kai/git/GomocupJudge/engine/pbrain-yixin15.exe",
        board = [[(0,0) for i in xrange(20)] for j in xrange(20)],
        timeout_turn = 1000,
        timeout_match = 100000,
        max_memory = 350*1024*1024,
        game_type = 1,
        rule = 0,
        folder = "C:/Kai/git/GomocupJudge/tmp",
        working_dir = "C:/Kai/git/GomocupJudge/engine",
        tolerance = 1000)

    msg, x, y = engine.start()

    print msg, x, y

    engine.clean()


if __name__ == '__main__':
    main()
