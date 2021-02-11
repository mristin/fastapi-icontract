"""Provide decorators for the endpoints."""

import inspect
import traceback
from typing import Optional

import fastapi
import icontract
import icontract._checkers
import icontract._represent
import icontract._types

import fastapi_icontract.openapi
from fastapi_icontract._globals import CallableT


def _func_body_as_text(func: CallableT) -> str:
    """Represent the condition as text to be included in the specs."""
    if not icontract._represent.is_lambda(a_function=func):
        return func.__name__

    lines, condition_lineno = inspect.findsource(func)
    filename = inspect.getsourcefile(func)
    assert filename is not None, f"Unexpected None filename for condition: {func}"

    decorator_inspection = icontract._represent.inspect_decorator(
        lines=lines, lineno=condition_lineno, filename=filename
    )
    lambda_inspection = icontract._represent.find_lambda_condition(
        decorator_inspection=decorator_inspection
    )

    assert (
        lambda_inspection is not None
    ), f"Expected lambda_inspection to be non-None if is_lambda is True on: {func}"

    return lambda_inspection.text


class require:  # pylint: disable=invalid-name
    """Decorate a FastAPI endpoint with a pre-condition."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        condition: CallableT,
        status_code: int = 422,
        description: Optional[str] = None,
        enforced: bool = True,
        undocument: bool = False,
    ) -> None:
        """
        Initialize.

        :param condition:
            pre-condition predicate.

            The arguments of the pre-condition are expected to be a subset
            of the endpoint arguments.

            It can either be a sync function, a lambda, an async function.
            If the condition returns a coroutine, the coroutine will be awaited
            first, and then checked for truthiness.

        :param status_code:
            If the pre-condition is violated, the checker will raise a
            :class:`fastapi.HTTPException`.
            This ``status_code`` will be indicated in the exception.
        :param description:
            textual description of the pre-condition.

            The ``description`` will be included in the exception if the pre-condition
            is violated.
        :param enforced:
            If set, the pre-condition is enforced.

            Otherwise, the pre-condition is only added to the OpenAPI schema,
            but is not verified.
            Usually, you enforce certain slow pre-conditions during testing and then
            disable them in production.
            An unenforced pre-condition is however still useful for the client as a
            formal documentation which is at least verified during testing.
        :param undocument:
            If set, the pre-condition is not documented in the OpenAPI schema.

        """
        # pylint: disable=too-many-arguments
        self.condition = condition
        self.description = description
        self.status_code = status_code

        self.undocument = undocument

        self.enforced = enforced
        self._contract = None  # type: Optional[icontract._types.Contract]

        if enforced:
            location = None  # type: Optional[str]
            tb_stack = traceback.extract_stack(limit=2)[:1]
            if len(tb_stack) > 0:
                frame = tb_stack[0]
                location = f"File {frame.filename}, line {frame.lineno} in {frame.name}"

            self._contract = icontract._types.Contract(
                condition=condition,
                description=description,
                error=fastapi.HTTPException(
                    status_code=status_code,
                    detail=(
                        f"Pre-condition violated: {description}"
                        if description
                        else None
                    ),
                ),
                location=location,
            )

    def __call__(self, func: CallableT) -> CallableT:
        """
        Add the pre-condition to the checker of a FastAPI endpoint.

        :param func: endpoint function to be wrapped
        :return: wrapped endpoint
        """
        if not self.enforced:
            result = func
        else:
            assert self._contract is not None, "Expected a contract if enforced."

            contract_checker = icontract._checkers.find_checker(func=func)
            if contract_checker is None:
                contract_checker = icontract._checkers.decorate_with_checker(func=func)

            result = contract_checker

            icontract._checkers.add_precondition_to_checker(
                checker=contract_checker, contract=self._contract
            )

        if not self.undocument:
            openapi_contracts = fastapi_icontract.openapi.get_or_attach(func=result)

            text = _func_body_as_text(func=self.condition)
            openapi_contracts.preconditions.append(
                fastapi_icontract.openapi.Contract(
                    enforced=self.enforced,
                    text=text,
                    status_code=self.status_code,
                    description=self.description,
                )
            )

        return result


class snapshot:  # pylint: disable=invalid-name
    """
    Add a snapshot to the checker of an FastAPI endpoint.

    This will decorate the endpoint with a snapshot of argument values captured
    *prior* to the invocation.

    A snapshot is defined by a capture function (usually a lambda) that accepts
    one or more arguments of the function.

    The captured values are supplied to post-conditions with the OLD argument of
    the condition.
    """

    def __init__(
        self,
        capture: CallableT,
        name: str,
        enabled: bool = True,
        undocument: bool = False,
    ) -> None:
        """
        Initialize.

        :param capture:
            function to capture the snapshot accepting a one or more arguments of
            the original function *prior* to the execution.

            The ``capture`` can either be a lambda, a sync function or an async
            function.
            If ``capture`` returns a coroutine, the coroutine will be first awaited
            before it is stored into the ``OLD`` structure.
        :param name: name of the snapshot as will be stored in the OLD structure.
        :param enabled:
            The snapshot is applied only if ``enabled`` is set.
            Otherwise, the snapshot is disabled and there is no run-time overhead.

            Usually the snapshots are enabled and disabled together with their
            related post-conditions.
        :param undocument:
            If set, the snapshot is not documented in the OpenAPI schema.

        """
        self.capture = capture
        self._snapshot = None  # type: Optional[icontract._types.Snapshot]
        self.enabled = enabled
        self.name = name

        # Resolve the snapshot only if enabled so that no overhead is incurred
        if enabled:
            location = None  # type: Optional[str]
            tb_stack = traceback.extract_stack(limit=2)[:1]
            if len(tb_stack) > 0:
                frame = tb_stack[0]
                location = f"File {frame.filename}, line {frame.lineno} in {frame.name}"

            self._snapshot = icontract._types.Snapshot(
                capture=capture, name=name, location=location
            )

        self.undocument = undocument

    def __call__(self, func: CallableT) -> CallableT:
        """
        Add the snapshot to the checker of a FastAPI endpoint ``func``.

        The function ``func`` is expected to be decorated with
        at least one postcondition before the snapshot.

        :param func: function whose arguments we need to snapshot
        :return: ``func`` as given in the input
        """
        if not self.enabled:
            result = func
        else:
            # Find a contract checker
            contract_checker = icontract._checkers.find_checker(func=func)

            if contract_checker is None:
                raise ValueError(
                    "You are decorating a function with a snapshot, "
                    "but no postcondition was defined on the function before."
                )

            result = contract_checker

            assert (
                self._snapshot is not None
            ), "Expected the enabled snapshot to have the property ``snapshot`` set."

            icontract._checkers.add_snapshot_to_checker(
                checker=contract_checker, snapshot=self._snapshot
            )

        if not self.undocument:
            openapi_contracts = fastapi_icontract.openapi.get_or_attach(func=result)

            text = _func_body_as_text(func=self.capture)
            openapi_contracts.snapshots.append(
                fastapi_icontract.openapi.Snapshot(
                    name=self.name, enabled=self.enabled, text=text
                )
            )

        return result


class ensure:  # pylint: disable=invalid-name
    """Decorate a FastAPI endpoint with a post-condition."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        condition: CallableT,
        status_code: int = 500,
        description: Optional[str] = None,
        enforced: bool = True,
        undocument: bool = False,
    ) -> None:
        """
        Initialize.

        :param condition:
            post-condition predicate.

            The arguments of the post-condition are expected to be a subset
            of the endpoint arguments.

            It can either be a sync function, a lambda, an async function.
            If the condition returns a coroutine, the coroutine will be awaited
            first, and then checked for truthiness.

        :param status_code:
            If the post-condition is violated, the checker will raise a
            :class:`fastapi.HTTPException`.
            This ``status_code`` will be indicated in the exception.
        :param description:
            textual description of the post-condition.

            The ``description`` will be included in the exception if the post-condition
            is violated.
        :param enforced:
            If set, the post-condition is enforced.

            Otherwise, the post-condition is only added to the OpenAPI schema,
            but is not verified.
            Usually, you enforce post-conditions during testing and then
            disable them all in production.
            An unenforced post-condition is however still useful for the client as a
            formal documentation which is at least verified during testing.
        :param undocument:
            If set, the post-condition is not documented in the OpenAPI schema.


        """
        # pylint: disable=too-many-arguments
        self.condition = condition
        self.status_code = status_code
        self.description = description
        self.enforced = enforced
        self.undocument = undocument

        self._contract = None  # type: Optional[icontract._types.Contract]

        if enforced:
            location = None  # type: Optional[str]
            tb_stack = traceback.extract_stack(limit=2)[:1]
            if len(tb_stack) > 0:
                frame = tb_stack[0]
                location = f"File {frame.filename}, line {frame.lineno} in {frame.name}"

            self._contract = icontract._types.Contract(
                condition=condition,
                description=description,
                error=fastapi.HTTPException(
                    status_code=status_code,
                    detail=(
                        f"Post-condition violated: {description}"
                        if description
                        else None
                    ),
                ),
                location=location,
            )

    def __call__(self, func: CallableT) -> CallableT:
        """
        Add the postcondition to the checker of a FastAPI endpoint.

        If the endpoint has not been already wrapped with a checker,
        this will wrap it with a checker first.

        :param func: endpoint function to be wrapped
        :return: wrapped endpoint
        """
        if not self.enforced:
            result = func
        else:
            assert self._contract is not None, "Expected a contract if enforced."

            contract_checker = icontract._checkers.find_checker(func=func)
            if contract_checker is None:
                contract_checker = icontract._checkers.decorate_with_checker(func=func)

            result = contract_checker

            icontract._checkers.add_postcondition_to_checker(
                checker=contract_checker, contract=self._contract
            )

        if not self.undocument:
            openapi_contracts = fastapi_icontract.openapi.get_or_attach(func=result)

            text = _func_body_as_text(func=self.condition)
            openapi_contracts.postconditions.append(
                fastapi_icontract.openapi.Contract(
                    enforced=self.enforced,
                    text=text,
                    status_code=self.status_code,
                    description=self.description,
                )
            )

        return result
