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


class CommentDummyAPI(RequestHandler):

    with on.path('/'):

        @on('GET')
        def do_index(self, parent_id):
            return {"action": "index", "parent_id": parent_id}

    #with on.path('/{comment_id:int}.*'):
    with on.path('/{comment_id:int}.json'):

        @on('GET')
        def do_show(self, parent_id, comment_id):
            return {"action": "show", "parent_id": parent_id, "comment_id": comment_id}


class BlablaAPI(RequestHandler):

    with on.path('/'):

        @on('GET')
        def do_index(self, parent_id, comment_id):
            return {"action": "show", "ids": [parent_id, comment_id]}

    #with on.path('/{blabla_id:int}.*'):
    with on.path('/{blabla_id:int}.json'):

        @on('GET')
        def do_show(self, parent_id, comment_id, blabla_id):
            return {"action": "show", "ids": [parent_id, comment_id, blabla_id]}


if True:

    import string
    #arr = []
    #for c in string.ascii_lowercase:
    #    path = "/%s" % (c * 3)
    #    arr.append((path, DummyAPI))
    #    arr.append((path+"/{id:int}/comments", CommentDummyAPI))
    #mapping = [("/api", arr)]
    dct = {}
    for c in string.ascii_lowercase:
        path = "/%s" % (c * 3)
        dct[path] = DummyAPI
        dct[path+"/{id:int}/comments"] = CommentDummyAPI
        #dct[path+"/{id:int}/comments/{comment_id:int}/blabla"] = BlablaAPI
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
    '/api/zzz/',
    '/api/aaa/123.json',
    '/api/zzz/789.json',
    '/api/aaa/123/comments/999.json',
    '/api/zzz/789/comments/999.json',
    #'/api/aaa/123/comments/999/blabla/888.json',
    #'/api/zzz/789/comments/999/blabla/888.json',
)

def validate(urlpath, result):
    if urlpath.endswith(('/123', '/123.json')):
        assert result == (DummyAPI, DummyAPI.do_show, [123]), "result=%r" % (result,)
    elif urlpath.endswith(('/789', '/789.json')):
        assert result == (DummyAPI, DummyAPI.do_show, [789]), "result=%r" % (result,)
    elif urlpath.endswith(('/123/comments/999', '/123/comments/999.json')):
        assert result == (CommentDummyAPI, CommentDummyAPI.do_show, [123, 999]), "result=%r" % (result,)
    elif urlpath.endswith(('/789/comments/999', '/789/comments/999.json')):
        assert result == (CommentDummyAPI, CommentDummyAPI.do_show, [789, 999]), "result=%r" % (result,)
    elif urlpath.endswith(('/blabla/', '/blabla.json')):
        assert result[0:2] == (BlablaAPI, BlablaAPI.do_index), "result=%r" % (result,)
    elif urlpath.endswith(('/blabla/888', '/blabla/888.json')):
        assert result[0:2] == (BlablaAPI, BlablaAPI.do_show), "result=%r" % (result,)
    else:
        assert result == (DummyAPI, DummyAPI.do_index, []), "result=%r" % (result,)


loop = 1000 * 1000
width = 17 + max( len(x) for x in urlpaths )
with Benchmarker(loop, width=width, cycle=1, extra=0) as bench:

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
