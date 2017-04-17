import socket
import sys
import os
import string
import threading

def recv_server(cur_socket):
    while True:
        try:
            data = cur_socket.recv(5242800)
        except:
            os._exit(0)
        print data

host = sys.argv[1]
port = string.atoi(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
trecv = threading.Thread(target = recv_server, args = (s,))
trecv.start()
while True:
    cmd = raw_input()
    s.sendall(cmd)
s.close()