# this is not the real server
# it is used to debug the client only

import socket

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "localhost"
    port = 6780
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
        elif x == 'newmatch':
            c.send("match new c3f044fafd550e01c97cf599f0cd7c31 e7d8817a65c86b9c4b6b675dd021269e "+
                   "1000 100000 0 1000 j10 20 350000000 1")
            c.recv(64)
            pass
        else:
            c.send(x)
        buf = c.recv(64)
        if len(buf) > 0:
            print addr, buf

if __name__ == '__main__':
    main()


