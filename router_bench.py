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
    OptimizedRegexpRouter, HashedRegexpRouter, SlicedRegexpRouter,
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

    #with on.path('/{id:int}.*'):
    with on.path('/{id:int}.json'):

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
    #arr = []
    #for c in string.ascii_lowercase:
    #    path = "/%s" % (c * 3)
    #    arr.append((path, DummyAPI))
    #    #arr.append((path+"/{x_id}/comments", DummyAPI))
    #mapping = [("/api", arr)]
    dct = {}
    for c in string.ascii_lowercase:
        path = "/%s" % (c * 3)
        dct[path] = DummyAPI
        #dct[path+"/{x_id}/comments"] = DummyAPI
    mapping = {"/api": dct}

else:

    mapping = {
        "/api": {
            "/aaa":  DummyAPI,
            "/bbb":  DummyAPI,
            "/ccc":  DummyAPI,
            "/ddd":  DummyAPI,
            "/eee":  DummyAPI,
            "/fff":  DummyAPI,
            "/ggg":  DummyAPI,
            "/hhh":  DummyAPI,
            "/iii":  DummyAPI,
            "/jjj":  DummyAPI,
            "/kkk":  DummyAPI,
            "/lll":  DummyAPI,
            "/mmm":  DummyAPI,
            "/nnn":  DummyAPI,
            "/ooo":  DummyAPI,
            "/ppp":  DummyAPI,
            "/qqq":  DummyAPI,
            "/rrr":  DummyAPI,
            "/sss":  DummyAPI,
            "/ttt":  DummyAPI,
            "/uuu":  DummyAPI,
            "/vvv":  DummyAPI,
            "/www":  DummyAPI,
            "/xxx":  DummyAPI,
            "/yyy":  DummyAPI,
            "/zzz":  DummyAPI,
        },
    }


router_classes = (
    NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter,
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter,
    OptimizedRegexpRouter, SlicedRegexpRouter, HashedRegexpRouter,
    StateMachineRouter,
)

urlpaths = (
    '/api/aaa/',
    '/api/aaa/123.json',
    '/api/zzz/',
    '/api/zzz/789.json',
)

def validate(urlpath, result):
    if urlpath.endswith(('/123', '/123.json')):
        assert result == (DummyAPI, DummyAPI.do_show, [123]), "result=%r" % (result,)
    elif urlpath.endswith(('/789', '/789.json')):
        assert result == (DummyAPI, DummyAPI.do_show, [789]), "result=%r" % (result,)
    else:
        assert result == (DummyAPI, DummyAPI.do_index, []), "result=%r" % (result,)


loop = 1000 * 1000
with Benchmarker(loop, width=39, cycle=1, extra=0) as bench:

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
