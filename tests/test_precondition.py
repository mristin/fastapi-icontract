import unittest
from typing import Optional, Tuple, List, Dict, Any

import fastapi
import fastapi.openapi.utils
import httpx

import fastapi_icontract

app = fastapi.FastAPI()


@app.get("/passes_no_description_and_no_status_code")
@fastapi_icontract.require(lambda: True)
async def passes_no_description_and_no_status_code() -> Any:
    return


@app.get("/passes_no_description_and_with_status_code")
@fastapi_icontract.require(lambda: True, status_code=404)
async def passes_no_description_and_with_status_code() -> Any:
    return


@app.get("/passes_description_and_with_status_code")
@fastapi_icontract.require(lambda: True, status_code=404,
                           description="Something.")
async def passes_description_and_with_status_code() -> Any:
    return


def this_func_will_raise() -> None:
    raise Exception("This exception should have never been raised.")


@app.get("/passes_with_not_enforced")
@fastapi_icontract.ensure(lambda: this_func_will_raise(), enforced=False)
async def passes_with_not_enforced() -> Any:
    return


@app.get("/fails_no_description_and_no_status_code")
@fastapi_icontract.require(lambda: False)
async def fails_no_description_and_no_status_code() -> Any:
    return


@app.get("/fails_no_description_and_with_status_code")
@fastapi_icontract.require(lambda: False, status_code=404)
async def fails_no_description_and_with_status_code() -> Any:
    return


@app.get("/fails_description_and_with_status_code")
@fastapi_icontract.require(lambda: False, status_code=404,
                           description="Something.")
async def fails_description_and_with_status_code() -> Any:
    return

class TestTable(unittest.IsolatedAsyncioTestCase):
    async def test_through(self) -> None:
        table = [
            ("/passes_no_description_and_no_status_code", 200, None),
            ("/passes_no_description_and_with_status_code", 200, None),
            ("/passes_description_and_with_status_code", 200, None),
            ("/passes_with_not_enforced", 200, None),
            # Mind that FastAPI sets the detail of the response automatically to
            # a message describing the error.
            ("/fails_no_description_and_no_status_code", 422, "Unprocessable Entity"),
            ("/fails_no_description_and_with_status_code", 404, "Not Found"),
            ("/fails_description_and_with_status_code", 404,
             "Pre-condition violated: Something.")
        ]  # type: List[Tuple[str, int, Optional[str]]]

        for route, expected_status_code, expected_detail in table:
            async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(route)

                self.assertEqual(
                    expected_status_code, response.status_code,
                    f"While testing the route: {route}")

                detail = None  # type: Optional[str]
                if response.json() and "detail" in response.json():
                    detail = response.json()["detail"]

                self.assertEqual(expected_detail, detail,
                                 f"While testing the route: {route}")

if __name__ == '__main__':
    unittest.main()
