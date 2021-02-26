***********************************
Visualizing Contracts in Swagger UI
***********************************
.. py:currentmodule:: fastapi_icontract

Assuming you include contracts in OpenAPI schema (see :ref:`contracts-in-openapi`),
they will be available per each path as a ``x-contracts`` extension field.
Unfortunately, Swagger UI does not pretty-prints extension fields, so that the contracts
end up barely readable as a long single-line string.

While you might inspect the OpenAPI specification, it is much more convenient to read
contracts in a nice structured layout.
To that end, we developed `swagger-ui-plugin-contracts`_, a JavaScript plugin that can
be readily included in Swagger UI.

.. _swagger-ui-plugin-contracts: https://github.com/mristin/swagger-ui-plugin-contracts

There are a couple of options how you can include the plugin in the Swagger UI of your
``app``.

Use ``set_up_route_for_docs_with_contracts_plugin``
===================================================

The most straightforward way is to replace the documentation route (*i.e.*, the route
corresponding to Swagger UI) is rendered.

First, you need to explicitly tell your ``app`` to skip creating the documentation route
at setup by setting ``docs_url=None``:

.. code-block:: python3

    app = FastAPI(docs_url=None)

Fastapi-icontracts gives you the function
:func:`set_up_route_for_docs_with_contracts_plugin` which
creates the documentation route with the contracts plugin included.

You need to call it explicitly once the ``app`` has been set up
(see the :ref:`full example <full-example>`):

.. code-block:: python3

    fastapi_icontract.set_up_route_for_docs_with_contracts_plugin(
        app=app, path="/docs")

From then on, Swagger UI with `swagger-ui-plugin-contracts`_ will be available at
``"/docs"`` path.

Specify Your Own Documentation Endpoint
=======================================
:func:`fastapi_icontract.set_up_route_for_docs_with_contracts_plugin` does not
really provide a way to customize the documentation endpoint.

For example, it does not allow you to specify a different URL from where
`swagger-ui-plugin-contracts`_ should be fetched, or add additional plugins.
If you need such more involved customizations, you need to specify the documentation
endpoint yourself.

If you only need to change the URLs of the relevant files (*e.g.*, to Swagger UI,
`swagger-ui-plugin-contracts`_, *etc.*), you can use the function
:func:`fastapi_icontract.swagger_ui.get_swagger_ui_html`:

If you need to include additional Swagger UI plugins or customize otherwise
the HTML code of the documentation, you need to re-write your own version
of :func:`fastapi_icontract.swagger_ui.get_swagger_ui_html`.
