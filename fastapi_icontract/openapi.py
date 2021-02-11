"""Define data structures to be added to the OpenAPI specs."""
import functools
from typing import List, Any, Optional, Dict

import fastapi
import fastapi.openapi.utils

from fastapi_icontract._globals import CallableT


class Contract:
    """Describe a contract of an operation."""

    def __init__(
        self, enforced: bool, text: str, status_code: int, description: Optional[str]
    ) -> None:
        """Initialize with the given values."""
        self.enforced = enforced
        self.text = text
        self.status_code = status_code
        self.description = description


class Snapshot:
    """Describe a snapshot involved in an operation."""

    def __init__(self, name: str, enabled: bool, text: str) -> None:
        """Initialize with the given values."""
        self.name = name
        self.enabled = enabled
        self.text = text


class Contracts:
    """Describe all the contracts of an operation."""

    def __init__(self) -> None:
        """Initialize with the empty values."""
        self.preconditions = []  # type: List[Contract]
        self.snapshots = []  # type: List[Snapshot]
        self.postconditions = []  # type: List[Contract]


def get_or_attach(func: CallableT) -> Contracts:
    """Get or create the attribute of the endpoint for the contracts."""
    if not hasattr(func, "__fastapi_icontract_openapi__"):
        contracts = Contracts()

        setattr(func, "__fastapi_icontract_openapi__", contracts)
    else:
        contracts = getattr(func, "__fastapi_icontract_openapi__")

    return contracts


def _contract_to_jsonable(contract: Contract) -> Dict[str, Any]:
    """Convert the contract to a JSON-able structure."""
    jsonable = {
        "enforced": contract.enforced,
        "text": contract.text,
        "language": "python3",
        "statusCode": contract.status_code,
    }
    if contract.description:
        jsonable["description"] = contract.description

    return jsonable


def _snapshot_to_jsonable(snapshot: Snapshot) -> Dict[str, Any]:
    """Convert the snapshot to a JSON-able structure."""
    jsonable = {
        "name": snapshot.name,
        "enabled": snapshot.enabled,
        "text": snapshot.text,
        "language": "python3",
    }

    return jsonable


def contracts_to_jsonable(contracts: Contracts) -> Dict[str, Any]:
    """Convert the contracts to a JSON-able structure."""
    return {
        "preconditions": [
            _contract_to_jsonable(contract) for contract in contracts.preconditions
        ],
        "snapshots": [
            _snapshot_to_jsonable(snapshot) for snapshot in contracts.snapshots
        ],
        "postconditions": [
            _contract_to_jsonable(contract) for contract in contracts.postconditions
        ],
    }


def wrap_openapi_with_contracts(app: fastapi.FastAPI) -> None:
    """Wrap the ``openapi`` method of the ``app`` to include the contracts in the schema."""
    old_openapi_func = app.openapi

    # Delete the cached openapi_schema so that we can re-create it
    app.openapi_schema = None

    def wrapper() -> Optional[Dict[str, Any]]:
        # Retrieve from cache, if possible
        if app.openapi_schema is not None:
            return app.openapi_schema

        openapi_schema = old_openapi_func()

        operation_contracts = dict()  # type: Dict[str, Contracts]

        for route in app.routes:
            if (
                not isinstance(route, fastapi.routing.APIRoute)
                or not route.include_in_schema
            ):
                continue

            contracts = getattr(route.endpoint, "__fastapi_icontract_openapi__", None)

            if contracts is None:
                continue

            assert isinstance(contracts, Contracts)

            for method in route.methods:
                operation_id = fastapi.openapi.utils.generate_operation_id(
                    route=route, method=method
                )

                assert (
                    operation_id is not None
                ), f"Unexpected None operation ID for endpoint {route.endpoint}"

                assert (
                    operation_id not in operation_contracts
                ), f"Unexpected duplicate contracts for operation ID: {operation_id}"
                operation_contracts[operation_id] = contracts

        # Find the operation in the schema
        for path in openapi_schema["paths"].values():
            for operation in path.values():
                operation_id = operation.get("operationId", None)
                if operation_id is not None and operation_id in operation_contracts:
                    contracts = operation_contracts[operation_id]
                    operation["x-contracts"] = contracts_to_jsonable(contracts)

        # Cache
        app.openapi_schema = openapi_schema

        return openapi_schema

    functools.update_wrapper(wrapper=wrapper, wrapped=old_openapi_func)
    app.openapi = wrapper  # type: ignore
