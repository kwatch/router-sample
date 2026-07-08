# -*- coding: utf-8 -*-

##
## See:
##      https://pythonhosted.org/Benchmarker/
## for details of 'benchmarker.py'.
##

import sys, os, re
from benchmarker import Benchmarker

from minikeight import (
    on, RequestHandler,
    NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter, HashedLinearRouter,
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter,
    OptimizedRegexpRouter, SlicedRegexpRouter, HashedRegexpRouter,
    TrieRouter, StateMachineRouter,
)


router_classes = (
    NaiveLinearRouter,
    PrefixLinearRouter,
    FixedLinearRouter,
    HashedLinearRouter,
    #
    NaiveRegexpRouter,
    SmartRegexpRouter,
    NestedRegexpRouter,
    OptimizedRegexpRouter,
    SlicedRegexpRouter,
    HashedRegexpRouter,
    #
    TrieRouter,
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


class MockAPI(RequestHandler):

    with on.path(''):

        @on('GET')
        def do_any(self, *params):
            return {"params": params}


benchtype = os.environ.get('BENCHTYPE') or None
if benchtype == None:

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

    import string
    dct = {}
    for c in string.ascii_lowercase:
        path = "/%s" % (c * 3)   # ex: "/aaa", "/bbb", ...
        dct[path] = DummyAPI
        dct[path+"/{id:int}/comments"] = CommentDummyAPI
        #dct[path+"/{id:int}/comments/{comment_id:int}/blabla"] = BlablaAPI
    mapping = {"/api": dct}
    ## same as below
    #mapping = {
    #    "/api": {
    #        {"/aaa": DummyAPI, "/aaa/{id:int}/comments": CommentDummyAPI},
    #        {"/bbb": DummyAPI, "/bbb/{id:int}/comments": CommentDummyAPI},
    #        {"/ccc": DummyAPI, "/ccc/{id:int}/comments": CommentDummyAPI},
    #        {"/ddd": DummyAPI, "/ddd/{id:int}/comments": CommentDummyAPI},
    #        {"/eee": DummyAPI, "/eee/{id:int}/comments": CommentDummyAPI},
    #        {"/fff": DummyAPI, "/fff/{id:int}/comments": CommentDummyAPI},
    #        {"/ggg": DummyAPI, "/ggg/{id:int}/comments": CommentDummyAPI},
    #        {"/hhh": DummyAPI, "/hhh/{id:int}/comments": CommentDummyAPI},
    #        {"/iii": DummyAPI, "/iii/{id:int}/comments": CommentDummyAPI},
    #        {"/jjj": DummyAPI, "/jjj/{id:int}/comments": CommentDummyAPI},
    #        {"/kkk": DummyAPI, "/kkk/{id:int}/comments": CommentDummyAPI},
    #        {"/lll": DummyAPI, "/lll/{id:int}/comments": CommentDummyAPI},
    #        {"/mmm": DummyAPI, "/mmm/{id:int}/comments": CommentDummyAPI},
    #        {"/nnn": DummyAPI, "/nnn/{id:int}/comments": CommentDummyAPI},
    #        {"/ooo": DummyAPI, "/ooo/{id:int}/comments": CommentDummyAPI},
    #        {"/ppp": DummyAPI, "/ppp/{id:int}/comments": CommentDummyAPI},
    #        {"/qqq": DummyAPI, "/qqq/{id:int}/comments": CommentDummyAPI},
    #        {"/rrr": DummyAPI, "/rrr/{id:int}/comments": CommentDummyAPI},
    #        {"/sss": DummyAPI, "/sss/{id:int}/comments": CommentDummyAPI},
    #        {"/ttt": DummyAPI, "/ttt/{id:int}/comments": CommentDummyAPI},
    #        {"/uuu": DummyAPI, "/uuu/{id:int}/comments": CommentDummyAPI},
    #        {"/vvv": DummyAPI, "/vvv/{id:int}/comments": CommentDummyAPI},
    #        {"/www": DummyAPI, "/www/{id:int}/comments": CommentDummyAPI},
    #        {"/xxx": DummyAPI, "/xxx/{id:int}/comments": CommentDummyAPI},
    #        {"/yyy": DummyAPI, "/yyy/{id:int}/comments": CommentDummyAPI},
    #        {"/zzz": DummyAPI, "/zzz/{id:int}/comments": CommentDummyAPI},
    #    },
    #}

elif benchtype == "many":

    urlpaths = (
        '/api/aaa000/',
        '/api/zzz099/',
        '/api/aaa000/123.json',
        '/api/zzz099/789.json',
        '/api/aaa000/123/comments/999.json',
        '/api/zzz099/789/comments/999.json',
        #'/api/aaa000/123/comments/999/blabla/888.json',
        #'/api/zzz099/789/comments/999/blabla/888.json',
    )

    import string
    dct = {}
    for i in range(100):
        for c in string.ascii_lowercase:
            path = "/%s" % (c * 3) + "%03d" % i
            dct[path] = DummyAPI
            dct[path+"/{id:int}/comments"] = CommentDummyAPI
            #dct[path+"/{id:int}/comments/{comment_id:int}/blabla"] = BlablaAPI
    mapping = {"/api": dct}

elif benchtype == "githubapi":

    urlpaths = [
        #'/repos/{owner}/{repo}',
        '/repos/owner1/repo2',
        #'/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments',
        '/repos/owner1/repo2/pulls/333/reviews/444/comments',
        #'/teams/{team_id}/memberships/{username}',
        '/teams/12345/memberships/username1',
    ]
    urlpaths = [ "/api" + x for x in urlpaths ]

    datafile = "data/github-api-paths.txt"
    dct = {}
    callback = lambda m: m.group(0).replace('-', '_')  # ex: '{foo-id}' -> '{foo_id}'
    with open(datafile) as f:
        for line in f:
            #urlpath = line.strip()
            urlpath = re.sub(r'\{.*\}', callback, line.strip())
            if not urlpath:
                continue
            if urlpath.startswith('#'):
                continue
            dct[urlpath] = MockAPI
    mapping = {"/api": dct}

else:

    raise Exception("%s : Unknonw benchmark type." % (benchtype,))


def validate(urlpath, result):
    if benchtype == None or benchtype == "many":
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
    elif benchtype == "githubapi":
        if urlpath == "/api/repos/owner1/repo2":
            assert result == (MockAPI, MockAPI.do_any, ["owner1", "repo2"]), "result=%r" % (result,)
        elif urlpath == "/api/repos/owner1/repo2/pulls/333/reviews/444/comments":
            assert result == (MockAPI, MockAPI.do_any, ["owner1", "repo2", "333", "444"]), "result=%r" % (result,)
        elif urlpath == "/api/teams/12345/memberships/username1":
            assert result == (MockAPI, MockAPI.do_any, ["12345", "username1"]), "result=%r" % (result,)
        else:
            assert False, "urlpath=%r" % (urlpath,)
    else:
        raise Exception("%s : Unknonw benchmark type." % (benchtype,))


loop = int(os.environ.get('N') or 1000 * 1000)
width = 17 + max( len(x) for x in urlpaths )
with Benchmarker(loop, width=width, cycle=1, extra=0) as bench:

    debug = bench.properties.get('debug', False)

    for router_class in router_classes:
        for urlpath in urlpaths:
            label = router_class.__name__.replace('Router', '')
            if router_class.__name__.startswith("Hashed"):
                router_obj = router_class(mapping, r'^/api/\w\w')
            else:
                router_obj = router_class(mapping)

            @bench("%-15s: %-16s" % (label, urlpath))
            def _(bm, router=router_obj, urlpath=urlpath):
                for _ in bm:
                    result = router.lookup('GET', urlpath)
                #
                if debug:
                    validate(urlpath, result)
