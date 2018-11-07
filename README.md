README
======


What's this?
------------

Sample code of Router classes.

See [presentation slide](http://bit.ly/fastest_router) for details.


Requirements
------------

* Python (>= 3.5)

(Sample code will work on Python 3.x, but benchmark script fails
 on Python <= 3.4 due to limitation of 're' library.
 See https://stackoverflow.com/questions/478458/ for details.)


How to run
----------

```
$ python3 --version
Python 3.6.6
$ pip install -r requirements.txt
$ kk -l                         # list tasks
$ kk test                       # run test scripts
$ kk bench                      # run benchmark
$ kk bench -n 100000 -i 5 -x 2  # run benchmark with options
```

Or:

```
$ python3 --version
Python 3.6.6
$ pip install -r requirements.txt
$ python3 -m oktest tests       # run test scripts
$ python3 router_bench.py       # run benchmark
$ python3 router_bench.py -h    # show options of benchmark
$ python3 router_bench.py -n 100000 -c 5 -x 2
```


License
-------

CC0 (public domain)
