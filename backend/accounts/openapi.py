from drf_spectacular.utils import extend_schema

AUTH_TAG = "auth"
TFA_AUTH_TAG = "2FA-auth"


def _schema(tag, *, request=None, responses=None, summary=None):
    kwargs = {"tags": [tag]}
    if summary:
        kwargs["summary"] = summary
    if request is not None:
        kwargs["request"] = {
            "application/json": request,
            "application/x-www-form-urlencoded": request,
        }
    if responses is not None:
        kwargs["responses"] = responses
    return extend_schema(**kwargs)


def auth_schema(*, request=None, responses=None, summary=None):
    return _schema(AUTH_TAG, request=request, responses=responses, summary=summary)


def tfa_auth_schema(*, request=None, responses=None, summary=None):
    return _schema(TFA_AUTH_TAG, request=request, responses=responses, summary=summary)
