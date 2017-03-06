import socket
import hashlib
import os
import zipfile
import shutil
import platform

from ai_match import ai_match

class client(object):
    def __init__(self, host, port, working_dir):
        self.host = host
        self.port = port
        self.working_dir = working_dir
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.engine_dir = os.path.join(self.working_dir, "engine")
        self.match_dir = os.path.join(self.working_dir, "match")
        self.folder_dir = os.path.join(self.match_dir, "folder")
        self.engine = []
        for fname in os.listdir(self.engine_dir):
            if fname.lower().endswith(".zip") or fname.lower().endswith(".exe"):
                self.engine += [(fname, self.md5(os.path.join(self.engine_dir, fname)))]
        self.is_os_64bit = platform.machine().endswith('64')
        self.display_info()

    def display_info(self):
        print 'System is '+ ('64' if self.is_os_64bit else '32') + 'bit'
        for engine in self.engine:
            print engine[0], engine[1]

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
                with open(os.path.join(self.engine_dir, fname), "wb") as f:
                    f.write(engine)
                self.engine += [(fname, self.md5(os.path.join(self.engine_dir, fname)))]
                self.client_socket.send("received")
            elif buf.lower().startswith("match new"):
                buf = buf.strip().split(' ')[2:]
                md5_1 = buf[0]
                md5_2 = buf[1]
                timeout_turn = int(buf[2])
                timeout_match = int(buf[3])
                rule = int(buf[4])
                tolerance = int(buf[5])
                opening = buf[6]
                board_size = int(buf[7])
                max_memory = int(buf[8])
                game_type = int(buf[9])
                self.client_socket.send("ok")

                for engine in self.engine:
                    if engine[1] == md5_1 or engine[1] == md5_2:
                        try:
                            os.mkdir(os.path.join(self.match_dir, engine[1]))
                            if engine[0].lower().endswith(".zip"):
                                zip_ref = zipfile.ZipFile(os.path.join(self.engine_dir, engine[0]), 'r')
                                zip_ref.extractall(os.path.join(self.match_dir, engine[1]))
                                zip_ref.close()
                            else:
                                shutil.copy(os.path.join(self.engine_dir, engine[0]), os.path.join(self.match_dir, engine[1]))
                            os.mkdir(os.path.join(self.folder_dir, engine[1]))
                        except:
                            pass

                def get_cmd_protocol(md5):
                    exe_list = []
                    has_pbrain = False
                    for fname in os.listdir(os.path.join(self.match_dir, md5)):
                        if fname.lower().endswith(".exe"):
                            if fname.lower().startswith("pbrain"):
                                if has_pbrain:
                                    exe_list += [fname]
                                else:
                                    exe_list = [fname]
                                    has_pbrain = True
                            else:
                                if not has_pbrain:
                                    exe_list += [fname]
                            
                    if len(exe_list) > 1:
                        for fname in exe_list:
                            if (self.is_os_64bit and '64' in fname) or (not self.is_os_64bit and '64' not in fname):
                                cmd = os.path.join(self.match_dir, md5, fname)
                                protocol = 'new' if fname.lower().endswith('pbrain') else 'old'
                                return cmd, protocol
                    fname = exe_list[0]
                    cmd = os.path.join(self.match_dir, md5, fname).replace("\\", "/")
                    protocol = 'new' if fname.lower().startswith('pbrain') else 'old'
                    return cmd, protocol
                        
                        
                cmd_1, protocol_1 = get_cmd_protocol(md5_1)
                cmd_2, protocol_2 = get_cmd_protocol(md5_2)
                #print cmd_1, protocol_1
                #print cmd_2, protocol_2

                game = ai_match(board_size = board_size,
                                opening = self.str_to_pos(opening),
                                cmd_1 = cmd_1,
                                cmd_2 = cmd_2,
                                protocol_1 = protocol_1,
                                protocol_2 = protocol_2,
                                timeout_turn_1 = timeout_turn,
                                timeout_turn_2 = timeout_turn,
                                timeout_match_1 = timeout_match,
                                timeout_match_2 = timeout_match,
                                max_memory_1 = max_memory,
                                max_memory_2 = max_memory,
                                game_type = game_type,
                                rule = rule,
                                folder_1 = os.path.join(self.folder_dir, md5_1),
                                folder_2 = os.path.join(self.folder_dir, md5_2),
                                working_dir_1 = os.path.join(self.match_dir, md5_1),
                                working_dir_2 = os.path.join(self.match_dir, md5_2),
                                tolerance = tolerance)
                msg, pos, ret = game.play()
                #print msg, pos, ret
                self.client_socket.send("match finished " + self.pos_to_str(pos) + " " + msg.encode("base64"))
                
            elif buf.lower().startswith("quit"):
                self.client_socket.send("bye")
                break
            else:
                self.client_socket.send("unknown command")
                continue

def main():
    client(host="localhost", port=6780, working_dir = "C:/Kai/git/GomocupJudge").listen()


if __name__ == '__main__':
    main()
