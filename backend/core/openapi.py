from drf_spectacular.utils import extend_schema, extend_schema_view

CORE_TAG = "core"
ME_TAG = "me"
PROVIDER_TAG = "provider"
CUSTOMER_TAG = "customer"
MARKETPLACE_TAG = "marketplace"


def _schema(tag, request=None, responses=None, summary=None):
    kwargs = {"tags": [tag]}
    if request is not None:
        kwargs["request"] = request
    if responses is not None:
        kwargs["responses"] = responses
    if summary is not None:
        kwargs["summary"] = summary
    return extend_schema(**kwargs)


def core_read_only_viewset(viewset_cls):
    """Group list/retrieve operations under the Swagger tag 'core'."""
    return extend_schema_view(
        list=extend_schema(tags=[CORE_TAG]),
        retrieve=extend_schema(tags=[CORE_TAG]),
    )(viewset_cls)


def me_schema(**kwargs):
    return _schema(ME_TAG, **kwargs)


def provider_schema(**kwargs):
    return _schema(PROVIDER_TAG, **kwargs)


def customer_schema(**kwargs):
    return _schema(CUSTOMER_TAG, **kwargs)


def marketplace_schema(**kwargs):
    return _schema(MARKETPLACE_TAG, **kwargs)
