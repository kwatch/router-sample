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

* Ruby (>= 3.0)


How to run (Python3)
--------------------

Install:

```
$ python3 --version
Python 3.6.6
$ python3 -m venv pyvenv
$ . pyvenv/bin/activate
$ pip3 install -r requirements.txt
```

Run:

```
$ kk -l                         # list tasks
$ kk test                       # run test scripts
$ kk bench                      # run benchmark
$ kk bench -n 100000 -i 5 -x 2  # run benchmark with options
```

Or:

```
$ python3 -m oktest tests       # run test scripts
$ python3 router_bench.py       # run benchmark
$ python3 router_bench.py -h    # show options of benchmark
$ python3 router_bench.py -n 100000 -c 5 -x 2
```


How to run (Ruby3)
------------------

Install:

```
$ ruby --version
ruby 3.4.7
$ mkdir gems
$ export GEM_HOME=$PWD/gems
$ export PATH=$GEM_HOME/bin:$PATH
$ bundler install
```

Run:

```
$ rake                          # list tasks
$ rake test:rb                  # run test scripts
$ rake bench:rb                 # run benchmark
$ rake bench:guide              # show how to run benchmark
```

Or:

```
$ oktest -sc tests/ruby         # run test scripts
$ ruby router_bench.rb          # run benchamrk
$ ruby router_bench.rb -h       # show options of benchmark
$ N=1000_000 ruby router_bench.rb -c 5 -x 2
```


License
-------

MIT-LICENSE
