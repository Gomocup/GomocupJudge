import socket
import argparse
import subprocess, shlex
import sys
import time
from queue import Queue, Empty
from threading import Thread

global_timeout = 0.1
global_retry = 10


class client(object):
    def __init__(self, host, port, key, ai):
        self.host = host
        self.port = port
        self.key = key
        self.ai = ai
        self.process = None
        self.client_socket = None
        self.msgqueue = []
        self.msgstamp = int(str(time.time()).replace(".", ""))
        self.msgok = set()
        self.timestamp = {}
        self.timestamp["send"] = time.time() - global_timeout
        self.timestamp["ping"] = time.time() - global_timeout
        self.timestamp["connected"] = time.time() - global_timeout

    def _recv_socket(self, size):
        try:
            self.buf_socket
        except:
            self.buf_socket = ""

        for i in range(len(self.buf_socket)):
            if self.buf_socket[i] == "\n":
                ret = self.buf_socket[:i]
                self.buf_socket = self.buf_socket[i + 1 :]
                return ret
        self.client_socket.settimeout(global_timeout)
        try:
            buf = self.client_socket.recv(size).decode()
            self.buf_socket = self.buf_socket + buf
        except:
            pass
        self.client_socket.settimeout(None)
        return None

    def _recv_ai(self):
        if self.process is not None:
            try:
                buf = self.queue.get_nowait().decode()
            except Empty:
                pass
            else:
                return buf
        return None

    def reconnect(self):
        try:
            if time.time() >= self.timestamp["ping"] + global_timeout:
                self.client_socket.settimeout(global_timeout)
                self.client_socket.send(("ping " + self.key + "\n").encode())
                self.client_socket.settimeout(None)
                self.timestamp["ping"] = time.time()
            assert (
                time.time()
                < self.timestamp["connected"] + global_timeout * global_retry
            )
        except:
            while True:
                # print("reconnecting...", flush=True)
                try:
                    self.client_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM
                    )
                    self.client_socket.connect((self.host, self.port))
                    self.timestamp["connected"] = time.time()
                    self.client_socket.settimeout(global_timeout)
                    self.client_socket.send(("ping " + self.key + "\n").encode())
                    self.client_socket.settimeout(None)
                    break
                except:
                    time.sleep(global_timeout)

    def recv(self):
        while True:
            self.reconnect()
            try:
                ret = self._recv_socket(16 * 1024 * 1024)
                if ret is not None:
                    return ["socket", ret]
                ret = self._recv_ai()
                if ret is not None:
                    return ["ai", ret]
            except:
                pass
            time.sleep(global_timeout)

    def send(self):
        while len(self.msgqueue) > 0:
            self.reconnect()
            try:
                print(str(time.time()) + "\t" + self.msgqueue[0][1].strip(), flush=True)
                if time.time() >= self.timestamp["send"] + global_timeout:
                    self.client_socket.settimeout(global_timeout)
                    self.client_socket.send(
                        (
                            "msg "
                            + str(self.msgqueue[0][0])
                            + " "
                            + self.msgqueue[0][1]
                        ).encode()
                    )
                    self.client_socket.settimeout(None)
                    self.timestamp["send"] = time.time()
                break
            except:
                time.sleep(global_timeout)

    def write(self, msg):
        self.process.stdin.write(msg.encode())
        self.process.stdin.flush()

    def listen(self):
        while True:
            buf = self.recv()
            # print(buf, flush=True)
            if buf[0] == "socket":
                if len(buf[1]) > 0:
                    self.timestamp["connected"] = time.time()
                if buf[1].startswith("ping"):
                    pass
                elif buf[1].startswith("new"):
                    msgid = int(buf[1].split(" ")[1])
                    if msgid not in self.msgok:
                        self.msgok.add(msgid)
                        if self.process is not None:
                            self.process.kill()
                        self.process = subprocess.Popen(
                            shlex.split(self.ai),
                            shell=False,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            bufsize=1,
                            close_fds="posix" in sys.builtin_module_names,
                            cwd=".",
                        )

                        def enqueue_output(out, q):
                            for line in iter(out.readline, b""):
                                q.put(line)
                            out.close()

                        self.queue = Queue()
                        queuethread = Thread(
                            target=enqueue_output,
                            args=(self.process.stdout, self.queue),
                        )
                        queuethread.daemon = True
                        queuethread.start()
                    try:
                        self.client_socket.settimeout(global_timeout)
                        self.client_socket.send(("ok " + str(msgid) + "\n").encode())
                        self.client_socket.settimeout(None)
                    except:
                        pass
                elif buf[1].startswith("msg"):
                    msgid = int(buf[1].split(" ")[1])
                    msg = " ".join(buf[1].split(" ")[2:])
                    if msgid not in self.msgok:
                        self.msgok.add(msgid)
                        self.write(msg + "\n")
                        sys.stdout.flush()
                    try:
                        self.client_socket.settimeout(global_timeout)
                        self.client_socket.send(("ok " + str(msgid) + "\n").encode())
                        self.client_socket.settimeout(None)
                    except:
                        pass
                elif buf[1].startswith("ok"):
                    msgid = int(buf[1].strip().split(" ")[1])
                    if len(self.msgqueue) > 0 and self.msgqueue[0][0] == msgid:
                        del self.msgqueue[0]
                        self.timestamp["send"] = time.time() - global_timeout

            elif buf[0] == "ai":
                self.msgqueue += [(self.msgstamp, buf[1])]
                self.msgstamp += 1
            self.send()


def main():
    parser = argparse.ArgumentParser(
        description="Gomocup Experimental Tournament Client"
    )

    parser.add_argument("--host", dest="host", action="store", required=True)
    parser.add_argument("--port", dest="port", action="store", required=True)
    parser.add_argument("--key", dest="key", action="store", required=True)
    parser.add_argument("--ai", dest="ai", action="store", required=True)

    args = parser.parse_args()

    client(host=args.host, port=int(args.port), key=args.key, ai=args.ai).listen()


if __name__ == "__main__":
    main()
