from drf_spectacular.utils import extend_schema


def json_and_form_request(serializer):
    """Document JSON (API clients) and form POST (Swagger Try it out)."""

    return extend_schema(
        request={
            "application/json": serializer,
            "application/x-www-form-urlencoded": serializer,
        },
    )
