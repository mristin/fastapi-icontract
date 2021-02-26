"""Implement the example from the readme."""
from typing import List, TypeVar, Iterable, Awaitable, Callable, AsyncIterable, Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import asyncstdlib as a

import fastapi_icontract

app = FastAPI(docs_url=None)

# The functions ``async_apply`` and ``await_each`` are copy/pasted
# from asyncstdlib which are to appear in the next release.

T = TypeVar('T')


async def async_apply(
        __func: Callable[..., T], *args: Awaitable[Any], **kwargs: Awaitable[Any]
) -> T:
    """Await the arguments and keyword arguments and then apply ``func`` on them."""
    return __func(
        *[await arg for arg in args], **{k: await arg for k, arg in kwargs.items()}
    )


async def await_each(awaitables: Iterable[Awaitable[T]]) -> AsyncIterable[T]:
    """
    Iterate through ``awaitables`` and await each item.

    This converts an *iterable of async* into an *async iterator* of awaited values.

    Consequently, we can apply various functions made for ``AsyncIterable[T]`` to
    ``Iterable[Awaitable[T]]`` as well.

    Example:
    .. code-block:: python3
        import asyncstdlib as a
         async def check1() -> bool:
              ...
        async def check2() -> bool:
              ...
        async def check3() -> bool:
              ...
         okay = await a.all(
             a.await_each(
                 [check1(), check2(), check3()]))
    """
    for awaitable in awaitables:
        yield await awaitable

class Book(BaseModel):
    identifier: str
    author: str
    category: str


# This is our mock database.
BOOKS = [
    Book(identifier="The Blazing World", author="Margaret Cavendish", category="sci-fi"),
    Book(identifier="Pride and Prejudice", author="Jane Austen", category="romance")
]


@app.get("/has_author", response_model=bool)
async def has_author(identifier: str) -> Any:
    """Check if the author exists in the database."""
    return identifier in {book.author for book in BOOKS}


@app.get("/has_category", response_model=bool)
async def has_category(category: str) -> Any:
    return category in {book.category for book in BOOKS}


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
    result = [book for book in BOOKS if book.category == category]
    return result


@app.get("/has_book", response_model=bool)
async def has_book(book_id: str) -> Any:
    """Check whether the book exists."""
    return book_id in [book.identifier for book in BOOKS]


@app.get("/book_count", response_model=int)
async def book_count() -> Any:
    """Count the available books."""
    return len(BOOKS)


@app.post("/upsert_book")
@fastapi_icontract.snapshot(lambda book: has_book(book.identifier), name="has_book")
@fastapi_icontract.snapshot(lambda: book_count(), name="book_count")
@fastapi_icontract.ensure(lambda book: has_book(book.identifier))
@fastapi_icontract.ensure(
    lambda book, OLD: async_apply(
        lambda a_book_count: (
                OLD.book_count + 1 == a_book_count if not OLD.has_book
                else OLD.book_count == a_book_count),
        book_count()))
async def add_book(book: Book) -> None:
    existing_book = next(
        (a_book for a_book in BOOKS if a_book.identifier == book.identifier), None)

    if existing_book:
        existing_book.author = book.author
        existing_book.category = book.category
    else:
        BOOKS.append(book)


fastapi_icontract.wrap_openapi_with_contracts(app=app)
fastapi_icontract.set_up_route_for_docs_with_contracts_plugin(app=app)

if __name__ == "__main__":
    print("Serving the example server on http://localhost:8000.\n"
          "Have a look for the Swagger UI with the contracts plugin at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
