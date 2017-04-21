import socket
import hashlib
import os
import zipfile
import shutil
import platform
import argparse
import sys

from ai_match import ai_match
from utility import *

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
        if not os.path.isdir(self.engine_dir):
            os.mkdir(self.engine_dir)
        if not os.path.isdir(self.match_dir):
            os.mkdir(self.match_dir)
        if not os.path.isdir(self.folder_dir):
            os.mkdir(self.folder_dir)
            
        self.engine = []
        for fname in os.listdir(self.engine_dir):
            if fname.lower().endswith(".zip") or fname.lower().endswith(".exe"):
                self.engine += [(fname, self.md5(os.path.join(self.engine_dir, fname)))]
        self.is_os_64bit = platform.machine().endswith('64')
        
        self.settings = {}
        self.settings["real_time_pos"] = 0
        self.settings["real_time_message"] = 0
        #self.settings["allow pondering"] = 0
        #self.settings[""] = 0
        self.settings["socket"] = self.client_socket
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
    
    def listen(self):
        while True:
            buf = self.client_socket.recv(16*1024*1024)
            #print '\"' + buf + '\"'
            #sys.stdout.flush()
            if buf.lower().startswith("engine exist"):
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
                if len(buf) >= 10:
                    game_type = int(buf[9])
                else:
                    game_type = 3
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
                                cmd = os.path.join(self.match_dir, md5, fname).replace("\\", "/")
                                protocol = 'new' if fname.lower().startswith('pbrain') else 'old'
                                return cmd, protocol
                    fname = exe_list[0]
                    cmd = os.path.join(self.match_dir, md5, fname).replace("\\", "/")
                    protocol = 'new' if fname.lower().startswith('pbrain') else 'old'
                    return cmd, protocol
                    
                cmd_1, protocol_1 = get_cmd_protocol(md5_1)
                cmd_2, protocol_2 = get_cmd_protocol(md5_2)

                print cmd_1, protocol_1
                print cmd_2, protocol_2
                
                game = ai_match(board_size = board_size,
                                opening = str_to_pos(opening),
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
                                tolerance = tolerance,
                                settings = self.settings)
                msg, psq, result, endby = game.play()

                #print msg, psq
                print result, endby
                
                self.client_socket.send("match finished " + psq_to_psq(psq, board_size).encode("base64").replace("\n", "").replace("\r", "") + \
                                        " " + msg.encode("base64").replace("\n", "").replace("\r", "") + " " + str(result) + " " + str(endby))
                self.client_socket.recv(16) #received
                
            elif buf.lower().startswith("set real_time_pos"):
                self.settings["real_time_pos"] = int(buf.strip().split()[-1])
                self.client_socket.send("ok")
            elif buf.lower().startswith("set real_time_message"):
                self.settings["real_time_message"] = int(buf.strip().split()[-1])
                self.client_socket.send("ok")
            elif buf.lower().startswith("pause"):
                #TODO
                self.client_socket.send("ok")
            elif buf.lower().startswith("continue"):
                #TODO
                self.client_socket.send("ok")
            elif buf.lower().startswith("terminate"):
                #TODO
                self.client_socket.send("ok")
            else:
                self.client_socket.send("unknown command")
                continue

def main():
    parser = argparse.ArgumentParser(description='GomocupJudge Client')

    parser.add_argument("--host", dest="host", action="store", required=True)
    parser.add_argument("--port", dest="port", action="store", required=True)
    parser.add_argument("--dir", dest="working_dir", action="store", required=True)
    
    args = parser.parse_args()

    client(host=args.host, port=int(args.port), working_dir = args.working_dir).listen()


if __name__ == '__main__':
    main()
