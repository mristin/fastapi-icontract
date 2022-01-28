"""Test the example from the readme."""
import json
import os
import pathlib
import unittest

import httpx

import tests_3_8.example_async


class TestBooks(unittest.IsolatedAsyncioTestCase):
    async def test_ok(self) -> None:
        async with httpx.AsyncClient(
                app=tests_3_8.example_async.app, base_url="http://test") as ac:
            response = await ac.get("/books_in_category", params={"category": "sci-fi"})
            self.assertEqual(200, response.status_code)
            self.assertListEqual(
                [{'author': "Margaret Cavendish",
                  'identifier': "The Blazing World",
                  "category": "sci-fi"}],
                response.json())

    async def test_precondition_violated(self) -> None:
        async with httpx.AsyncClient(
                app=tests_3_8.example_async.app, base_url="http://test") as ac:
            response = await ac.get(
                "/books_in_category", params={"category": "non-fiction"})
            self.assertEqual(404, response.status_code)
            self.assertDictEqual(
                {'detail': 'Pre-condition violated: The category must exist.'},
                response.json())

    async def test_upsert_existing_book(self) -> None:
        async with httpx.AsyncClient(
                app=tests_3_8.example_async.app, base_url="http://test") as ac:
            response = await ac.post(
                "/upsert_book",
                json={"identifier": "Jane Eyre",
                      "author": "Charlotte Brontë",
                      "category": "romance"})
            self.assertEqual(200, response.status_code)

class TestOpenAPI(unittest.IsolatedAsyncioTestCase):
    async def test_the_content(self)->None:
        async with httpx.AsyncClient(
                app=tests_3_8.example_async.app, base_url="http://test") as ac:
            response = await ac.get("/openapi.json")

            expected_pth = pathlib.Path(
                os.path.realpath(__file__)).parent / "example_async_schema.json"

            expected = json.loads(expected_pth.read_text())
            self.assertDictEqual(expected, response.json())

class TestDoc(unittest.IsolatedAsyncioTestCase):
    async def test_the_content(self)->None:
        async with httpx.AsyncClient(
                app=tests_3_8.example_async.app, base_url="http://test") as ac:
            response = await ac.get("/docs")

            expected_pth = pathlib.Path(
                os.path.realpath(__file__)).parent / "example_async_docs.html"

            expected = expected_pth.read_text()
            self.assertEqual(expected, response.text)


if __name__ == '__main__':
    unittest.main()
