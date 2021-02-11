************
Transactions
************

Fastapi-icontract is not aware of the transactions.

This is especially relevant for concurrent systems where multiple clients modify a
shared resource (*e.g.*, a database) at the same time.
If you are not careful, you can end up with quite a few
`time-of-check-time-of-use (TOCTOU)`_ errors.

.. _time-of-check-time-of-use (TOCTOU): https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use

A possible approach to use transaction both in the contracts *and* the endpoint is to
introduce a decorator on top of fastapi-icontract decorators which will start
a transaction and pass it down to the contracts and the function, and then close it
when the underlying call stack is executed.

For example:

.. code-block:: python3

    from fastapi_icontract import require

    @app.get("/books_in_category", response_model=List[Book])
    @start_transaction  # This passes ``txn`` to the underlying function and contracts
    @require(
        lambda txn, category: has_category(txn, category),
        status_code=404,
        description="The category must exist."
    )
    async def books_in_category(category: str) -> Any:
        """Retrieve the books of the given category from the database."""
        ...

How you implement the ``start_transaction`` depends on your particular system, and
we present its usage here just for illustration.
