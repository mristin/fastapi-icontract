import unittest
from typing import Optional, Tuple, List, Any

import fastapi
import httpx

import fastapi_icontract

app = fastapi.FastAPI()


@app.post("/passes_snapshot_without_name")
@fastapi_icontract.snapshot(lambda lst: lst[:], name="lst")
@fastapi_icontract.ensure(lambda result, OLD: len(OLD.lst) == result)
async def passes_snapshot_without_name(lst: List[int]) -> Any:
    return len(lst)


@app.post("/passes_snapshot_with_name")
@fastapi_icontract.snapshot(lambda lst: len(lst), name="len_lst")
@fastapi_icontract.ensure(lambda result, OLD: OLD.len_lst == result)
async def passes_snapshot_with_name(lst: List[int]) -> Any:
    return len(lst)


@app.post("/fails_snapshot_without_name")
@fastapi_icontract.snapshot(lambda lst: lst[:], name="lst")
@fastapi_icontract.ensure(lambda result, OLD: len(OLD.lst) == result)
async def fails_snapshot_without_name(lst: List[int]) -> Any:
    return len(lst) + 1  # Here's the error!


@app.post("/fails_snapshot_with_name")
@fastapi_icontract.snapshot(lambda lst: len(lst), name="len_lst")
@fastapi_icontract.ensure(lambda result, OLD: OLD.len_lst == result)
async def fails_snapshot_with_name(lst: List[int]) -> Any:
    return len(lst) + 1  # Here's the error!


def this_func_will_raise() -> None:
    raise Exception("This exception should have never been raised.")


@app.post("/snapshot_not_enforced")
@fastapi_icontract.snapshot(
    lambda: this_func_will_raise(), name="not_raising", enabled=False)
@fastapi_icontract.ensure(lambda: this_func_will_raise(), enforced=False)
async def snapshot_not_enforced(lst: List[int]) -> Any:
    return


class TestTable(unittest.IsolatedAsyncioTestCase):
    async def test_through(self) -> None:
        table = [
            ("/passes_snapshot_without_name", 200),
            ("/passes_snapshot_with_name", 200),
            ("/fails_snapshot_without_name", 500),
            ("/fails_snapshot_with_name", 500),
            ("/snapshot_not_enforced", 200),
        ]  # type: List[Tuple[str, int]]

        for route, expected_status_code in table:
            async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(route, json=[1, 2, 3])

                self.assertEqual(
                    expected_status_code, response.status_code,
                    f"While testing the route: {route}")


if __name__ == '__main__':
    unittest.main()
