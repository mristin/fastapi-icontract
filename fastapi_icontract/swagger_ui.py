"""Provide rendering of Swagger UI with the contracts plugin included."""

import json
from typing import Optional, Dict, Any

import fastapi
import fastapi.openapi.docs
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import HTMLResponse


def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    swagger_ui_plugin_contracts_url: str = "https://unpkg.com/swagger-ui-plugin-contracts",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    """
    Generate the HTML for Swagger UI endpoint.

    This is a patched version of the original fastapi.applications.get_swagger_ui_html
    which includes a separate JavaScript code to display contracts in a pretty format.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script src="{swagger_ui_plugin_contracts_url}"></script>
    <script>
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
    """

    if oauth2_redirect_url:
        html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

    html += """
        dom_id: '#swagger-ui',
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        plugins: [
            ContractsPlugin
        ],
        layout: "BaseLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true
    })"""

    if init_oauth:
        html += f"""
        ui.initOAuth({json.dumps(jsonable_encoder(init_oauth))})
        """

    html += """
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


def set_up_route_for_docs_with_contracts_plugin(
    app: fastapi.FastAPI, path: str = "/docs"
) -> None:
    """
    Set up the route for Swagger UI with included plugin swagger-ui-plugin-contracts.

    The path must not be set before.
    You must explicitly tell FastAPI to exclude it during initialization with:

    .. code-block:: python

        app = FastAPI(docs_url=None)
    """
    for route in app.routes:
        if not isinstance(route, fastapi.routing.APIRoute):
            continue

        assert isinstance(route, fastapi.routing.APIRoute)

        if route.path == path and "GET" in route.methods:
            raise ValueError(
                f"The FastAPI app {app} has already the route with the method 'GET' set up for "
                f"{path!r}. "
                f"No route with method 'GET' must be set for {path!r} if you want to set up "
                f"an alternative Swagger UI with contracts plugin."
            )

    if app.openapi_url is None:
        raise ValueError(
            f"The FastAPI app {app} has the OpenAPI URL set to None. "
            f"Swagger UI with contracts plug-in can not be generated "
            f"if OpenAPI schema is not available."
        )

    # The part below has been adapted from fastapi.applications.FastAPI.setup()

    async def swagger_ui_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
        if oauth2_redirect_url:
            oauth2_redirect_url = root_path + oauth2_redirect_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=oauth2_redirect_url,
            init_oauth=app.swagger_ui_init_oauth,
        )

    app.add_route(path, swagger_ui_html, include_in_schema=False)

    if app.swagger_ui_oauth2_redirect_url:
        oauth2_already_set_up = False

        for route in app.routes:
            if not isinstance(route, fastapi.routing.APIRoute):
                continue

            assert isinstance(route, fastapi.routing.APIRoute)

            if (
                route.path == app.swagger_ui_oauth2_redirect_url
                and "GET" in route.methods
            ):
                oauth2_already_set_up = True

        if not oauth2_already_set_up:
            # We need to set up the Oauth2 route if it has not been already set since
            # it will be not automatically set in app.setup().
            #
            # Here is the relevant part of the app.setup() implementation:
            #
            # .. code-block:: python
            #
            #     if self.openapi_url and self.docs_url:
            #         ...
            #         if self.swagger_ui_oauth2_redirect_url:
            #             ...
            #

            async def swagger_ui_redirect(
                req: Request,  # pylint: disable=unused-argument
            ) -> HTMLResponse:
                return fastapi.openapi.docs.get_swagger_ui_oauth2_redirect_html()

            app.add_route(
                app.swagger_ui_oauth2_redirect_url,
                swagger_ui_redirect,
                include_in_schema=False,
            )
