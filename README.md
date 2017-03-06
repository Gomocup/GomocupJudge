# GomocupJudge

### Introduction
GomocupJudge is a new manager for Gomocup **under development**.

* Tested in Python 2.7

### Protocol

* The server and clients communicate through socket.  
* At any time, a client runs at most 1 match.

Sample

    server: engine exist md5 [ai's md5]
    client: no
    server: engine send [ai's filename, encoded in base64] [ai's file(exe/zip), encoded in base64]
    client: received
    server: engine exist md5 [ai's md5]
    client: yes
    server: match new [ai1's md5] [ai2's md5] [timeout_turn(ms)] [timeout_match(ms)] [rule] [tolerance(ms)] [opening, encoded in pos] [board_size] [max_memory] [game_type]
    client: ok
    client: match finished [game record, encoded in pos] [ais' messages, encoded in base64]
    server: received

    server: set real_time_pos 1
    client: ok
    server: set real_time_message 1
    client: ok

### TODO
* Support CPU affinity
* Check max_memory
* Check max folder size
* Check pondering
* Start a new thread for each match instance
* Check forbidden moves (foul) for Renju
* set real_time_pos
* set real_time_message

