.. _contracts-in-openapi:

********************************
Documenting Contracts in OpenAPI
********************************

Fastapi-icontract provides the function
:func:`fastapi_icontract.wrap_openapi_with_contracts` so that you can include
the contracts in the ``openapi.json`` endpoint of your FastAPI ``app``.

The function is called once the ``app`` has been fully specified
(see the :ref:`full example <full-example>`):

.. code-block:: python3

    fastapi_icontract.wrap_openapi_with_contracts(app=app)

The function will override the ``app.openapi`` method and cache the results
for efficiency.

The modified schema is afterwards available at ``app.openapi_url`` (usually set to the
default ``"/openapi.json"``).
