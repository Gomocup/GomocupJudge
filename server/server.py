import time
import socket
import sys
import string
import threading
import platform
import re
import os
import hashlib
import base64
import Queue
import subprocess
import random
import ftplib
import paramiko

def get_md5(curpath, engine):
    engine_path = curpath + slash + 'engine' + slash + engine
    if os.path.isfile(engine_path):
        fin = open(engine_path, 'rb')
        reads = fin.read()
        fin.close() 
        if not reads:
            return None
        md5 = hashlib.md5(reads).hexdigest()
        return md5
    else:
        return None

def get_base64(curpath, engine):
    engine_path = curpath + slash + 'engine' + slash + engine
    if os.path.isfile(engine_path):
        fin = open(engine_path, 'rb')
        reads = fin.read()
        fin.close()
        if not reads:
            return None
        return re.sub(r'\s+', '', base64.b64encode(reads))
    else:
        return None        

class Match:
    def __init__(self, curpath, tournament, tur_name, matchid, player1, player2, round, board_size, rule, opening, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message):
        self.curpath = curpath
        self.tournament = tournament
        self.tur_name = tur_name
        self.matchid = matchid
        self.player1 = player1
        self.player2 = player2
        self.round = round    
        self.group_id = (self.player1[0], self.player2[0], self.round)
        self.board_size = board_size
        self.rule = rule
        self.opening = opening        
        self.reverse = opening_reverse(opening)
        self.time_turn = time_turn
        self.time_match = time_match
        self.tolerance = tolerance
        self.memory = memory
        self.real_time_pos = real_time_pos
        self.real_time_message = real_time_message
        self.started = False
        self.result = None
        self.end_with = None
        self.time1 = 0
        self.time2 = 0
        self.move1 = 0
        self.move2 = 0
        self.client = None
    
    def assign(self, client):
        self.client = client
        self.started = True
        #print repr(self.player1)
        #print repr(self.player2)
        client.assign(self)
        
    def reinit(self):
        self.started = False
        self.result = None
        self.end_with = None
        self.time1 = 0
        self.time2 = 0
        self.move1 = 0
        self.move2 = 0
        self.client = None
        
    def to_string(self):
        return repr(self.group_id) + '\t' + repr(self.result) + '\t' + repr(self.end_with) + '\t' + repr(self.time1) + '\t' + repr(self.time2) + '\t' + repr(self.move1) + '\t' + repr(self.move2)
    
    def read_string(self, cur_str):
        cur_group_id, self.result, self.end_with, self.time1, self.time2, self.move1, self.move2 = map(eval, cur_str.split("\t"))
        if self.result != None:
            self.started = True
        else:
            self.started = False

def soft_div(a, b, un):
    if b != 0:
        return str(round(a * 1.0 / b)) + un
    else:
        return '-'
        
class Tournament:
    def __init__(self, curpath, engines, tur_name, board_size, rule, openings, is_tournament, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message):
        self.curpath = curpath
        self.enginepath = curpath + slash + 'engine'
        self.engines = engines
        self.md5s = []
        for engine in self.engines:
            self.md5s.append(get_md5(curpath, engine))
        self.nengines = len(self.engines)
        self.tur_name = tur_name
        self.board_size = board_size
        self.rule = rule
        self.openings = openings
        self.round = len(self.openings)
        self.is_tournament = is_tournament
        self.time_turn = time_turn
        self.time_match = time_match
        self.tolerance = tolerance
        self.memory = memory
        self.real_time_pos = real_time_pos
        self.real_time_message = real_time_message
        self.matches = []
        self.ratings = [(i, None, self.engines[i]) for i in range(self.nengines)]
        self.lresult = [[0, 0, 0] for i in range(self.nengines)]
        self.mresult = [[[0, 0, 0] for i in range(self.nengines)] for j in range(self.nengines)]
        self.times = [0 for i in range(self.nengines)]
        self.moves = [0 for i in range(self.nengines)]
        self.games = [0 for i in range(self.nengines)]
        self.timeouts = [0 for i in range(self.nengines)]
        self.crashes = [0 for i in range(self.nengines)]
        self.wins = [[0, 0] for i in range(self.nengines)]
        self.losses = [[0, 0] for i in range(self.nengines)]
        self.draws = [[0, 0] for i in range(self.nengines)]
        self.valids = [True for i in range(self.nengines)]
        matchcount = 0
        for i in range(self.round):
            if self.is_tournament:
                for j in range(self.nengines):
                    for k in range(self.nengines):
                        if j < k:
                            player1 = (j, self.engines[j], self.md5s[j])
                            player2 = (k, self.engines[k], self.md5s[k])
                            cur_match = Match(curpath, self, tur_name, matchcount, player1, player2, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                            self.matches.append(cur_match)
                            matchcount += 1
                            cur_match = Match(curpath, self, tur_name, matchcount, player2, player1, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                            self.matches.append(cur_match)
                            matchcount += 1
            else:
                for k in range(1, self.nengines):
                    player1 = (0, self.engines[0], self.md5s[0])
                    player2 = (k, self.engines[k], self.md5s[k])
                    cur_match = Match(curpath, self, tur_name, matchcount, player1, player2, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                    self.matches.append(cur_match)
                    matchcount += 1
                    cur_match = Match(curpath, self, tur_name, matchcount, player2, player1, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                    self.matches.append(cur_match)
                    matchcount += 1
        self.nmatches = len(self.matches)
        self.leftmatches = self.nmatches
        self.load_state()
        self.save_state()
        self.statistics()
        self.print_table()
        self.print_statistics()
    
    def statistics(self):
        self.times = [0 for i in range(self.nengines)]
        self.moves = [0 for i in range(self.nengines)]
        self.games = [0 for i in range(self.nengines)]
        self.timeouts = [0 for i in range(self.nengines)]
        self.crashes = [0 for i in range(self.nengines)]
        self.wins = [[0, 0] for i in range(self.nengines)]
        self.losses = [[0, 0] for i in range(self.nengines)]
        self.draws = [[0, 0] for i in range(self.nengines)]
        self.valids = [True for i in range(self.nengines)]
        for match in self.matches:
            if match.result != None:
                player1 = match.player1[0]
                player2 = match.player2[0]
                self.times[player1] += match.time1
                self.times[player2] += match.time2
                self.moves[player1] += match.move1
                self.moves[player2] += match.move2
                self.games[player1] += 1
                self.games[player2] += 1
                if match.end_with == 2:
                    if match.result == 1:
                        self.timeouts[player2] += 1
                    elif match.result == 2:
                        self.timeouts[player1] += 1
                elif match.end_with == 3 or match.end_with == 4:
                    if match.result == 1:
                        self.crashes[player2] += 1
                    elif match.result == 2:
                        self.crashes[player1] += 1
                if not match.reverse:
                    if match.result == 1:
                        self.wins[player1][0] += 1
                        self.losses[player2][1] += 1
                    elif match.result == 2:
                        self.wins[player2][1] += 1
                        self.losses[player1][0] += 1
                    else:
                        self.draws[player1][0] += 1
                        self.draws[player2][1] += 1
                else:
                    if match.result == 1:
                        self.wins[player1][1] += 1
                        self.losses[player2][0] += 1
                    elif match.result == 2:
                        self.wins[player2][0] += 1
                        self.losses[player1][1] += 1
                    else:
                        self.draws[player1][1] += 1
                        self.draws[player2][0] += 1
        for i in range(self.nengines):
            if self.games[i] > 0 and (self.timeouts[i] + self.crashes[i]) * 1.0 / self.games[i] > 0.1:
                self.valids[i] = False
        
    def generate_pgn(self):
        result_path = self.curpath + slash + 'result' + slash + tur_name
        pgn_file = result_path + slash + "result.pgn"
        fout = open(pgn_file, 'w')
        nmatches = 0
        for match in self.matches:
            if match.result != None:
                if self.valids[match.player1[0]] == False or self.valids[match.player2[0]] == False:
                    continue
                fout.write("[White \"" + str(match.player1[0]) + "#" + match.player1[1].rsplit('.', 1)[0] + "\"]\n")
                fout.write("[Black \"" + str(match.player2[0]) + "#" + match.player2[1].rsplit('.', 1)[0] + "\"]\n")
                if match.result == 1:
                    cur_result = "1-0"
                elif match.result == 2:
                    cur_result = "0-1"
                else:
                    cur_result = "1/2-1/2"
                fout.write("[Result \"" + cur_result + "\"]\n")
                fout.write("\n")
                fout.write("1. d4 d5 " + cur_result + "\n")
                fout.write("\n")
                nmatches += 1
        fout.close()
        if nmatches > 0:
            return True
        else:
            return False
        
    def compute_elo(self):        
        result_path = self.curpath + slash + 'result' + slash + tur_name
        ratings = []
        if self.generate_pgn():
            bayeselo_exe = self.curpath + slash + "bayeselo.exe"
            p = subprocess.Popen([bayeselo_exe], bufsize = 1048576, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
            pin, pout = p.stdin, p.stdout
            pin.write("readpgn " + result_path + slash + "result.pgn\n")
            pin.flush()
            pin.write("elo\n")
            pin.flush()
            pin.write("offset 1600\n")
            pin.flush()
            pin.write("mm\n")
            pin.flush()
            pin.write("exactdist\n")
            pin.flush()
            pin.write("ratings >" + result_path + slash + "ratings.txt\n")
            pin.flush()
            pin.write("los 0 200 4 >" + result_path + slash + "los.txt\n")
            pin.flush()
            pin.write("x\n")
            pin.flush()
            pin.write("x\n")
            pin.flush()
            p.wait()
            fin = open(result_path + slash + "ratings.txt", 'r')
            reads = fin.readline()
            while True:
                reads = fin.readline()
                if not reads:
                    break
                reads = reads.strip()
                reads = re.split(r'\s+', reads)
                ratings.append((string.atoi(reads[1].split('#', 1)[0]), string.atoi(reads[2]), reads[1].split('#', 1)[1], string.atoi(reads[4])))
            fin.close()
        inratings = [False for i in range(self.nengines)]
        for engine_id, rating, engine_name, rating_m in ratings:
            inratings[engine_id] = True
        for i in range(self.nengines):
            if not inratings[i]:
                ratings.append((i, None, self.engines[i].rsplit('.', 1)[0], None))
        self.ratings = ratings
        
    def print_table(self):
        result_path = self.curpath + slash + 'result' + slash + tur_name
        self.compute_elo()
        fout = open(result_path + slash + "_table.html", 'w')
        fout.write("<HTML>\n<HEAD>\n<TITLE>Piskvork tournament result</TITLE>\n<LINK href=\"piskvork.css\" type=text/css rel=stylesheet>\n</HEAD>\n")
        fout.write("<BODY>\n")
        fout.write("<TABLE border=1 class=\"result\">\n")
        #fout.write("<LINK href=\"http://gomocup.org/wp-content/tournaments/tables/piskvork.css\" type=text/css rel=stylesheet/>\n")
        fout.write("<TBODY align=center>\n")
        fout.write("<TR><TH>#</TH><TH>Name</TH><TH>Elo</TH><TH>Total</TH>")
        cur_rank = 0
        for engine_id, rating, engine_name, rating_m in self.ratings:
            cur_rank += 1
            cur_name = engine_name
            short_name = cur_name[:min(3, len(cur_name))]
            fout.write("<TH><NUM>" + str(cur_rank) + "</NUM><BR/><NAME>" + short_name + "<NAME></TH>")
        fout.write("</TR>\n")
        cur_rank = 0
        for engine_id, rating, engine_name, rating_m in self.ratings:
            cur_rank += 1
            cur_name = engine_name
            cur_lresult = self.lresult[engine_id]
            if rating == None:
                rating_str = "-"
            else:
                rating_str = str(rating)
            fout.write("<TR><TD><NUM>" + str(cur_rank) + "</NUM></TD><TD><NAME>" + cur_name + "</NAME></TD><TD>" + rating_str + "</TD><TD>" + str(cur_lresult[0]) + ":" + str(cur_lresult[1]) + "</TD>")
            for engine_id_2, rating_2, engine_name_2, rating_m_2 in self.ratings:
                if engine_id == engine_id_2:
                    fout.write("<TD class=\"dash\">-</TD>")
                else:
                    cur_mresult = self.mresult[engine_id][engine_id_2]
                    winf = cur_mresult[0] - cur_mresult[1]
                    if winf > 0:
                        fout.write("<TD class=\"win\">" + str(cur_mresult[0]) + ":" + str(cur_mresult[1]) + "</TD>")
                    elif winf == 0:
                        fout.write("<TD class=\"draw\">" + str(cur_mresult[0]) + ":" + str(cur_mresult[1]) + "</TD>")
                    else:
                        fout.write("<TD class=\"loss\">" + str(cur_mresult[0]) + ":" + str(cur_mresult[1]) + "</TD>")
            fout.write("</TR>\n")
        fout.write("</TBODY>\n</TABLE>\n</BODY>\n</HTML>\n")
        fout.close()
        ssh_upload(result_path + slash + "_table.html", False)
        
    def print_statistics(self):
        result_path = self.curpath + slash + 'result' + slash + tur_name
        fout = open(result_path + slash + "_result.txt", 'w')
        cur_rank = 0
        for engine_id, rating, engine_name, rating_m in self.ratings:
            cur_rank += 1
            if not rating:
                rating = '-'
            fout.write(str(cur_rank) + '. ' + engine_name + ' ' + str(rating) + '\n')
            fout.write('    wins: ' + str(self.wins[engine_id][0]) + '+' + str(self.wins[engine_id][1]) + ', ')
            fout.write('losses: ' + str(self.losses[engine_id][0]) + '+' + str(self.losses[engine_id][1]) + ', ')
            fout.write('draws: ' + str(self.draws[engine_id][0]) + '+' + str(self.draws[engine_id][1]) + '\n')
            fout.write('    timeouts: ' + str(self.timeouts[engine_id]) + ', ' + 'errors: ' + str(self.crashes[engine_id]) + ', ' + 'total games: ' + str(self.games[engine_id]) + '\n')
            fout.write('    time/game: ' + soft_div(self.times[engine_id], self.games[engine_id], 's') + ', ' + 'time/turn: ' + soft_div(self.times[engine_id] * 1000, self.moves[engine_id], 'ms') + ', ' + 'move/game: ' + soft_div(self.moves[engine_id], self.games[engine_id], '') + '\n')
            fout.write('\n')
        fout.close()
        ssh_upload(result_path + slash + "_result.txt", False)
              
    def assign_match(self, client):
        inv_ratings = {}
        for engine_id, rating, engine_name, rating_m in self.ratings:
            if rating != None:
                inv_ratings[engine_id] = (rating, rating_m)
            else:
                inv_ratings[engine_id] = (0, random.randint(0, 100))
        minelo = None
        minind = -1
        for i in range(self.nmatches):
            if self.matches[i].started == False:
                player1 = self.matches[i].player1[0]
                player2 = self.matches[i].player2[0]
                curelo = inv_ratings[player1][0] - inv_ratings[player1][1] + inv_ratings[player2][0] - inv_ratings[player2][1]
                if minelo == None or curelo < minelo:
                    minelo = curelo
                    minind = i
        if minind < 0:
            return False
        else:
            self.matches[minind].assign(client)
            return True        
        
    def save_state(self):
        result_path = self.curpath + slash + 'result' + slash + tur_name
        state_path = result_path + slash + "state.txt"
        fout = open(state_path, 'w')
        for match in self.matches:
            fout.write(match.to_string() + '\n')
        fout.close()
       
    def load_state(self):
        result_path = self.curpath + slash + 'result' + slash + tur_name
        state_path = result_path + slash + "state.txt"
        try:
            fin = open(state_path, 'r')
        except:
            return
        leftmatches = 0
        for match in self.matches:
            readstr = fin.readline()
            if readstr:
                match.read_string(readstr.strip())
                if match.result == None:
                    leftmatches += 1
            else:
                break
        self.leftmatches = leftmatches
        fin.close()
        self.restore_result()        
        
    def restore_result(self):
        for match in self.matches:
            player1 = match.player1[0]
            player2 = match.player2[0]
            if match.result != None:
                if match.result == 1:
                    self.lresult[player1][0] += 1
                    self.lresult[player2][1] += 1
                    self.mresult[player1][player2][0] += 1
                    self.mresult[player2][player1][1] += 1
                elif match.result == 2:
                    self.lresult[player1][1] += 1
                    self.lresult[player2][0] += 1
                    self.mresult[player1][player2][1] += 1
                    self.mresult[player2][player1][0] += 1
                else:
                    self.lresult[player1][2] += 1
                    self.lresult[player2][2] += 1
                    self.mresult[player1][player2][2] += 1
                    self.mresult[player2][player1][2] += 1
        
def cmp_result(result1, result2):
    win1 = result1[1][0] * 1.0 + result1[1][2] * 0.5
    loss1 = result1[1][1] * 1.0 + result1[1][2] * 0.5
    win2 = result2[1][0] * 1.0 + result2[1][2] * 0.5
    loss2 = result2[1][1] * 1.0 + result2[1][2] * 0.5
    if loss1 > 0 and loss2 > 0:
        ret = win1 / loss1 - win2 / loss2
        if ret > 0:
            return 1
        elif ret < 0:
            return -1
        else:
            return 0
    elif loss1 == 0 and loss2 > 0:
        return 1
    elif loss1 > 0 and loss2 == 0:
        return -1
    else:
        return int(win1 - win2)
        
def extend_pos(pos, board_size, player1, player2):
    return 'Piskvorky ' + str(board_size) + 'x' + str(board_size) + ', 11:11, 0\n' + pos + player1 + '\n' + player2 + '\n' + '-1\n'
    
def parse_pos(pos, opening):
    len_opening = opening_length(opening)
    spos = pos.strip()
    if spos:
        times = map(lambda x: string.atoi(x.split(',')[-1]), pos.strip().split('\n'))[len_opening:]
    else:
        times = []
    len_times = len(times)
    times1 = times[0::2]
    times2 = times[1::2]
    time1 = sum(times1)
    time2 = sum(times2)
    move1 = len(times1)
    move2 = len(times2)
    return (time1, time2, move1, move2)
                    
class Client_state:
    def __init__(self, curpath, addr):
        self.curpath = curpath
        self.addr = addr
        self.active = False
        self.matchid = None
        self.match = None
        self.tournament = None
        self.started = False
        self.ended = False
        self.ended_all = False
        self.active_time = None
        self.time_match = None
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = None
        self.sent_real_time_message = None
        self.tmp_pos = None
        self.cur_pos = None
        self.tmp_message = None
        self.cur_message = None
    
    def assign(self, match):
        self.active = True
        self.matchid = match.matchid
        self.match = match
        self.tournament = match.tournament
        self.started = False
        self.active_time = time.time()
        self.time_match = match.time_match
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = False
        self.sent_real_time_message = False
        self.tmp_pos = None
        self.cur_pos = None
        self.tmp_message = None
        self.cur_message = None
        outstr = 'Game ' + str(self.match.group_id) + ' started on Client ' + self.addr + '.'
        print_log(outstr)
            
    def end(self, pos, message, result, end_with):
        pos = base64.b64decode(pos)
        pos = opening_pos2psq(self.match.opening) + pos
        message = base64.b64decode(message)
        result = string.atoi(result)
        if result > 0:
            if opening_reverse(self.match.opening):
                result = 3 - result
        end_with = string.atoi(end_with)
        round = self.match.round
        player1 = self.match.player1
        player2 = self.match.player2
        tur_name = self.match.tur_name
        pos_name = str(round) + '_' + str(player1[0]) + '_' + str(player2[0]) + '.psq'
        result_path = self.curpath + slash + 'result' + slash + tur_name
        pos_path = result_path + slash + pos_name
        fpos = open(pos_path, 'w')
        if not self.match.reverse:
            fpos.write(extend_pos(pos, self.match.board_size, self.match.player1[1], self.match.player2[1]))
        else:
            fpos.write(extend_pos(pos, self.match.board_size, self.match.player2[1], self.match.player1[1]))
        fpos.write(str(result) + ',' + self.tournament.tur_name + '\n')
        fpos.close()
        if upload_offline_result:
            ssh_upload(pos_path, False)
        fmessage = open(result_path + slash + 'message.txt', 'a')
        fmessage.write(message)
        fmessage.write('\n--> ' + pos_path + '\n\n')
        fmessage.close()
        ssh_upload(result_path + slash + 'message.txt', False)
        self.match.result = result
        self.match.end_with = end_with  
        self.match.time1, self.match.time2, self.match.move1, self.match.move2 = parse_pos(pos, self.match.opening)
        cur_tur = self.tournament
        player1_id = player1[0]
        player2_id = player2[0]
        if result == 1:
            cur_tur.lresult[player1_id][0] += 1
            cur_tur.lresult[player2_id][1] += 1
            cur_tur.mresult[player1_id][player2_id][0] += 1
            cur_tur.mresult[player2_id][player1_id][1] += 1
        elif result == 2:
            cur_tur.lresult[player1_id][1] += 1
            cur_tur.lresult[player2_id][0] += 1
            cur_tur.mresult[player1_id][player2_id][1] += 1
            cur_tur.mresult[player2_id][player1_id][0] += 1
        else:
            cur_tur.lresult[player1_id][2] += 1
            cur_tur.lresult[player2_id][2] += 1
            cur_tur.mresult[player1_id][player2_id][2] += 1
            cur_tur.mresult[player2_id][player1_id][2] += 1
        
        outstr = 'Game ' + str(self.match.group_id) + ' finished on Client ' + self.addr + '.'
        print_log(outstr)
        
        self.active = False
        self.matchid = None
        self.match = None
        self.started = False
        self.ended = True
        self.active_time = None
        self.time_match = None
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = None
        self.sent_real_time_message = None
        self.tmp_pos = None
        self.cur_pos = None
        self.tmp_message = None
        self.cur_message = None
        
        self.tournament.save_state()
        self.tournament.statistics()
        self.tournament.print_table()
        self.tournament.print_statistics()
        
        cur_tur.leftmatches -= 1
        if cur_tur.leftmatches == 0:
            return True
        else:
            return False
            
    def save_pos(self, pos):
        pos = base64.b64decode(pos)
        if not self.cur_pos:
            self.cur_pos = opening_pos2psq(self.match.opening) + pos
        else:
            self.cur_pos = self.cur_pos + pos
        pos_name = self.addr.replace('.', '_').replace(':', '_') + '.psq'
        tmp_path = self.curpath + slash + 'result' + slash + 'tmp'
        if os.path.exists(tmp_path):
            if not os.path.isdir(tmp_path):
                os.remove(tmp_path)
                os.makedirs(tmp_path)
        else:
            os.makedirs(tmp_path)
        pos_path = tmp_path + slash + pos_name
        fpos = open(pos_path, 'w')
        if not self.match.reverse:
            fpos.write(extend_pos(self.cur_pos, self.match.board_size, self.match.player1[1], self.match.player2[1]))
        else:
            fpos.write(extend_pos(self.cur_pos, self.match.board_size, self.match.player2[1], self.match.player1[1]))
        fpos.close()
        if random.random() < upload_ratio:
            ssh_upload(pos_path, True)
        
    def save_message(self, message):
        message = base64.b64decode(message)
        if not self.cur_message:
            self.cur_message = message
        else:
            self.cur_message = self.cur_message + message
        message_name = self.addr.replace('.', '_').replace(':', '_') + '.txt'    
        tmp_path = self.curpath + slash + 'result' + slash + 'tmp'
        if os.path.exists(tmp_path):
            if not os.path.isdir(tmp_path):
                os.remove(tmp_path)
                os.makedirs(tmp_path)
        else:
            os.makedirs(tmp_path)
        message_path = tmp_path + slash + message_name
        fmessage = open(message_path, 'w')
        fmessage.write(cur_message)
        fmessage.close()
        ssh_upload(message_path, True)
    
    def process(self, output_queue):
        if self.active:
            if self.has_player1 == None:
                self.ask = 'player1'
                output_queue.put((self.addr, "engine exist " + self.match.player1[2]))
            elif self.has_player1 == False:
                self.ask = 'player1'
                output_queue.put((self.addr, "engine send " + base64.b64encode(self.match.player1[1]) + " " + get_base64(self.curpath, self.match.player1[1])))
            elif self.has_player2 == None:
                self.ask = 'player2'
                output_queue.put((self.addr, "engine exist " + self.match.player2[2]))
            elif self.has_player2 == False:
                self.ask = 'player2'
                output_queue.put((self.addr, "engine send " + base64.b64encode(self.match.player2[1]) + " " + get_base64(self.curpath, self.match.player2[1])))
            elif self.sent_real_time_pos == False:
                self.ask = 'real_time_pos'
                if self.match.real_time_pos == True:
                    output_queue.put((self.addr, "set real_time_pos 1"))
                else:
                    output_queue.put((self.addr, "set real_time_pos 0"))
            elif self.sent_real_time_message == False:
                self.ask = 'real_time_message'
                if self.match.real_time_message == True:
                    output_queue.put((self.addr, "set real_time_message 1"))
                else:
                    output_queue.put((self.addr, "set real_time_message 0"))
            elif self.tmp_pos != None:
                self.save_pos(self.tmp_pos)
                self.tmp_pos = None
                output_queue.put((self.addr, "received"))
            elif self.tmp_message != None:
                self.save_message(self.tmp_message)
                self.tmp_message = None
                output_queue.put((self.addr, "received"))
            elif not self.started:
                self.ask = 'match'
                output_queue.put((self.addr, "match new " + self.match.player1[2] + ' ' + self.match.player2[2] + \
                                  ' ' + self.match.time_turn + ' ' + self.match.time_match + ' ' + self.match.rule + \
                                  ' ' + self.match.tolerance + ' ' + self.match.opening + ' ' + self.match.board_size + \
                                  ' ' + self.match.memory))
        else:
            if self.ended:            
                self.ask = None
                output_queue.put((self.addr, "ok"))
                if self.tournament.assign_match(self):
                    self.process(output_queue)
                else:
                    output_queue.put((self.addr, "end"))
                    self.ended_all = True
        

def print_log(outstr, file = None):
    curtime = time.time()
    strdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(curtime))
    outstring = '[' + strdate + ']' + ' ' + outstr    
    if not file:
        print outstring
        file = log_file
    fout = open(file, 'a')
    fout.write(outstring)
    fout.write('\n')
    fout.close()
   

def connect_addr(addr, trecv, conn):
    outstr = 'Client ' + addr + ' connected.'
    print_log(outstr)
    trecvs[addr] = (trecv, conn)
    
def disconnect_addr(addr):
    outstr = 'Client ' + addr + ' disconnected.'
    print_log(outstr)
    if trecvs.has_key(addr):
        del trecvs[addr]

def recv_client(conn, addr):
    global recv_str, recv_mutex
    while True:
        try:
            data = conn.recv(5242800)
            if not data:
                disconnect_addr(addr)
                return
            if recv_mutex.acquire():
                if not recv_str.has_key(addr):
                    recv_str[addr] = ''
                recv_str[addr] = recv_str[addr] + data
                sdata = recv_str[addr].split('\n')
                recv_str[addr] = sdata[-1]
                sdata = sdata[:-1]
                for edata in sdata:
                    input_queue.put((addr, edata))
                    out_str = repr(('input', addr, edata))
                    print_log(out_str, net_log_file)
                recv_mutex.release()
        except:
            disconnect_addr(addr)
            if clients_state.has_key(addr):
                if clients_state[addr].match:
                    if clients_state[addr].match.result == None:                        
                        outstr = 'Game ' + repr(clients_state[addr].match.group_id) + ' failed on Client ' + addr + '.'
                        print_log(outstr)
                        clients_state[addr].match.reinit()
                del clients_state[addr]
            return

def output_client():
    while(True):    
        addr, outstr = output_queue.get()
        out_str = repr(('output', addr, outstr))
        print_log(out_str, net_log_file)
        if trecvs.has_key(addr):
            conn = trecvs[addr][1]
            conn.sendall(outstr + '\n')
            if outstr == "end":
                disconnect_addr(addr)

def accept_client(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        addr = addr[0] + ':' + str(addr[1])
        trecv = threading.Thread(target = recv_client, args = (conn, addr))        
        connect_addr(addr, trecv, conn)
        trecv.start()
        clients_state[addr] = Client_state(curpath, addr)
        input_queue.put((addr, 'connected'))
        out_str = repr(('input', addr, 'connected'))
        print_log(out_str, net_log_file)
    conn.close()

def check_end():
    while True:
        end_flag = True
        for client_addr, client in clients_state.iteritems():
            if not client.ended_all:
                end_flag = False
        if not output_queue.empty():
            end_flag = False
        if not ftp_queue.empty():
            end_flag = False
        if tournament_state.leftmatches > 0:
            end_flag = False
        if end_flag:
            print_log("Server ended.")
            os._exit(0)
        time.sleep(1)
    
def parse_line_tournament(line):
    try:
        left, right = line.split('=')
        left = left.strip()
        right = right.strip()
        right = re.sub(r'\s+', ' ', right)
        if ' ' in right:
            return (left, right.split(' '))
        else:
            return (left, right)
    except:
        return None

def read_tournament(tournament_file):
    fin = open(tournament_file, 'r')
    tournament_map = {}
    while True:
        reads = fin.readline()
        if reads == None or len(reads) == 0:
            break
        line = parse_line_tournament(reads)
        if line:
            tournament_map[line[0]] = line[1]
    fin.close()
    return tournament_map

def parse_line_opening(line):
    try:
        line = line.strip()
        line = re.sub(r'\s+', '', line)
        return line
    except:
        return None

def opening2pos(opening, board_size):
    opening = opening.split(',')
    hboard = board_size / 2
    pos = ""
    for i in range(len(opening) / 2):
        curx = hboard + string.atoi(opening[2 * i])
        cury = hboard + string.atoi(opening[2 * i + 1])
        pos = pos + chr(ord('a') + curx)
        pos = pos + str(1 + cury)
    return pos

def opening_pos2psq(pos):
    poses = re.findall(r'[a-z][0-9]{1,2}', pos)
    cur_psq = ''
    for p in poses:
        px = ord(p[0]) - ord('a') + 1
        py = string.atoi(p[1:])
        cur_psq += str(px) + ',' + str(py) + ',' + '0\n'
    return cur_psq
 
def opening_reverse(pos):
    count = 0
    for c in pos:
        if c >= 'a' and c <= 'z':
            count += 1
    if count % 2 == 1:
        return True
    else:
        return False
        
def opening_length(pos):
    count = 0
    for c in pos:
        if c >= 'a' and c <= 'z':
            count += 1
    return count
    
def read_opening(opening_file, board_size):
    fin = open(opening_file, 'r')
    openings_list = []
    while True:
        reads = fin.readline()
        if reads == None or len(reads) == 0:
            break
        line = parse_line_opening(reads)
        if line:
            openings_list.append(opening2pos(line, board_size))
    fin.close()
    return openings_list
    
class Ftp_Queue:
    def __init__(self):
        self.mutex = threading.Lock()
        self.ele = []
    
    def get(self):
        while True:
            if self.mutex.acquire():
                if not self.ele:
                    self.mutex.release()
                else:
                    ret = self.ele[0]
                    del self.ele[0]
                    self.mutex.release()
                    return ret
            time.sleep(1)
    
    def put(self, ele):
        if self.mutex.acquire():
            if ele not in self.ele:
                self.ele.append(ele)
            self.mutex.release()
        
    def put_to_head(self, ele):
        if self.mutex.acquire():
            self.ele.insert(0, ele)
            self.mutex.release()
    
    def empty(self):
        if self.mutex.acquire():
            if not self.ele:
                self.mutex.release()
                return True
            else:
                self.mutex.release()
                return False

def ssh_connect():
    if remote_info:
        ssh_server = remote_info[0]
        if ':' in ssh_server:
            ssh_server, port = remote_info[0].rsplit(':', 1)
            port = string.atoi(port)
        else:
            port = 22
        username = remote_info[1]
        password = remote_info[2]
        tra = paramiko.Transport((ssh_server, port))
        tra.connect(username = username, password = password)
        sftp = paramiko.SFTPClient.from_transport(tra)
        return (tra, sftp)
    
def ssh_upload(upfile, is_online):
    if remote_info:
        ftp_queue.put((upfile, is_online))
                
def ssh_upload_process():
    global ftp_queue
    if remote_info:
        while True:
            upfile, is_online = ftp_queue.get()
            try:
                if is_online:
                    r_path = remote_info[3]
                else:
                    r_path = remote_info[4]
                if not r_path[-1] == '/':
                    r_path = r_path + '/'
                sftp.put(upfile, r_path + upfile.split(slash)[-1])
            except:
                ftp_queue.put_to_head((upfile, is_online))
    
def ssh_quit():
    tra.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print 'Parameter error!'
        exit(-1)
        
    trecvs = {}
    clients_state = {}
    input_queue = Queue.Queue(maxsize = 0)
    output_queue = Queue.Queue(maxsize = 0)

    curpath = sys.path[0]
    curos = platform.system()
    if curos == 'Windows':
        slash = '\\'
    else:
        slash = '/'

    recv_str = {}
    recv_mutex = threading.Lock()
    tournament_name = sys.argv[1]
    tournament_file = curpath + slash + 'tournament' + slash + tournament_name + '.txt'
    tournament = read_tournament(tournament_file)
    tur_name = tournament['name']
    board_size = tournament['board']
    rule = tournament['rule']
    opening_file = curpath + slash + 'opening' + slash + tournament['opening'] + '.txt'
    engines = tournament['engines']
    is_tournament = tournament['tournament']
    time_turn = tournament['time_turn']
    time_match = tournament['time_match']
    tolerance = tournament['tolerance']
    memory = tournament['memory']
    real_time_pos = string.atoi(tournament['real_time_pos'])
    if real_time_pos > 0:
        real_time_pos = True
    else:
        real_time_pos = False
    real_time_message = string.atoi(tournament['real_time_message'])
    if real_time_message > 0:
        real_time_message = True
    else:
        real_time_message = False
    try:
        upload_ratio = string.atof(tournament['upload_ratio'])
    except:
        upload_ratio = 1.0
    try:
        upload_offline_result = string.atoi(tournament['upload_offline_result'])
        if upload_offline_result == 1:
            upload_offline_result = True
        else:
            upload_offline_result = False
    except:
        upload_offline_result = True
    remote_name = tournament['remote']
    if remote_name:
        remote_file = curpath + slash + 'remote' + slash + remote_name + '.txt'
        remote = read_tournament(remote_file)
        remote_host = remote['host']
        remote_username = remote['username']
        remote_password = remote['password']
        remote_path = remote['remotepath']
        if not remote_path[-1] == '/':
            remote_path = remote_path + '/'
        remote_online_path = remote_path + '/'
        remote_tur_path = remote_path + tur_name + '/'
        remote_info = (remote_host, remote_username, remote_password, remote_online_path, remote_tur_path)
    else:
        remote_info = None
    ftp_queue = Ftp_Queue()
    tra, sftp = ssh_connect()
    result_dir = curpath + slash + 'result' + slash + tur_name
    if os.path.exists(result_dir):
        if not os.path.isdir(result_dir):
            os.remove(result_dir)
            os.makedirs(result_dir)
    else:
        os.makedirs(result_dir)
    log_file = result_dir + slash + 'log.txt'
    net_log_file = result_dir + slash + 'netlog.txt'
    state_file = result_dir + slash + 'state.txt'
    result_file = result_dir + slash + 'result.txt'
    message_file = result_dir + slash + 'message.txt'
    openings = read_opening(opening_file, string.atoi(board_size))

    tournament_state = Tournament(curpath, engines, tur_name, board_size, rule, openings, is_tournament, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)

    host = '0.0.0.0'
    port = string.atoi(sys.argv[2])
    taccept = threading.Thread(target = accept_client, args = (host, port))
    taccept.start()
    toutput = threading.Thread(target = output_client)
    toutput.start()
    tend = threading.Thread(target = check_end)
    tend.start()
    tftp = threading.Thread(target = ssh_upload_process)
    tftp.start()    
    
    print_log("Server started.")

    while(True):
        cur_input = input_queue.get()
        print cur_input
        inaddr = cur_input[0]
        instr = cur_input[1].strip()
        sinstr = re.split(r'\s', instr)
        cur_client = clients_state[inaddr]
        if len(sinstr) == 0:
            continue
        if sinstr[0].lower() == 'connected':
            tournament_state.assign_match(cur_client)
            cur_client.process(output_queue)
        elif sinstr[0].lower() == 'yes':
            if cur_client.ask == 'player1':
                cur_client.has_player1 = True
                cur_client.process(output_queue)
            elif cur_client.ask == 'player2':
                cur_client.has_player2 = True
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'no':
            if cur_client.ask == 'player1':
                cur_client.has_player1 = False
                cur_client.process(output_queue)
            elif cur_client.ask == 'player2':
                cur_client.has_player2 = False
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'ok':
            if cur_client.ask == 'match':
                cur_client.started == True
                cur_client.save_pos('')
            elif cur_client.ask == 'real_time_pos':
                cur_client.sent_real_time_pos = True
                cur_client.process(output_queue)
            elif cur_client.ask == 'real_time_message':
                cur_client.sent_real_time_message = True
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'received':
            if cur_client.ask == 'player1':
                cur_client.has_player1 = None
                cur_client.process(output_queue)
            elif cur_client.ask == 'player2':
                cur_client.has_player2 = None
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'match':
            if sinstr[1].lower() == 'finished':
                pos = sinstr[2]
                message = sinstr[3]
                result = sinstr[4]
                end_with = sinstr[5]
                cur_client.end(pos, message, result, end_with)
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'pos':
            if real_time_pos:
                tmp_pos = sinstr[1]
                cur_client.tmp_pos = tmp_pos
                cur_client.process(output_queue)
        elif sinstr[0].lower() == 'message':
            if real_time_message:
                tmp_message = sinstr[1]
                cur_client.tmp_message = tmp_message
                cur_client.process(output_queue)
