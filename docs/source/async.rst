*****
Async
*****

Fastapi-icontract works out-of-the-box with the async functions in conditions and
snapshot captures.
If a condition or a capture returns a `coroutine`_, the `coroutine`_ is awaited first
and then tested for truthiness or captured, respectively.

.. _coroutine: https://docs.python.org/3/glossary.html#term-coroutine

However, Python 3 does not allow async lambdas (see `this Python issue`_), so you
need to use a third-party library such as `asyncstdlib`_.

.. _this Python issue: https://bugs.python.org/issue33447
.. _asyncstdlib: https://pypi.org/project/asyncstdlib/

For example, note how we transform each ``book`` in the result in the following
post-condition and verify that the author of the book exists in the system
using an async function ``has_author``:

.. code-block:: python3

    @app.get("/books_in_category", response_model=List[Book])
    @fastapi_icontract.require(
        has_category,
        status_code=404,
        description="The category must exist."
    )
    @fastapi_icontract.ensure(
        lambda result: a.all(await_each(has_author(book.author) for book in result)),
        description="One ore more authors of the resulting books do not exist."
    )
    async def books_in_category(category: str) -> Any:
        """Retrieve the books of the given category from the database."""

The full example is available at :func:`tests.example.books_in_category`.
