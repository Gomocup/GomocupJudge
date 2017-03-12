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

def get_md5(curpath, engine):
    engine_path = curpath + slash + 'engine' + slash + engine
    print engine_path
    print os.path.isfile(engine_path)
    if os.path.isfile(engine_path):
        fin = open(engine_path, 'rb')
        reads = fin.read()
        fin.close() 
        if not reads:
            return None
        md5 = hashlib.md5(reads).hexdigest()
        print md5
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
        return base64.b64encode(reads)
    else:
        return None        

class Match:
    def __init__(self, curpath, matchid, player1, player2, round, board_size, rule, opening, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message):
        self.curpath = curpath
        self.matchid = matchid
        self.player1 = player1
        self.player2 = player2
        self.round = round    
        self.board_size = board_size
        self.rule = rule
        self.opening = opening
        self.time_turn = time_turn
        self.time_match = time_match
        self.tolerance = tolerance
        self.memory = memory
        self.real_time_pos = real_time_pos
        self.real_time_message = real_time_message
        self.started = False
        self.result = None
        self.time1 = 0
        self.time2 = 0
        self.moves = 0
        self.client = None
        
    def setup(self, result, time1, time2, moves):
        self.result = result
        self.time1 = time1
        self.time2 = time2
        self.moves = moves
    
    def assign(self, client):
        self.client = client
        self.started = True
        client.assign(self)
        
        
class Tournament:
    def __init__(self, curpath, engines, tur_name, board_size, rule, openings, is_tournament, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message):
        self.curpath = curpath
        self.enginepath = curpath + slash + 'engine'
        self.engines = engines
        self.md5s = []
        for engine in self.engines:
            self.md5s.append(get_md5(curpath, engine))
        print self.md5s
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
        matchcount = 0
        for i in range(self.round):
            if self.is_tournament:
                for j in range(self.nengines):
                    for k in range(self.nengines):
                        if j < k:
                            player1 = (j, self.engines[j], self.md5s[j])
                            player2 = (k, self.engines[k], self.md5s[k])
                            cur_match = Match(curpath, matchcount, player1, player2, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                            self.matches.append(cur_match)
                            matchcount += 1
                            cur_match = Match(curpath, matchcount, player2, player1, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                            self.matches.append(cur_match)
                            matchcount += 1
            else:
                for k in range(1, self.nengines):
                    player1 = (0, self.engines[0], self.md5s[0])
                    player2 = (k, self.engines[k], self.md5s[k])
                    cur_match = Match(curpath, matchcount, player1, player2, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                    self.matches.append(cur_match)
                    matchcount += 1
                    cur_match = Match(curpath, matchcount, player2, player1, i, board_size, rule, openings[i], time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)
                    self.matches.append(cur_match)
                    matchcount += 1
        self.nmatches = len(self.matches)
              
    def assign_match(self, client):
        for i in range(self.nmatches):
            if self.matches[i].started == False:
                self.matches[i].assign(client)
                return True
        return False
                    
class Client_state:
    def __init__(self, curpath, addr):
        self.curpath = curpath
        self.addr = addr
        self.active = False
        self.matchid = None
        self.match = None
        self.started = False
        self.active_time = None
        self.time_match = None
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = None
        self.sent_real_time_message = None        
    
    def assign(self, match):
        self.active = True
        self.matchid = match.matchid
        self.match = match
        self.started = False
        self.active_time = time.time()
        self.time_match = match.time_match
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = False
        self.sent_real_time_message = False
            
    def end(self, pos, message):
        # TODO save pos message
        self.active = False
        self.matchid = None
        self.match = None
        self.started = False
        self.active_time = None
        self.time_match = None
        self.ask = None
        self.has_player1 = None
        self.has_player2 = None
        self.sent_real_time_pos = None
        self.sent_real_time_message = None
    
    def process(self, output_queue):
        if self.active:
            if self.has_player1 == None:
                self.ask = 'player1'
                print self.match.player1
                output_queue.put((self.addr, "engine exist " + self.match.player1[1] + ' ' + self.match.player1[2]))
            elif self.has_player1 == False:
                self.ask = 'player1'
                output_queue.put((self.addr, "engine send" + get_base64(self.curpath, self.match.player1[1])))
            elif self.has_player2 == None:
                self.ask = 'player2'
                output_queue.put((self.addr, "engine exist " + self.match.player2[1] + ' ' + self.match.player2[2]))
            elif self.has_player2 == False:
                self.ask = 'player2'
                output_queue.put((self.addr, "engine send" + get_base64(self.curpath, self.match.player2[1])))
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
            elif not self.started:
                self.ask = 'match'
                output_queue.put((self.addr, "match new " + str(self.match.matchid) + ' ' + self.match.player1[2] + ' ' + self.match.player2[2] + ' ' + self.match.time_turn + ' ' + self.match.time_match + ' ' + self.match.rule + ' ' + self.match.tolerance + ' ' + self.match.opening))
        

def print_log(outstr, file = None):
    curtime = time.time()
    strdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(curtime))
    outstring = '[' + strdate + ']' + ' ' + outstr
    print outstring
    if file:
        fout = open(file, 'a')
        fout.write(outstring)
        fout.write('\n')
        fout.close()

def connect_addr(addr, trecv, conn):
    outstr = 'Client ' + addr + ' connected.'
    print_log(outstr, log_file)
    trecvs[addr] = (trecv, conn)
    
def disconnect_addr(addr):
    outstr = 'Client ' + addr + ' disconnected.'
    print_log(outstr, log_file)
    del trecvs[addr]

def recv_client(conn, addr):
    while True:
        try:
            data = conn.recv(2621440)
            if not data:
                disconnect_addr(addr)
                return
            input_queue.put((addr, data))
        except:
            disconnect_addr(addr)
            return

def output_client():
    while(True):
        addr, outstr = output_queue.get()
        conn = trecvs[addr][1]
        conn.sendall(outstr)

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
    conn.close()
    
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
    
def read_opening(opening_file):
    fin = open(opening_file, 'r')
    openings_list = []
    while True:
        reads = fin.readline()
        if reads == None or len(reads) == 0:
            break
        line = parse_line_opening(reads)
        if line:
            openings_list.append(line)
    fin.close()
    return openings_list

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
    result_dir = curpath + slash + 'result' + slash + tournament_name
    if os.path.exists(result_dir):
        if not os.path.isdir(result_dir):
            os.remove(result_dir)
            os.makedirs(result_dir)
    else:
        os.makedirs(result_dir)
    log_file = result_dir + slash + 'log.txt'
    state_file = result_dir + slash + 'state.txt'
    result_file = result_dir + slash + 'result.txt'
    message_file = result_dir + slash + 'message.txt'
    openings = read_opening(opening_file)

    tournament_state = Tournament(curpath, engines, tur_name, board_size, rule, openings, is_tournament, time_turn, time_match, tolerance, memory, real_time_pos, real_time_message)

    host = '0.0.0.0'
    port = string.atoi(sys.argv[2])
    taccept = threading.Thread(target = accept_client, args = (host, port))
    taccept.start()
    toutput = threading.Thread(target = output_client)
    toutput.start()

    while(True):
        cur_input = input_queue.get()
        print cur_input
        inaddr = cur_input[0]
        instr = cur_input[1].strip()
        sinstr = re.split(r'\s+', instr)
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
            pos = sinstr[2]
            message = sinstr[3]
            cur_client.end(pos, message)
