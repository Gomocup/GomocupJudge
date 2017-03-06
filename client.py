#TODO
#* support hybrid AI

import socket
import hashlib
import os
import zipfile

from ai_match import ai_match

class client(object):
    def __init__(self, host, port, working_dir):
        self.host = host
        self.port = port
        self.working_dir = working_dir
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.engine = []
        for fname in os.listdir(self.working_dir):
            if fname.lower().endswith(".zip") or fname.lower().endswith(".exe"):
                self.engine += [(fname, self.md5(os.path.join(working_dir, fname)))]
        print self.engine
        

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def pos_to_str(self, pos):
        s = ''
        for i in xrange(len(pos)):
            x, y = pos[i]
            s += chr(ord('a')+x) + str(y+1)
        return s

    def str_to_pos(self, s):
        pos = []
        i = 0
        s = s.lower()
        while i < len(s):
            x = ord(s[i]) - ord('a')
            y = ord(s[i+1]) - ord('0')
            if i+2 < len(s) and s[i+2].isdigit():
                y = y * 10 + ord(s[i+2]) - ord('0') - 1
                i += 3
            else:
                y = y - 1
                i += 2
            pos += [(x,y)]
        return pos            
    
    def listen(self):
        while True:
            buf = self.client_socket.recv(16*1024*1024)
            if buf.lower().startswith("engine exist md5"):
                md5 = buf.strip().split()[-1]
                exist = False
                for engine in self.engine:
                    if engine[1] == md5:
                        exist = True
                        break
                self.client_socket.send("yes" if engine[1] == md5 else "no")
            elif buf.lower().startswith("engine send"):
                base64fname, base64engine = buf.strip().split(' ')[-2:]
                fname = base64fname.decode('base64')
                engine = base64engine.decode('base64')
                with open(os.path.join(self.working_dir, fname), "wb") as f:
                    f.write(engine)
                self.engine += [(fname, self.md5(os.path.join(self.working_dir, fname)))]
                self.client_socket.send("received")
            elif buf.lower().startswith("match new"):
                buf = buf.strip().split()[2:]
                md5_1 = buf[0]
                md5_2 = buf[1]
                timeout_turn = int(buf[2])
                timeout_match = int(buf[3])
                rule = int(buf[4])
                tolerence = int(buf[5])
                opening = buf[6]
                board_size = buf[7]
                max_memory = int(buf[8])
                self.client_socket.send("ok")

                '''
                #TODO
                game = ai_match(board_size = board_size,
                                opening = str_to_pos(opening),
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
                '''
                
            elif buf.lower().startswith("quit"):
                self.client_socket.send("bye")
                break
            else:
                self.client_socket.send("unknown command")
                continue

def main():
    client(host="localhost", port=5678, working_dir = "C:/Kai/git/GomocupJudge/engine").listen()


if __name__ == '__main__':
    main()
