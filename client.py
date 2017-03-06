import socket
import hashlib
import os

from match import match

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
                print base64fname, fname
                with open(os.path.join(self.working_dir, fname), "wb") as f:
                    f.write(engine)
                self.engine += [(fname, self.md5(os.path.join(self.working_dir, fname)))]
                self.client_socket.send("received")
            elif buf.lower().startswith("match new"):
                buf = buf.strip().split()
                #TODO
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
