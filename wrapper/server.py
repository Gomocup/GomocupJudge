import socket
import argparse
import sys
from threading import Thread
from queue import Queue, Empty
import time

class server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        def enqueue_output(q):
            while True:
                q.put(sys.stdin.readline())
            out.close()
        self.queue = Queue()
        queuethread = Thread(target=enqueue_output, args=(self.queue,))
        queuethread.daemon = True
        queuethread.start()

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
        self.conn.settimeout(0.01)
        try:
            buf = self.conn.recv(size).decode()
            self.buf_socket = self.buf_socket + buf
        except:
            pass
        self.conn.settimeout(None)
        return None        

    def _recv_stdin(self):
        try: buf = self.queue.get_nowait()
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
            ret = self._recv_stdin()
            if ret is not None:
                return ["stdin", ret]
            time.sleep(0.01)

    def listen(self):
        self.server_socket.listen()
        self.conn, self.addr = self.server_socket.accept()
        self.conn.send("new\n".encode())
        while True:
            buf = self.recv()
            if buf[0] == "socket":
                sys.stdout.write(buf[1]+"\n")
                sys.stdout.flush()
            elif buf[0] == "stdin":
                self.conn.send(("msg "+buf[1]).encode())
            
            
def main():
    parser = argparse.ArgumentParser(description='Gomocup Experimental Tournament Client')

    parser.add_argument("--host", dest="host", action="store", required=True)
    parser.add_argument("--port", dest="port", action="store", required=True)

    args = parser.parse_args()
    
    server(host=args.host, port=int(args.port)).listen()
            
if __name__ == '__main__':
    main()

        
