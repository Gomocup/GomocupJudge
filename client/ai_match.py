import sys
from old_protocol import old_protocol
from new_protocol import new_protocol
from check_forbid import check_forbid
from utility import *

class ai_match(object):
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
                 tolerance = 1000,
                 settings = {},
                 special_rule = ""):
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
        self.settings = settings
        self.special_rule = special_rule
        self.engine_1 = None
        self.engine_2 = None
        
        self.board = [[0 for i in xrange(self.board_size)] for j in xrange(self.board_size)]
        for i in xrange(len(self.opening)):
            x, y = self.opening[i]
            self.board[x][y] = i % 2 + 1

        self.move_num = 0
        self.last_move = (-1, -1)
        self.board_1 = [[(0,0) for i in xrange(self.board_size)] for j in xrange(self.board_size)]
        self.board_2 = [[(0,0) for i in xrange(self.board_size)] for j in xrange(self.board_size)]

    def next_move(self):
        #print self.move_num
        if self.move_num == 0:
            for i in xrange(len(self.opening)):
                x, y = self.opening[i]
                if len(self.opening) % 2 == i % 2:
                    self.board_1[x][y] = (i+1, 1)
                    self.board_2[x][y] = (i+1, 2)
                else:
                    self.board_1[x][y] = (i+1, 2)
                    self.board_2[x][y] = (i+1, 1)

            if self.engine_1 is None:
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
            else:
                self.engine_1.init_board(self.board_1)
                
            msg, x, y = self.engine_1.start()
            t = self.engine_1.timeused
        elif self.move_num == 1:
            if self.engine_2 is None:
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
            else:
                self.engine_2.init_board(self.board_2)
            msg, x, y = self.engine_2.start()
            t = self.engine_2.timeused
        else:
            if self.move_num % 2 == 0:
                msg, x, y = self.engine_1.turn(self.last_move[0], self.last_move[1])
                t = self.engine_1.timeused
            else:
                msg, x, y = self.engine_2.turn(self.last_move[0], self.last_move[1])
                t = self.engine_2.timeused

        self.move_num += 1
        self.board_1[x][y] = (len(self.opening)+self.move_num, (self.move_num + 1) % 2 + 1)
        self.board_2[x][y] = (len(self.opening)+self.move_num, (self.move_num + 0) % 2 + 1)
        self.last_move = (x,y)
        return msg, x, y, t

    #return
    # -4: timeout
    # -3: crash
    # -2: foul
    # -1: illegal
    #  0: normal
    #  1: win
    def make_move(self, x, y, color):
        if self.board[x][y] != 0:
            return -1

        if self.rule == 4 and color == 1 and check_forbid(self.board, x, y):
            return -2
        
        self.board[x][y] = color
        nx = [0, 1, -1, 1]
        ny = [1, 0,  1, 1]
        for d in range(4):
            c = 1
            blocked = 0
            _x, _y = x, y
            for i in range(1,6):
                _x += nx[d]
                _y += ny[d]
                if _x<0 or _x>=self.board_size:
                    blocked += 1
                    break
                if _y<0 or _y>=self.board_size:
                    blocked += 1
                    break
                if self.board[_x][_y] != self.board[x][y]:
                    if self.board[_x][_y] != 0:
                        blocked += 1
                    break
                c += 1
            _x, _y = x, y
            for i in range(1,6):
                _x -= nx[d]
                _y -= ny[d]
                if _x<0 or _x>=self.board_size:
                    blocked += 1
                    break
                if _y<0 or _y>=self.board_size:
                    blocked += 1
                    break
                if self.board[_x][_y] != self.board[x][y]:
                    if self.board[_x][_y] != 0:
                        blocked += 1
                    break
                c += 1
            if (self.rule == 0 or self.rule == 4) and c >= 5:
                return 1
            if self.rule == 1 and c == 5:
                return 1
            if self.rule == 9 and c == 5 and blocked < 2:
                return 1
            if self.rule == 8 and (c > 5 or (c==5 and blocked < 2)):
                return 1
        return 0        

    def play(self):
        msg = ''
        psq = []
        status = 0
        result = endby = 0
        posswap = False

        if self.special_rule == "swap2":
            try:
                i = 0
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
                _msg, x, y = self.engine_1.swap2board()
                t = self.engine_1.timeused
                print x,y,t
                if len(y) != 3:
                    status = -1
                else:
                    for j in range(len(y)):
                        if self.board[y[j][0]][y[j][1]] == 0:
                            self.board_2[y[j][0]][y[j][1]] = (j+1, (j+1) % 2 + 1)
                            self.board[y[j][0]][y[j][1]] = j % 2 + 1
                            self.opening += [y[j]]
                            psq += [(y[j][0],y[j][1],0)]
                        else:
                            status = -1
                    msg += '(1) (2) (3) ' + _msg + str(int(t)) + 'ms\n'
                assert(status == 0)
                
                i = 1
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
                _msg, x, y = self.engine_2.swap2board()
                t = self.engine_1.timeused
                print x,y,t
                if len(y) == 0: #swap
                    msg += '(3-swap) ' + _msg + str(int(t)) + 'ms\n'
                    posswap = True
                elif len(y) == 1: #stay with its color
                    if self.board[y[0][0]][y[0][1]] == 0:
                        self.board[y[0][0]][y[0][1]] = 2
                        self.opening += [y[0]]
                        msg += '(3-stay with its color) (4) ' + _msg + str(int(t)) + 'ms\n'
                        psq += [(y[0][0],y[0][1],0)]
                    else:
                        status = -1
                elif len(y) == 2: #put two stones
                    i = 2
                    for j in range(len(y)):
                        if self.board[y[j][0]][y[j][1]] == 0:
                            self.board_2[y[j][0]][y[j][1]] = (j+4, j % 2 + 1)
                            self.board[y[j][0]][y[j][1]] = (j+1) % 2 + 1
                            self.opening += [y[j]]
                            psq += [(y[j][0],y[j][1],0)]
                        else:
                            status = -1
                    msg += '(3-put two stones) (4) (5) ' + _msg + str(int(t)) + 'ms\n'
                    self.engine_1.init_board(self.board_2)
                    _msg, x, y = self.engine_1.swap2board()
                    t = self.engine_1.timeused
                    print x,y,t
                    self.engine_1, self.engine_2 = self.engine_2, self.engine_1
                    if len(y) == 0: #swap
                        msg += '(5-swap) ' + _msg + str(int(t)) + 'ms\n'
                    elif len(y) == 1: #stay with its color
                        posswap = True
                        if self.board[y[0][0]][y[0][1]] == 0:
                            self.board[y[0][0]][y[0][1]] = 2
                            self.opening += [y[0]]
                            msg += '(5-stay with its color) (6) ' + _msg + str(int(t)) + 'ms\n'
                            psq += [(y[0][0],y[0][1],0)]
                        else:
                            status = -1
                    else:
                        status = -1
                else:
                    status = -1
                assert(status == 0)
                
            except Exception("TLE"):
                status = -4
            except Exception("MLE"):
                status = -3
            except Exception("FLE"):
                status = -3
            except:
                status = -3

            if status != 0:
                result = (i+1) % 2 + 1
                if status == -1:
                    endby = 3 #illegal coordinate
                elif status == -3:
                    endby = 4 #crash
                elif status == -4:
                    endby = 2 #timeout

        if status == 0:
            if "real_time_pos" in self.settings and self.settings["real_time_pos"] == 1:
                for i in xrange(len(psq)):
                    self.settings["send"]("pos " + psq_to_psq([psq[i]], self.board_size).encode("base64").replace("\n", "").replace("\r", ""))
                    self.settings["recv"](16) #received
            if "real_time_message" in self.settings and self.settings["real_time_message"] == 1:
                self.settings["send"]("message " + msg.encode("base64").replace("\n", "").replace("\r", ""))
                self.settings["recv"](16) #received
            if posswap:
                self.settings["send"]("pos swap")
                print "pos swap"
                self.settings["recv"](16) #received
            for i in xrange(len(self.opening), self.board_size**2):
                if self.rule == 4 and i >= self.board_size**2 - 25:
                    break
                try:
                    _msg, x, y, t = self.next_move()
                    print x,y,t
                    msgturn = '('+str(i+1)+') ' + _msg + str(int(t)) + 'ms\n'
                    psqturn = [(x,y,int(t))]
                    msg += msgturn
                    psq += psqturn
                    if len(psq) >= 3:
                        _psqturn = [(x,y,int(t)-psq[len(psq)-3][2])]
                    else:
                        _psqturn = [(x,y,int(t))]
                    status = self.make_move(x, y, i%2+1)
                    if status == -2:
                        msgturn = msgturn + "Forbidden move!\n"
                        msg += "Forbidden move!\n"
                        psq = psq[:-1]
                    if status != -2 and "real_time_pos" in self.settings and self.settings["real_time_pos"] == 1:
                        self.settings["send"]("pos " + psq_to_psq(_psqturn, self.board_size).encode("base64").replace("\n", "").replace("\r", ""))
                        self.settings["recv"](16) #received
                    if "real_time_message" in self.settings and self.settings["real_time_message"] == 1:
                        self.settings["send"]("message " + msgturn.encode("base64").replace("\n", "").replace("\r", ""))
                        self.settings["recv"](16) #received
                except Exception("TLE"):
                    status = -4
                except Exception("MLE"):
                    status = -3
                except Exception("FLE"):
                    status = -3
                except:
                    status = -3

                if status != 0:
                    if status == 1:
                        result = i % 2 + 1
                        endby = 0 #draw/five
                    else:
                        result = (i+1) % 2 + 1
                        if status == -1:
                            endby = 3 #illegal coordinate
                        elif status == -2:
                            endby = 1 #foul
                        elif status == -3:
                            endby = 4 #crash
                        elif status == -4:
                            endby = 2 #timeout
                    break
        print endby
        sys.stdout.flush()
        try:
            self.engine_1.clean()
        except:
            pass
        try:
            self.engine_2.clean()
        except:
            pass
        if status == 0:
            result = 0 #draw
            endby = 0 #draw/five
        return msg, psq, result, endby
        
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
    test = ai_match(
        board_size = 20,
        opening = [(10,10)],
        cmd_1 = "C:/GomocupJudge/client/match/2b6d35c3ca7a8ec313373b4a568069f8/pbrain-sWINe2017_64.exe",
        cmd_2 = "C:/GomocupJudge/client/match/1b7dbb708ee4c6d9398b9a0a878961c8/QMENTAT6.exe",
        protocol_1 = "new",
        protocol_2 = "old",
        timeout_turn_1 = 5000,
        timeout_turn_2 = 5000,
        timeout_match_1 = 120000,
        timeout_match_2 = 120000,
        max_memory_1 = 350*1024*1024,
        max_memory_2 = 350*1024*1024,
        game_type = 1,
        rule = 0,
        folder_1 = "C:/GomocupJudge/client/match/folder/2b6d35c3ca7a8ec313373b4a568069f8/",
        folder_2 = "C:/GomocupJudge/client/match/folder/1b7dbb708ee4c6d9398b9a0a878961c8/",
        working_dir_1 = "C:/GomocupJudge/client/match/2b6d35c3ca7a8ec313373b4a568069f8/",
        working_dir_2 = "C:/GomocupJudge/client/match/1b7dbb708ee4c6d9398b9a0a878961c8/",
        tolerance = 1000)

    '''
    for i in xrange(20):
        msg, x, y, t = test.next_move()
        print '['+str(i)+']', x, y
        print msg
        test.print_board()
    '''

    msg, pos, ret, endby = test.play()
    print msg, pos, ret, endby
        
if __name__ == '__main__':
    main()
