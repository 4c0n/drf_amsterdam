from collections import OrderedDict
from typing import Any

from rest_framework import pagination, response
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class HALPagination(pagination.PageNumberPagination):
    """Implement HAL-JSON style pagination.

    used on most rest Datapunt APIs.
    """

    page_size_query_param: str = 'page_size'

    def get_paginated_response(self, data: Any) -> Response:
        assert self.request is not None

        self_link = self.request.build_absolute_uri()
        if self_link.endswith(".api"):
            self_link = self_link[:-4]

        assert self.page is not None

        if self.page.has_next():
            next_link = replace_query_param(
                self_link, self.page_query_param, self.page.next_page_number())
        else:
            next_link = None

        if self.page.has_previous():
            prev_link = replace_query_param(
                self_link, self.page_query_param,
                self.page.previous_page_number())
        else:
            prev_link = None

        return response.Response(OrderedDict([
            ('_links', OrderedDict([
                ('self', dict(href=self_link)),
                ('next', dict(href=next_link)),
                ('previous', dict(href=prev_link)),
            ])),
            ('count', self.page.paginator.count),
            ('results', data)
        ]))


class HALCursorPagination(pagination.CursorPagination):
    """Implement HAL-JSON Cursor style pagination.

    standard for large datasets Datapunt APIs.
    """
    page_size_query_param = 'page_size'
    count_table = True
    count = 0

    def paginate_queryset(self, queryset, request, view=None):
        if self.count_table:
            self.count = queryset.count()
        return super(HALCursorPagination, self).paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        self_link = self.base_url
        if self_link.endswith(".api"):
            self_link = self_link[:-4]

        next_link = self.get_next_link()
        previous_link = self.get_previous_link()

        _response = OrderedDict([
            ('_links', OrderedDict([
                ('next', dict(href=next_link)),
                ('previous', dict(href=previous_link)),
            ])),
            ('count', self.count),
            ('results', data)
        ])

        if not self.count_table:
            _response.pop('count')

        return response.Response(_response)
