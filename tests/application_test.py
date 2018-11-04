# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from oktest import ok, test, subject, situation, at_end

from minikeight import Application, new_env, StartResponse
from mock_handler import mapping

app = Application(mapping)


class Application_TestCase(object):

    def provide_sr(self):
        return StartResponse()

    with subject('#__call__()'):

        @test("returns response body.")
        def _(self):
            sr = StartResponse()
            x = app(new_env('GET', '/api/v1/books.json'), sr)
            ok (x) == [b'{"action":"index"}']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "18")]
            #
            sr = StartResponse()
            x = app(new_env('GET', '/api/v1/books/123.json'), sr)
            ok (x) == [b'{"action":"show","id":123}']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "26")]
            #
            sr = StartResponse()
            x = app(new_env('POST', '/api/v1/books/123/comments'), sr)
            ok (x) == [b'{"action":"create","book_id":123}']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "33")]
            #
            sr = StartResponse()
            x = app(new_env('PUT', '/api/v1/books/123/comments/abcd'), sr)
            ok (x) == [b'{"action":"update","book_id":123,"code":"abcd"}']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "47")]
            #
            sr = StartResponse()
            x = app(new_env('PUT', '/api/v1/orders/123.json'), sr)
            ok (x) == [b'{"action":"update","id":123}']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "28")]

        @test("response body is empty when request method is HEAD.")
        def _(self):
            sr = StartResponse()
            x = app(new_env('HEAD', '/api/v1/books.json'), sr)
            ok (x) == [b'']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "18")]
            #
            sr = StartResponse()
            x = app(new_env('HEAD', '/api/v1/books/123.json'), sr)
            ok (x) == [b'']
            ok (sr.status) == "200 OK"
            ok (sr.headers) == [("Content-Type", "application/json"),
                                ("Content-Length", "26")]

        @test("returns 404 when not found.")
        def _(self):
            sr = StartResponse()
            x = app(new_env("GET", "/api/v1/books/abc.json"), sr)
            ok (x) == [b'<h2>404 Not Found</h2>']
            ok (sr.status) == "404 Not Found"
            ok (sr.headers) == [("Content-Type", "text/html;charset=utf-8"),
                                ("Content-Length", "22")]

        @test("returns 405 when method not allowed.")
        def _(self):
            sr = StartResponse()
            x = app(new_env("POST", "/api/v1/books/123.json"), sr)
            ok (x) == [b'<h2>405 Method Not Allowed</h2>']
            ok (sr.status) == "405 Method Not Allowed"
            ok (sr.headers) == [("Content-Type", "text/html;charset=utf-8"),
                                ("Content-Length", "31")]

        @test("redirects to '/path/' or '/path' if possible.")
        def _(self):
            sr = StartResponse()
            for meth in ("GET", "HEAD"):
                x = app(new_env(meth, "/api/v1/orders"), sr)
                ok (x) == [b'redirect to /api/v1/orders/']
                ok (sr.status) == "301 Moved Permanently"
                ok (sr.headers) == [("Content-Type", "text/plain;charset=utf-8"),
                                    ("Content-Length", "27"),
                                    ("Location", "/api/v1/orders/")]
            #
            for meth in ("GET", "HEAD"):
                sr = StartResponse()
                x = app(new_env(meth, "/api/v1/orders/123/"), sr)
                ok (x) == [b'redirect to /api/v1/orders/123']
                ok (sr.status) == "301 Moved Permanently"
                ok (sr.headers) == [("Content-Type", "text/plain;charset=utf-8"),
                                    ("Content-Length", "30"),
                                    ("Location", "/api/v1/orders/123")]

        @test("redirect is available only when GET or HEAD method.")
        def _(self):
            sr = StartResponse()
            x = app(new_env("POST", "/api/v1/orders"), sr)
            ok (x) == [b'<h2>404 Not Found</h2>']
            ok (sr.status) == "404 Not Found"
            ok (sr.headers) == [("Content-Type", "text/html;charset=utf-8"),
                                ("Content-Length", "22")]


if __name__ == '__main__':
    import oktest
    oktest.main()
