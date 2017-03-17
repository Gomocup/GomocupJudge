import socket
import sys
import string

host = sys.argv[1]
port = string.atoi(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
while True:
    data = s.recv(2621400)
    print data
    cmd = raw_input("Please input cmd:")
    s.sendall(cmd)
s.close()