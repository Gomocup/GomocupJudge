import socket
import argparse
import subprocess, shlex
import sys
import time
from queue import Queue, Empty
from threading import Thread

class client(object):
    def __init__(self, host, port, ai):
        self.host = host
        self.port = port
        self.ai = ai
        self.process = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def _recv_socket(self, size):
        try:
            self.buf_socket
        except:
            self.buf_socket = ""

        for i in range(len(self.buf_socket)):
            if self.buf_socket[i] == "\n":
                ret = self.buf_socket[:i]
                self.buf_socket = self.buf_socket[i+1:]
                return ret
        self.client_socket.settimeout(0.01)
        try:
            buf = self.client_socket.recv(size).decode()
            self.buf_socket = self.buf_socket + buf
        except:
            pass
        self.client_socket.settimeout(None)        
        return None

    def _recv_ai(self):            
        if self.process is not None:
            try: buf = self.queue.get_nowait().decode()
            except Empty:
                pass
            else:
                return buf            
        return None
    
    def recv(self):
        while True:
            ret = self._recv_socket(16*1024*1024)
            if ret is not None:
                return ["socket", ret]
            ret = self._recv_ai()
            if ret is not None:
                return ["ai", ret]
            time.sleep(0.01)

    def write(self, msg):
        self.process.stdin.write(msg.encode())
        self.process.stdin.flush()
    
    def listen(self):
        while True:
            buf = self.recv()
            if buf[0] == "socket":
                if buf[1].startswith("new"):
                    self.process = subprocess.Popen(shlex.split(self.ai),
                                                    shell=False,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    bufsize=1,
                                                    close_fds='posix' in sys.builtin_module_names,
                                                    cwd=".")
                    def enqueue_output(out, q):
                        for line in iter(out.readline, b''):
                            q.put(line)
                        out.close()
                    self.queue = Queue()
                    queuethread = Thread(target=enqueue_output, args=(self.process.stdout, self.queue))
                    queuethread.daemon = True
                    queuethread.start()
                elif buf[1].startswith("msg"):
                    self.write(buf[1][4:]+"\n")
            elif buf[0] == "ai":
                self.client_socket.send(buf[1].encode())

def main():
    parser = argparse.ArgumentParser(description='Gomocup Experimental Tournament Client')

    parser.add_argument("--host", dest="host", action="store", required=True)
    parser.add_argument("--port", dest="port", action="store", required=True)
    parser.add_argument("--ai", dest="ai", action="store", required=True)
    
    args = parser.parse_args()

    client(host=args.host, port=int(args.port), ai=args.ai).listen()


if __name__ == '__main__':
    main()
