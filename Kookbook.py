# -*- coding: utf-8 -*-

##
## Usage:
##
##   $ kk -l                         # list tasks
##   $ kk test                       # run test scripts
##   $ kk bench                      # run benchmark
##   $ kk bench -n 100000 -i 1 -x 0  # run benchmark with options
##
## Requirements: Python3, pip3 install -r requirements.txt
##


@recipe
def test(c):
    """run test scripts"""
    system("python3 -m oktest tests")


@recipe
@spices("-n N : number of loop",
        "-i N : number of iteration",
        "-x N : ignores max/min N results")
def bench(c, n=1000*1000, i=1, x=0):
    """run benchmark"""
    system(c%"python3 router_bench.py -n $(n) -c $(i) -x $(x)")
