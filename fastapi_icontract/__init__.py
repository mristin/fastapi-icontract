"""Specify contracts for FastAPI endpoints."""

# pylint: disable=invalid-name

__version__ = "0.0.2"
__author__ = "Marko Ristin"
__license__ = "License :: OSI Approved :: MIT License"
__status__ = "Alpha"

import fastapi_icontract._decorators
import fastapi_icontract.openapi
import fastapi_icontract.swagger_ui

require = fastapi_icontract._decorators.require
snapshot = fastapi_icontract._decorators.snapshot
ensure = fastapi_icontract._decorators.ensure

wrap_openapi_with_contracts = fastapi_icontract.openapi.wrap_openapi_with_contracts
set_up_route_for_docs_with_contracts_plugin = (
    fastapi_icontract.swagger_ui.set_up_route_for_docs_with_contracts_plugin
)
