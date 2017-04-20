# GomocupJudge

### Introduction
GomocupJudge is a new manager for Gomocup **under development**.

* Tested in Python 2.7

### Protocol

* The server and clients communicate through socket.  
* At any time, a client runs at most 1 match.
* Pondering is not allowed (AI's process is suspended when it is not thinking)

Sample

    server: engine exist md5 [ai's md5]
    client: no
    server: engine send [ai's filename, encoded in base64] [ai's file(exe/zip), encoded in base64]
    client: received
    server: engine exist md5 [ai's md5]
    client: yes

    server: match new [ai1's md5] [ai2's md5] [timeout_turn(ms)] [timeout_match(ms)] [rule] [tolerance(ms)] [opening, encoded in pos] [board_size] [max_memory(bytes)]
    client: ok
    client: match finished [game record, encoded in base64] [ais' messages, encoded in base64] [result: 0 draw, 1 black win, 2 white win] [end by: 0 draw/five, 1 foul, 2 timeout, 3 illegal coordinate, 4 crash]
    server: received

    server: set real_time_pos 1
    client: ok
    server: set real_time_message 1
    client: ok

    client: pos [the latest move, encoded in base64]
    server: received
    client: message [the latest message, encoded in base64]
    server: received

### TODO

    server: pause
    client: ok
    server: continue
    client: ok
    server: terminate
    client: ok
    server: set check_pondering 1
    client: ok

* Check max_memory
* Check max folder size
* Start a new thread for each match instance

