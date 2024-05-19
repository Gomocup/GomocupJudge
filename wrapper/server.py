import socket
import argparse
import sys
from threading import Thread
from queue import Queue, Empty
import time
import json

global_timeout = 0.1
global_retry = 10


class server(object):
    def __init__(self, host, port, key):
        self.host = host
        self.port = port
        self.key = key
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.conn = None
        self.addr = None

        def enqueue_output(q):
            while True:
                q.put(sys.stdin.readline())
            out.close()

        self.queue = Queue()
        self.msgqueue = []
        self.msgstamp = int(str(time.time()).replace(".", ""))
        self.msgok = set()
        self.timestamp = {}
        self.timestamp["send"] = time.time() - global_timeout
        self.timestamp["ping"] = time.time() - global_timeout
        self.timestamp["connected"] = time.time() - global_timeout
        queuethread = Thread(target=enqueue_output, args=(self.queue,))
        queuethread.daemon = True
        queuethread.start()

    def _recv_socket(self, size):
        for i in range(len(self.buf_socket)):
            if self.buf_socket[i] == "\n":
                ret = self.buf_socket[:i]
                self.buf_socket = self.buf_socket[i + 1 :]
                return ret
        self.conn.settimeout(global_timeout)
        try:
            buf = self.conn.recv(size).decode()
            self.buf_socket = self.buf_socket + buf
        except:
            pass
        self.conn.settimeout(None)
        return None

    def _recv_stdin(self):
        try:
            buf = self.queue.get_nowait()
        except Empty:
            pass
        else:
            return buf
        return None

    def reconnect(self):
        try:
            if time.time() >= self.timestamp["ping"] + global_timeout:
                self.conn.settimeout(global_timeout)
                self.conn.send(("ping\n").encode())
                self.conn.settimeout(None)
                self.timestamp["ping"] = time.time()
            assert (
                time.time()
                < self.timestamp["connected"] + global_timeout * global_retry
            )
        except:
            while True:
                try:
                    self.server_socket.listen()
                    self.conn, self.addr = self.server_socket.accept()
                    # print(self.addr, flush=True)
                    self.timestamp["connected"] = time.time()
                    self.buf_socket = ""
                    c = 0
                    while c < global_retry:
                        buf = self._recv_socket(16 * 1024 * 1024)
                        if buf is not None:
                            break
                        time.sleep(global_timeout)
                        c += 1
                    if (
                        buf is not None
                        and buf.startswith("ping")
                        and buf[5:].strip() == self.key
                    ):
                        break
                except:
                    pass

    def recv(self):
        while True:
            self.reconnect()
            try:
                ret = self._recv_socket(16 * 1024 * 1024)
                if ret is not None:
                    return ["socket", ret]
                ret = self._recv_stdin()
                if ret is not None:
                    return ["stdin", ret]
            except:
                pass
            time.sleep(global_timeout)

    def send(self):
        while len(self.msgqueue) > 0:
            self.reconnect()
            try:
                if time.time() >= self.timestamp["send"] + global_timeout:
                    self.conn.settimeout(global_timeout)
                    self.conn.send((self.msgqueue[0][1]).encode())
                    self.conn.settimeout(None)
                    self.timestamp["send"] = time.time()
                break
            except:
                time.sleep(global_timeout)

    def listen(self):
        self.msgqueue += [(self.msgstamp, "new " + str(self.msgstamp) + "\n")]
        self.msgstamp += 1
        while True:
            buf = self.recv()
            if buf[0] == "socket":
                # print(buf, flush=True)
                if len(buf[1]) > 0:
                    self.timestamp["connected"] = time.time()
                if buf[1].startswith("ping"):
                    pass
                elif buf[1].startswith("msg"):
                    # print(buf, flush=True)
                    msgid = int(buf[1].split(" ")[1])
                    msg = " ".join(buf[1].split(" ")[2:])
                    if msgid not in self.msgok:
                        self.msgok.add(msgid)
                        sys.stdout.write(msg + "\n")
                        sys.stdout.flush()
                    try:
                        self.conn.settimeout(global_timeout)
                        self.conn.send(("ok " + str(msgid) + "\n").encode())
                        self.conn.settimeout(None)
                    except:
                        pass
                elif buf[1].startswith("ok"):
                    msgid = int(buf[1].strip().split(" ")[1])
                    if len(self.msgqueue) > 0 and self.msgqueue[0][0] == msgid:
                        del self.msgqueue[0]
                        self.timestamp["send"] = time.time() - global_timeout
            elif buf[0] == "stdin":
                self.msgqueue += [
                    (self.msgstamp, ("msg " + str(self.msgstamp) + " " + buf[1]))
                ]
                self.msgstamp += 1
            self.send()


def main():
    fn = sys.argv[0]
    while len(fn) > 0 and fn[-1] not in "\\/":
        fn = fn[:-1]
    fn += "config.json"
    try:
        with open(fn, "r", encoding="utf8") as f:
            config = json.load(f)
    except:
        config = {}
        parser = argparse.ArgumentParser(
            description="Gomocup Experimental Tournament Server"
        )
        parser.add_argument("--host", dest="host", action="store", required=True)
        parser.add_argument("--port", dest="port", action="store", required=True)
        parser.add_argument("--key", dest="key", action="store", required=True)
        args = parser.parse_args()
        config["host"] = args.host
        config["port"] = args.port
        config["key"] = args.key
        with open(fn, "w", encoding="utf8") as f:
            json.dump(config, f, indent=2)

    server(host=config["host"], port=int(config["port"]), key=config["key"]).listen()


if __name__ == "__main__":
    main()
