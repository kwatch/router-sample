# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from oktest import ok, test, subject, situation, at_end

from minikeight import (
    Router,
    NaiveLinearRouter, PrefixLinearRouter, FixedLinearRouter,
    NaiveRegexpRouter, SmartRegexpRouter, NestedRegexpRouter,
    StateMachineRouter,
)
from mock_handler import HomeAPI, BooksAPI, BookCommentsAPI, OrdersAPI, mapping


class MockRouter(Router):

    def find(self, req_path):
        d = {
            "/":
                (HomeAPI, {"GET": HomeAPI.do_home}, []),
            "/api/v1/books.json":
                (BooksAPI, {"GET": BooksAPI.do_index, "POST": BooksAPI.do_create}, []),
            "/api/v1/books/123.json":
                (BooksAPI, {"GET": BooksAPI.do_show, "PUT": BooksAPI.do_update, "DELETE": BooksAPI.do_delete}, [123]),
            "/api/v1/orders/":
                (OrdersAPI, {"GET": OrdersAPI.do_index, "POST": OrdersAPI.do_create}, []),
            "/api/v1/orders/123.html":
                (OrdersAPI, {"GET": OrdersAPI.do_show, "PUT": OrdersAPI.do_update, "DELETE": OrdersAPI.do_delete}, [123]),
            "/api/v1/orders/123.json":
                (OrdersAPI, {"GET": OrdersAPI.do_show, "PUT": OrdersAPI.do_update, "DELETE": OrdersAPI.do_delete}, [123]),
        }
        return d.get(req_path)


class Router_TestCase(object):

    def provide_router(self):
        return MockRouter()

    with subject('#lookup()'):

        @test("returns tuple when found.")
        def _(self, router):
            t = router.lookup("GET", "/api/v1/books.json")
            ok (t) == (BooksAPI, BooksAPI.do_index, [])
            t = router.lookup("POST", "/api/v1/books.json")
            ok (t) == (BooksAPI, BooksAPI.do_create, [])
            t = router.lookup("GET", "/api/v1/books/123.json")
            ok (t) == (BooksAPI, BooksAPI.do_show, [123])
            t = router.lookup("PUT", "/api/v1/books/123.json")
            ok (t) == (BooksAPI, BooksAPI.do_update, [123])
            t = router.lookup("DELETE", "/api/v1/books/123.json")
            ok (t) == (BooksAPI, BooksAPI.do_delete, [123])
            #
            t = router.lookup("GET", "/api/v1/orders/")
            ok (t) == (OrdersAPI, OrdersAPI.do_index, [])
            t = router.lookup("POST", "/api/v1/orders/")
            ok (t) == (OrdersAPI, OrdersAPI.do_create, [])
            t = router.lookup("GET", "/api/v1/orders/123.html")
            ok (t) == (OrdersAPI, OrdersAPI.do_show, [123])
            t = router.lookup("PUT", "/api/v1/orders/123.html")
            ok (t) == (OrdersAPI, OrdersAPI.do_update, [123])
            t = router.lookup("DELETE", "/api/v1/orders/123.html")
            ok (t) == (OrdersAPI, OrdersAPI.do_delete, [123])


class Router_TestBase(object):

    ROUTER_CLASS = None
    TUPLE_TYPE   = tuple

    def provide_router(self):
        return self.ROUTER_CLASS(mapping)

    def provide_tupletype(self):
        return self.TUPLE_TYPE

    def _test_when_found(self, router):
        tupletype = self.TUPLE_TYPE
        c = HomeAPI
        t = router.find('/')
        methods = {"GET": c.do_home}
        ok (t) == (c, methods, [])
        ##
        c = BooksAPI
        t = router.find('/api/v1/books.json')
        methods = {"GET": c.do_index, "POST": c.do_create}
        ok (t) == (c, methods, [])
        #
        t = router.find('/api/v1/books/123.json')
        methods = {"GET": c.do_show, "PUT": c.do_update, "DELETE": c.do_delete}
        ok (t) == (c, methods, [123])
        ##
        c = OrdersAPI
        t = router.find('/api/v1/orders/')
        methods = {"GET": c.do_index, "POST": c.do_create}
        ok (t) == (c, methods, [])
        #
        t = router.find('/api/v1/orders/123.json')
        methods = {"GET": c.do_show, "PUT": c.do_update, "DELETE": c.do_delete}
        ok (t) == (c, methods, [123])
        ##
        c = BookCommentsAPI
        t = router.find('/api/v1/books/123/comments')
        methods = {"GET": c.do_index, "POST": c.do_create}
        ok (t) == (c, methods, [123])
        #
        t = router.find('/api/v1/books/123/comments/abcd')
        methods = {"GET": c.do_show, "PUT": c.do_update, "DELETE": c.do_delete}
        ok (t) == (c, methods, [123, 'abcd'])

    def _test_when_not_found(self, router):
        ok (router.find('')) == None
        #
        ok (router.find('/api/v1/books/')) == None
        ok (router.find('/api/v1/books/abc.json')) == None
        ok (router.find('/api/v1/books/123.html')) == None
        #
        ok (router.find('/api/v1/orders')) == None
        ok (router.find('/api/v1/orders/abc.html')) == None
        ok (router.find('/api/v1/orders/123.html/')) == None
        #
        ok (router.find('/api/v1/books/')) == None
        ok (router.find('/api/v1/books/123/comments/abcd.json')) == None
        ok (router.find('/api/v1/books/123/comments/abcd/')) == None

    def _test_suffix_pattern(self, router):
        tupletype = self.TUPLE_TYPE
        c = OrdersAPI
        methods = {"GET": c.do_show, "PUT": c.do_update, "DELETE": c.do_delete}
        #
        t = router.find('/api/v1/orders/123.json')
        ok (t) == (c, methods, [123])
        #
        t = router.find('/api/v1/orders/123.html')
        ok (t) == (c, methods, [123])
        #
        t = router.find('/api/v1/orders/123')
        ok (t) == (c, methods, [123])

    with subject("#find()"):

        @test("returns tuple when found.")
        def _(self, router):
            self._test_when_found(router)

        @test("returns None when not found.")
        def _(self, router):
            self._test_when_not_found(router)

        @test("supports '.*' as suffix pattern.")
        def _(self, router):
            self._test_suffix_pattern(router)


class NaiveLinearRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = NaiveLinearRouter


class PrefixLinearRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = PrefixLinearRouter


class FixedLinearRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = FixedLinearRouter


class NaiveRegexpRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = NaiveRegexpRouter


class SmartRegexpRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = SmartRegexpRouter


class NestedRegexpRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = NestedRegexpRouter


class StateMachineRouter_TestCase(Router_TestBase):
    ROUTER_CLASS = StateMachineRouter
    TUPLE_TYPE = staticmethod(lambda xs: [ (int(x) if x.isdigit() else x) for x in xs ])


if __name__ == '__main__':
    import oktest
    oktest.main()
