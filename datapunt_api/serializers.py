"""
Serialization classes for Datapunt style Django REST Framework APIs.
"""
from collections import OrderedDict
from typing import Mapping, Any

from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.relations import RelatedField
from rest_framework.reverse import reverse
import json


def get_links(
        view_name: str,
        kwargs: Mapping[str, Any] | None = None,
        request: HttpRequest | None = None
) -> OrderedDict:
    result = OrderedDict([
        ('self', dict(
            href=reverse(view_name, kwargs=kwargs, request=request)
        ))
    ])

    return result


class DataSetSerializerMixin:
    """Add dataset field to indicate 'source' of this data."""
    def to_representation(self, obj):
        result = super().to_representation(obj)
        result['dataset'] = self.dataset
        return result


class LinksField(serializers.HyperlinkedIdentityField):

    def to_representation(self, value):
        request = self.context.get('request')

        result = OrderedDict([
            ('self', dict(
                href=self.get_url(value, self.view_name, request, None))
             ),
        ])

        return result


class HALSerializer(serializers.HyperlinkedModelSerializer):
    url_field_name: str = '_links'
    serializer_url_field: type[RelatedField] = LinksField


# TODO: check that this is needed (vs just using the HALSerializer above).
class SelfLinkSerializerMixin:
    def get__links(self, obj):
        """
        Serialization of _links field for detail view (assumes ModelViewSet).

        Note:
            Used to provide HAL-JSON style self links.
        """
        view = self.context['view']
        model = view.queryset.model
        pk_value = getattr(obj, model._meta.pk.name)

        return {
            'self': {
                'href': view.reverse_action('detail', args=[pk_value])
            }
        }


class RelatedSummaryField(serializers.Field):
    def to_representation(self, value):
        count = value.count()
        model_name = value.model.__name__
        mapping = model_name.lower() + "-list"
        url = reverse(mapping, request=self.context['request'])

        parent_pk = value.instance.pk
        filter_name = list(value.core_filters.keys())[0]

        return dict(
            count=count,
            href="{}?{}={}".format(url, filter_name, parent_pk),
        )


# Note about DisplayField below; setting source to '*' causes the
# whole (model) instance to be passed to the DisplayField See:
# http://www.django-rest-framework.org/api-guide/fields/#source
# Display field then uses the __str__ function on the Django
# model to get a nice string representation that can be presented
# to the user.

class DisplayField(serializers.Field):
    """
    Add a `_display` field, based on Model string representation.
    """
    def __init__(self, *args, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return str(value)


class MultipleGeometryField(serializers.Field):

    read_only = True

    def get_attribute(self, obj):
        # Checking if point geometry exists. If not returning the
        # regular multipoly geometry
        return obj.geometrie

    def to_representation(self, value):
        # Serialize the GeoField. Value could be either None,
        # Point or MultiPoly
        res = ''
        if value:
            res = json.loads(value.geojson)
        return res
