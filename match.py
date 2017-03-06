from old_protocol import old_protocol
from new_protocol import new_protocol

class match(object):
    def __init__(self,
                 board_size,
                 opening,
                 cmd_1,
                 cmd_2,
                 protocol_1,
                 protocol_2,
                 timeout_turn_1 = 30*1000,
                 timeout_turn_2 = 30*1000,
                 timeout_match_1 = 180*1000,
                 timeout_match_2 = 180*1000,
                 max_memory_1 = 350*1024*1024,
                 max_memory_2 = 350*1024*1024,
                 game_type = 1,
                 rule = 0,
                 folder_1 = "./",
                 folder_2 = "./",
                 working_dir_1 = "./",
                 working_dir_2 = "./",
                 tolerance = 1000):
        self.board_size = board_size
        self.opening = opening
        self.cmd_1 = cmd_1
        self.cmd_2 = cmd_2
        self.protocol_1 = protocol_1
        self.protocol_2 = protocol_2
        self.timeout_turn_1 = timeout_turn_1
        self.timeout_turn_2 = timeout_turn_2
        self.timeout_match_1 = timeout_match_1
        self.timeout_match_2 = timeout_match_2
        self.max_memory_1 = max_memory_1
        self.max_memory_2 = max_memory_2
        self.game_type = game_type
        self.rule = rule
        self.folder_1 = folder_1
        self.folder_2 = folder_2
        self.working_dir_1 = working_dir_1
        self.working_dir_2 = working_dir_2
        self.tolerance = tolerance

        self.move_num = 0
        self.last_move = (-1, -1)
        self.board_1 = [[(0,0) for i in xrange(self.board_size)] for j in xrange(self.board_size)]
        self.board_2 = [[(0,0) for i in xrange(self.board_size)] for j in xrange(self.board_size)]

    def next_move(self):
        if self.move_num == 0:
            for i in xrange(len(self.opening)):
                x, y = self.opening[i]
                if len(self.opening) % 2 == i % 2:
                    self.board_1[x][y] = (i+1, 1)
                    self.board_2[y][y] = (i+1, 2)
                else:
                    self.board_1[x][y] = (i+1, 2)
                    self.board_2[y][y] = (i+1, 1)
            self.engine_1 = self.init_protocol(self.cmd_1,
                                          self.protocol_1,
                                          self.board_1,
                                          self.timeout_turn_1,
                                          self.timeout_match_1,
                                          self.max_memory_1,
                                          self.game_type,
                                          self.rule,
                                          self.folder_1,
                                          self.working_dir_1,
                                          self.tolerance)
            msg, x, y = self.engine_1.start()
        elif self.move_num == 1:
            self.engine_2 = self.init_protocol(self.cmd_2,
                                          self.protocol_2,
                                          self.board_2,
                                          self.timeout_turn_2,
                                          self.timeout_match_2,
                                          self.max_memory_2,
                                          self.game_type,
                                          self.rule,
                                          self.folder_2,
                                          self.working_dir_2,
                                          self.tolerance)
            msg, x, y = self.engine_2.start()
        else:
            if self.move_num % 2 == 0:
                msg, x, y = self.engine_1.turn(self.last_move[0], self.last_move[1])
            else:
                msg, x, y = self.engine_2.turn(self.last_move[0], self.last_move[1])

        self.move_num += 1
        self.board_1[x][y] = (len(self.opening)+self.move_num, (self.move_num + 1) % 2 + 1)
        self.board_2[x][y] = (len(self.opening)+self.move_num, (self.move_num + 0) % 2 + 1)
        self.last_move = (x,y)
        return msg, x, y
                 
    def init_protocol(self,
                      cmd,
                      protocol_type,
                      board,
                      timeout_turn = 30*1000,
                      timeout_match = 180*1000,
                      max_memory = 350*1024*1024,
                      game_type = 1,
                      rule = 0,
                      folder = "./",
                      working_dir = "./",
                      tolerance = 1000):
        if protocol_type == 'old':
            return old_protocol(cmd, board, timeout_turn, timeout_match, max_memory, game_type, rule, folder, working_dir, tolerance)
        else:
            return new_protocol(cmd, board, timeout_turn, timeout_match, max_memory, game_type, rule, folder, working_dir, tolerance)

    def print_board(self):
        for i in xrange(self.board_size):
            s = ''
            for j in xrange(self.board_size):
                if self.board_1[i][j][1] == 0:
                    s += '_'
                elif self.board_1[i][j][1] == 1:
                    s += 'x'
                elif self.board_1[i][j][1] == 2:
                    s += 'o'
                else:
                    s += '#'
            print s

def main():
    #openings
    #[(2,3)]
    #[(1,10)]
    test = match(
        board_size = 20,
        opening = [(10,10)],
        cmd_1 = "C:/Kai/git/GomocupJudge/engine/pbrain-yixin15.exe",
        cmd_2 = "C:/Kai/git/GomocupJudge/engine/pisq7.exe",
        protocol_1 = "new",
        protocol_2 = "old",
        timeout_turn_1 = 5000,
        timeout_turn_2 = 5000,
        timeout_match_1 = 100000,
        timeout_match_2 = 100000,
        max_memory_1 = 350*1024*1024,
        max_memory_2 = 350*1024*1024,
        game_type = 1,
        rule = 0,
        folder_1 = "C:/Kai/git/GomocupJudge/tmp",
        folder_2 = "C:/Kai/git/GomocupJudge/tmp",
        working_dir_1 = "C:/Kai/git/GomocupJudge/engine",
        working_dir_2 = "C:/Kai/git/GomocupJudge/engine",
        tolerance = 1000)

    for i in xrange(20):
        msg, x, y = test.next_move()
        print '['+str(i)+']', x, y
        print msg
        test.print_board()
        
if __name__ == '__main__':
    main()
