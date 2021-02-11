**************
Pre-conditions
**************
.. py:currentmodule:: fastapi_icontract

The `pre-conditions`_ are the conditions which must hold *prior* to the execution
of the endpoint.

.. _pre-conditions: https://en.wikipedia.org/wiki/Precondition

You specify the `pre-conditions`_ using the decorator
:class:`require`.

Here is a snippet demonstrating how to specify a pre-condition
(see the :ref:`full example <full-example>`):

.. code-block:: python3

    from fastapi_icontract import require

    @app.get("/books_in_category", response_model=List[Book])
    @require(
        has_category,
        status_code=404,
        description="The category must exist."
    )
    async def books_in_category(category: str) -> Any:
        ...
