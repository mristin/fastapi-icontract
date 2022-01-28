*****************
FastAPI-icontract
*****************

.. image:: https://github.com/mristin/fastapi-icontract/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/fastapi-icontract/actions/workflows/ci.yml
    :alt: Continuous integration

.. image:: https://coveralls.io/repos/github/mristin/fastapi-icontract/badge.svg?branch=master
    :target: https://coveralls.io/github/mristin/fastapi-icontract?branch=main
    :alt: Test coverage

.. image:: https://badge.fury.io/py/fastapi-icontract.svg
    :target: https://badge.fury.io/py/fastapi-icontract
    :alt: PyPI - version

.. image:: https://img.shields.io/pypi/pyversions/fastapi-icontract.svg
    :alt: PyPI - Python Version

FastAPI-icontract is a `FastAPI`_ extension for design-by-contract which leverages
`icontract`_ to allow you to specify and enforce code contracts in your
`FastAPI endpoints`_.

.. _FastAPI: https://fastapi.tiangolo.com/
.. _icontract: https://github.com/Parquery/icontract
.. _FastAPI endpoints: https://fastapi.tiangolo.com/tutorial/first-steps/

Depending on how you set it up, FastAPI-icontract will:

* automatically **enforce** the contracts during testing or in production,
* automatically add the contracts to your **OpenAPI specification**, and
* render the **Swagger UI** with a specialized contracts plugin for nicer visualization.

Benefits of Adding Contracts to Your API
========================================

Enforcing code contracts in your FastAPI development opens up new venues for approaches
to more `systematic design`_ at the API level:

.. _systematic design: https://cacm.acm.org/blogs/blog-cacm/227928-why-not-program-right/fulltext

* Contracts are an important **part of the specification**.

  Unlike human language, contracts written in code are unambiguous.
* Contracts are **automatically verifiable**.

  Your clients can rest assured that you actually run them.
  FastAPI-icontract will specify precisely which contracts are run in production and
  which were only verified during testing.
* Contracts provide **deeper testing**.

  If you have a mesh of microservices that you need to test in conjunction,
  turn on all the contracts and test against your *client's* data instead of your own
  limited unit test data.
* Contracts specified in code allow for automatic **client-side** verification.

  Thus you can signal formally to the client up-front what you expect
  (using pre-conditions), while the client can verify what to expect back from you
  (using post-conditions).
* Contracts are **not just for input validation**.

  Though you can use contracts for input validation as well, FastAPI already allows you
  to specify how you want your `input verified`_.
  Contracts, on the other hand, really shine when you want to specify relations
  *between* the endpoints.
* Contracts allow for **automatic test generation**.

  Tools for property-based testing such as `Schemathesis`_ can automatically generate
  test data and verify that your API works as expected.
  Post-conditions are an easy way to define your properties to be tested.

  There is an ongoing discussion with the authors of the `Schemathesis`_ how to
  integrate it with tools which generate data based on contracts such as
  `icontract-hypothesis`_.
* Contracts open up **a wider ecosystem for analysis**.

  When you decorate the endpoints with contracts, you can immediately use analysis
  tools such as `CrossHair`_ to analyze your code and find bugs.

  (Though this only makes sense for really stateless, purely functional endpoints.)

.. _input verified: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
.. _Schemathesis: https://github.com/schemathesis/schemathesis
.. _icontract-hypothesis: https://github.com/mristin/icontract-hypothesis
.. _CrossHair: https://github.com/pschanely/CrossHair

Teaser
======

The full documentation is available at: `fastapi-icontract.readthedocs.io`_.

.. _fastapi-icontract.readthedocs.io: https://fastapi-icontract.readthedocs.io

The following example is meant to invite you to further explore the extension.

.. code-block:: python

    from typing import Optional, List, Any

    from fastapi import FastAPI
    from pydantic import BaseModel
    import asyncstdlib as a

    from fastapi_icontract import (
        require, snapshot, ensure,
        wrap_openapi_with_contracts,
        set_up_route_for_docs_with_contracts_plugin
    )

    app = FastAPI()

    @app.get("/has_author", response_model=bool)
    async def has_author(identifier: str):
        """Check if the author exists in the database."""
        ...

    @app.get("/categories", response_model=List[str])
    async def get_categories():
        """Retrieve the list of available categories."""
        ...

    class Book(BaseModel):
        identifier: str
        author: str

    @app.get("/has_category", response_model=bool)
    async def has_category(identifier: str):
        """Check if the author exists in the database."""
        ...

    @app.get("/books_in_category", response_model=List[Book])
    @require(
        has_category, status_code=404, description="The category must exist."
    )
    @ensure(
        lambda result: a.all(a.await_each(has_author(book.author) for book in result)),
        description="One ore more authors of the resulting books do not exist."
    )
    async def books_in_category(category: str) -> Any:
        """Retrieve the books of the given category from the database."""
        ...

    @app.get("/has_book", response_model=bool)
    async def has_book(book_id: str) -> Any:
        """Check whether the book exists."""
        ...

    @app.get("/book_count", response_model=int)
    async def book_count() -> Any:
        """Count the available books."""
        ...

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

    # Include contracts in /openapi.json
    wrap_openapi_with_contracts(app=app)

    # Include swagger-ui-plugin-contracts in /doc
    set_up_route_for_docs_with_contracts_plugin(app=app)

Versioning
==========
We follow `Semantic Versioning`_.
The version X.Y.Z indicates:

* X is the major version (backward-incompatible),
* Y is the minor version (backward-compatible), and
* Z is the patch version (backward-compatible bug fix).

.. _Semantic Versioning: http://semver.org/spec/v1.0.0.html
