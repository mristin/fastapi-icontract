***************
Post-conditions
***************
.. py:currentmodule:: fastapi_icontract

The `post-conditions`_ are the conditions which must hold *after* the execution
of the endpoint.

.. _post-conditions: https://en.wikipedia.org/wiki/Postcondition

You specify the post-conditions using the decorator :class:`ensure`.

`Post-conditions`_ usually involve comparing the state *before* and *after* the request
to an endpoint.
The state *after* the request is directly available to the post-condition.

Snapshots
=========
However, you need to specifically instruct fastapi-icontract which state needs to be
capture *before* the request.
This is done by using snapshots with the decorator :class:`snapshot`.

Examples
========

Here is a simple snippet that involves only a post-condition
(see the :ref:`full example <full-example>`):

.. code-block:: python3

    import asyncstdlib as a

    from fastapi_icontract import ensure

    @app.get("/books_in_category", response_model=List[Book])
    @ensure(
        lambda result: a.all(a.await_each(has_author(book.author) for book in result)),
        description="One ore more authors of the resulting books do not exist."
    )
    async def books_in_category(category: str) -> Any:
        """Retrieve the books of the given category from the database."""
        ...

The following snippet is a rather sophisticated one that involves both
the post-condition and a snapshot
(see the :ref:`full example <full-example>`):

.. code-block:: python3

    import asynstdlib as a
    from fastapi_icontract import snapshot, ensure

    @app.post("/upsert_book")
    @snapshot(lambda book: has_book(book.identifier), name="has_book")
    @snapshot(lambda: book_count(), name="book_count")
    @ensure(lambda book: has_book(book.identifier))
    @ensure(
        lambda book, OLD: a.apply(
            lambda a_book_count: (
                    OLD.book_count + 1 == a_book_count if not OLD.has_book
                    else OLD.book_count == a_book_count),
            book_count()))
    async def add_book(book: Book) -> None:
        ...
