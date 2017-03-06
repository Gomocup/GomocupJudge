# this is not the real server
# it is used to debug the client only

import socket

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "localhost"
    port = 5678
    s.bind((host, port))
    s.listen(5)
    
    c, addr = s.accept()
    while True:
        x = raw_input()
        if x == 'exit':
            break
        elif x == 'sendengine':
            with open("./tmp/Tito2014.zip", "rb") as f:
                engine = f.read().encode('base64')
            s = "engine send " + "Tito2014.zip".encode('base64') + " " + engine
            c.send(s)
            print "Tito2014.zip".encode('base64')
        else:
            c.send(x)
        buf = c.recv(64)
        if len(buf) > 0:
            print addr, buf

if __name__ == '__main__':
    main()


