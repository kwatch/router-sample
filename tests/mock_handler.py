# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from minikeight import on, RequestHandler


class HomeAPI(RequestHandler):

    with on.path(''):

        @on('GET')
        def do_home(self):
            return {"action": "home"}


class BooksAPI(RequestHandler):

    with on.path('.json'):

        @on('GET')
        def do_index(self):
            return {"action": "index"}

        @on('POST')
        def do_create(self):
            return {"action": "create"}

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


class BookCommentsAPI(RequestHandler):

    with on.path(''):

        @on('GET')
        def do_index(self, book_id):
            return {"action": "index", "book_id": book_id}

        @on('POST')
        def do_create(self, book_id):
            return {"action": "create", "book_id": book_id}

    with on.path('/{code}'):

        @on('GET')
        def do_show(self, book_id, code):
            return {"action": "show", "book_id": book_id, "code": code}

        @on('PUT')
        def do_update(self, book_id, code):
            return {"action": "update", "book_id": book_id, "code": code}

        @on('DELETE')
        def do_delete(self, book_id, code):
            return {"action": "delete", "book_id": book_id, "code": code}


class OrdersAPI(RequestHandler):

    with on.path('/'):

        @on('GET')
        def do_index(self):
            return {"action": "index"}

        @on('POST')
        def do_create(self):
            return {"action": "create"}

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

    with on.path('/{id:int}/edit.html'):

        @on('GET')
        def show_edit_form(self, id):
            return {"action": "show", "id": id}

        @on('POST')
        def post_edit_form(self, id):
            return {"action": "show", "id": id}

LIST_MAPPING = [
    (r'/'                  , HomeAPI),
    (r'/api/v1', [
        (r'/books'         , BooksAPI),
        (r'/books/{book_id:int}/comments', BookCommentsAPI),
        (r'/orders'        , OrdersAPI),
    ]),
]
MAPPING = LIST_MAPPING
