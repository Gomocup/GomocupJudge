Gomocup 2021 Experimental Tournament Client
===========================================

(**Please be aware that the client may be updated for better stability and performance before Gomocup 2021, so please check out the latest version when applicable)**

This year the tournament client will connect every AI to  [Renju Caffe](https://games.renjucaffe.com/). The usage is as follows:

 * Make sure you have [Python 3](https://www.python.org/downloads/) in your environment.
 * Download [client.py](https://raw.githubusercontent.com/Gomocup/GomocupJudge/master/wrapper21/client.py).
 * Execute ```python3 client.py --host HOST --name NAME --key KEY --ai PATH```
 where Gomocup will send HOST, NAME, and KEY to every participant before the start of the tournament, and PATH is the path to your AI.

