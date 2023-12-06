# -*- coding: utf-8 -*-

##
## See:
##      https://pythonhosted.org/Benchmarker/
## for details of 'benchmarker.py'.
##

import sys
from benchmarker import Benchmarker

from minikeight import (
    on, RequestHandler,
    NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter,
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter, OptimizedRegexpRouter,
    StateMachineRouter,
)


class DummyAPI(RequestHandler):

    with on.path('/'):

        @on('GET')
        def do_index(self):
            return {"action": "index"}

        @on('POST')
        def do_create(self):
            return {"action": "create"}

    with on.path('/new'):

        @on('GET')
        def do_new(self, id):
            return {"action": "new", "id": id}

    with on.path('/{id:int}.*'):

        @on('GET')
        def do_show(self, id):
            return {"action": "show", "id": id}

        @on('PUT')
        def do_update(self, id):
            return {"action": "update", "id": id}

        @on('DELETE')
        def do_delete(self, id):
            return {"action": "delete", "id": id}

    with on.path('/{id:int}/edit'):

        @on('GET')
        def do_edit(self, id):
            return {"action": "edit", "id": id}


##
## import string
## arr = []
## for c in string.ascii_lowercase:
##     path = "/%s" % (c * 3)
##     arr.append((path, DummyAPI))
## mapping = [("/api", arr)]
##

mapping = [
    (r'/api/v1', [
        (r'/aaa'    , DummyAPI),
        (r'/bbb'    , DummyAPI),
        (r'/ccc'    , DummyAPI),
        (r'/ddd'    , DummyAPI),
        (r'/eee'    , DummyAPI),
        (r'/fff'    , DummyAPI),
        (r'/ggg'    , DummyAPI),
        (r'/hhh'    , DummyAPI),
        (r'/iii'    , DummyAPI),
        (r'/jjj'    , DummyAPI),
        (r'/kkk'    , DummyAPI),
        (r'/lll'    , DummyAPI),
        (r'/mmm'    , DummyAPI),
        (r'/nnn'    , DummyAPI),
        (r'/ooo'    , DummyAPI),
        (r'/ppp'    , DummyAPI),
        (r'/qqq'    , DummyAPI),
        (r'/rrr'    , DummyAPI),
        (r'/sss'    , DummyAPI),
        (r'/ttt'    , DummyAPI),
        (r'/uuu'    , DummyAPI),
        (r'/vvv'    , DummyAPI),
        (r'/www'    , DummyAPI),
        (r'/xxx'    , DummyAPI),
        (r'/yyy'    , DummyAPI),
        (r'/zzz'    , DummyAPI),
    ]),
]


try:
    xrange
except NameError:
    xrange = range       # for Python3

#loop = 1000 * 1000
loop = 1000 * 100
with Benchmarker(loop, width=43) as bench:

    router_classes = (
        NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter,
        NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter, OptimizedRegexpRouter,
        StateMachineRouter,
    )
    urlpaths = (
        '/api/v1/aaa/',
        '/api/v1/aaa/123.json',
        '/api/v1/zzz/',
        '/api/v1/zzz/789.json',
    )
    debug = bench.properties.get('debug', False)

    for router_class in router_classes:
        for urlpath in urlpaths:

            @bench("%-21s: %-20s" % (router_class.__name__, urlpath))
            def _(bm, router=router_class(mapping), urlpath=urlpath):
                for _ in bm:
                    result = router.lookup('GET', urlpath)
                #
                if debug:
                    if urlpath.endswith('/123.json'):
                        assert result == (DummyAPI, DummyAPI.do_show, [123])
                    elif urlpath.endswith('/789.json'):
                        assert result == (DummyAPI, DummyAPI.do_show, [789])
                    else:
                        assert result == (DummyAPI, DummyAPI.do_index, [])
