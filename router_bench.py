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
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter,
    OptimizedRegexpRouter, HashedRegexpRouter,
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


if False:

    import string
    arr = []
    for c in string.ascii_lowercase:
        path = "/%s" % (c * 3)
        arr.append((path, DummyAPI))
        #arr.append((path + "/{id}/comments", DummyAPI))
    mapping = [("/api", arr)]

else:

    mapping = [
        (r'/api', [
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


router_classes = (
    NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter,
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter,
    OptimizedRegexpRouter, HashedRegexpRouter,
    StateMachineRouter,
)

urlpaths = (
    '/api/aaa/',
    '/api/aaa/123.json',
    '/api/zzz/',
    '/api/zzz/789.json',
)

def validate(urlpath, result):
    if urlpath.endswith('/123.json'):
        assert result == (DummyAPI, DummyAPI.do_show, [123])
    elif urlpath.endswith('/789.json'):
        assert result == (DummyAPI, DummyAPI.do_show, [789])
    else:
        assert result == (DummyAPI, DummyAPI.do_index, [])


loop = 1000 * 1000
with Benchmarker(loop, width=38, cycle=1, extra=0) as bench:

    debug = bench.properties.get('debug', False)

    for router_class in router_classes:
        for urlpath in urlpaths:
            label = router_class.__name__.replace('Router', '')

            @bench("%-15s: %-16s" % (label, urlpath))
            def _(bm, router=router_class(mapping), urlpath=urlpath):
                for _ in bm:
                    result = router.lookup('GET', urlpath)
                #
                if debug:
                    validate(urlpath, result)
