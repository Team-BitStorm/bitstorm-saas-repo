from drf_spectacular.utils import extend_schema, extend_schema_view

CORE_TAG = "core"


def core_read_only_viewset(viewset_cls):
    """Group list/retrieve operations under the Swagger tag 'core'."""
    return extend_schema_view(
        list=extend_schema(tags=[CORE_TAG]),
        retrieve=extend_schema(tags=[CORE_TAG]),
    )(viewset_cls)
