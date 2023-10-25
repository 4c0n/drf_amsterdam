from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework import renderers
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_extensions.mixins import DetailSerializerMixin
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.settings import api_settings

from rest_framework_xml.renderers import XMLRenderer

from .renderers import PaginatedCSVRenderer
from .pagination import HALPagination
from .serializers import (  # noqa: F401
    DisplayField, DataSetSerializerMixin, get_links,
    HALSerializer, LinksField, RelatedSummaryField,
    SelfLinkSerializerMixin
)

DEFAULT_RENDERERS = [
    renderers.JSONRenderer,
    PaginatedCSVRenderer,
    renderers.BrowsableAPIRenderer,
    XMLRenderer,
]


if api_settings.DEFAULT_RENDERER_CLASSES:
    DEFAULT_RENDERERS = api_settings.DEFAULT_RENDERER_CLASSES


class _DisabledHTMLFilterBackend(DjangoFilterBackend):
    """See https://github.com/tomchristie/django-rest-framework/issues/3766.

    This prevents DRF from generating the filter dropdowns (which can be HUGE
    in our case)
    """

    def to_html(self, request: Request, queryset: QuerySet, view: APIView) -> str:
        return ""


def _is_detailed_request(detailed_keyword, request):
    value = request.GET.get(detailed_keyword, False)
    if value and value in [1, '1', True, 'True', 'yes']:
        return True


class DatapuntViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet subclass for use in Datapunt APIs.

    Note:
    - this uses HAL JSON style pagination.
    """

    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination
    filter_backends = (_DisabledHTMLFilterBackend,)
    # TO restore filter box in your view!
    # filter_backends = (DjangoFilterBackend,)
    detailed_keyword = 'detailed'

    def list(self, request, *args, **kwargs):
        # Checking if a detailed response is required
        if _is_detailed_request(self.detailed_keyword, request):
            self.serializer_class = self.serializer_detail_class
        return super().list(request, *args, **kwargs)

    def get_renderer_context(self):
        # make CSV select fields to render.
        context = super().get_renderer_context()
        context['header'] = (
            self.request.GET['fields'].split(',')
            if 'fields' in self.request.GET else None)
        return context


class DatapuntViewSetWritable(DetailSerializerMixin, viewsets.ModelViewSet):
    """ViewSet subclass for use in Datapunt APIs.

    Note:
    - this uses HAL JSON style pagination.
    """

    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination
    filter_backends = (_DisabledHTMLFilterBackend,)

    detailed_keyword = 'detailed'

    def list(self, request, *args, **kwargs):
        # Checking if a detailed response is required
        if _is_detailed_request(self.detailed_keyword, request):
            self.serializer_class = self.serializer_detail_class
        return super().list(request, *args, **kwargs)
