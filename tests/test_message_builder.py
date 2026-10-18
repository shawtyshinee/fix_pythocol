"""Tests for reusable order and execution-report builders."""

import allure
import pytest

from src import ExecutionReportContext, Message, OrderContext, build_default_fix_message

pytestmark = allure.feature("FIX message builder")


@allure.story("Execution reports")
@allure.title("Build a FIX 4.4 execution report: {method}")
@allure.description("Build each execution state and verify its FIX 4.4 message type, order status, execution type, and preserved fields.")
@pytest.mark.parametrize(
    "method,status,exec_type",
    [
        ("new", "0", "0"),
        ("fulfill", "2", "F"),
        ("fullfil", "2", "F"),
        ("partfill", "1", "F"),
        ("partial_fill", "1", "F"),
        ("cancel", "4", "4"),
        ("reject", "8", "8"),
        ("pending_new", "A", "A"),
        ("pending_cancel", "6", "6"),
        ("pending_replace", "E", "E"),
    ],
)
def test_execution_report_states(method, status, exec_type):
    original = Message({8: "FIX.4.4", 11: "order-1"})
    context = ExecutionReportContext(original)
    result = getattr(context, method)({17: "exec-1"})
    with allure.step("Verify the callable context and resulting FIX fields"):
        assert result is context
        assert result() is original
        assert [original.get(tag) for tag in (35, 39, 150, 11, 17)] == [
            "8", status, exec_type, "order-1", "exec-1"
        ]


@allure.story("Execution reports")
@allure.title("Use the fill execution code for {version}")
@allure.description("Check legacy and modern fill execution codes and the legacy execution transaction type across FIX versions.")
@pytest.mark.parametrize("version,expected", [("FIX.4.0", None), ("FIX.4.1", "2"), ("FIX.4.2", "2"), ("FIX.4.3", "2"), ("FIX.4.4", "F"), ("FIX.5.0", "F"), ("FIXT.1.1", "F")])
def test_fill_execution_type_depends_on_protocol_version(version, expected):
    message = ExecutionReportContext(Message({8: version})).fulfill()()
    with allure.step("Verify version-specific execution fields"):
        assert message.get(150) == expected
        assert message.get(20) == ("0" if version in ("FIX.4.0", "FIX.4.1", "FIX.4.2") else None)


@allure.story("Execution reports")
@allure.title("Reject pending replace for {version}")
@allure.description("FIX 4.0 and 4.1 do not define the pending replace order state.")
@pytest.mark.parametrize("version", ["FIX.4.0", "FIX.4.1"])
def test_pending_replace_is_not_available_in_early_versions(version):
    with allure.step("Expect the unsupported state to raise ValueError"):
        with pytest.raises(ValueError, match="Pending replace"):
            ExecutionReportContext(Message({8: version})).pending_replace()


@allure.story("Order requests")
@allure.title("Build new and cancel requests")
@allure.description("Construct outgoing new and cancel requests on one mutable message, including order identifiers and side.")
def test_order_context_builds_new_and_cancel_requests():
    message = Message({8: "FIX.4.4", 11: "first", 55: "AAPL"})
    context = OrderContext(message)
    with allure.step("Build and verify a new order request"):
        assert context.new(Side="1")() is message
        assert (message.get(35), message.get(54)) == ("D", "1")
    with allure.step("Build and verify its cancel request"):
        context.cancel({41: "first", 11: "cancel-1"})
        assert (message.get(35), message.get(41), message.get(11)) == ("F", "first", "cancel-1")
        assert message.get(39) is None and message.get(150) is None


@allure.story("Order requests")
@allure.title("Remove execution status fields from a cancel request")
@allure.description("Ensure a cancel request does not retain execution report status or execution type fields.")
def test_order_request_removes_execution_report_status_fields():
    message = Message({35: "8", 39: "6", 150: "6", 11: "first"})
    result = OrderContext(message).cancel({41: "first", 11: "cancel-1"})()
    with allure.step("Verify the request contains no execution status fields"):
        assert result is message
        assert (result.get(35), result.get(39), result.get(150)) == ("F", None, None)


@allure.story("Builder contexts")
@allure.title("Keep order requests and execution reports separate")
@allure.description("Compare the request and report contexts to verify their distinct APIs and FIX message types.")
def test_order_and_execution_report_contexts_have_separate_roles():
    order = OrderContext(Message())
    report = ExecutionReportContext(Message())
    with allure.step("Verify each context exposes its own message types"):
        assert not hasattr(order, "pending_cancel")
        assert not hasattr(order, "fulfill")
        assert (order.new()().get(35), report.new()().get(35)) == ("D", "8")
        assert (order.cancel()().get(35), report.cancel()().get(35)) == ("F", "8")


@allure.story("Default order fields")
@allure.title("Convert lots to units for a limit order")
@allure.description("Verify symbol, quantity in units, limit-order type, and limit price produced by the default builder.")
def test_default_builder_creates_limit_order_fields():
    message = build_default_fix_message("AAPL", quantity=3, lot_size=100, price=12.5)
    with allure.step("Verify the symbol, unit quantity, order type, and price"):
        assert [message.get(tag) for tag in (55, 38, 40, 44)] == ["AAPL", 300, "2", 12.5]


@allure.story("Default order fields")
@allure.title("Reject nonpositive quantity, lot size, or price")
@allure.description("Each input that determines order size or price must be positive.")
@pytest.mark.parametrize("quantity,lot_size,price", [(0, 1, 1), (1, 0, 1), (1, 1, 0)])
def test_default_builder_rejects_nonpositive_values(quantity, lot_size, price):
    with allure.step("Expect invalid order values to raise ValueError"):
        with pytest.raises(ValueError):
            build_default_fix_message("AAPL", quantity, lot_size, price)


@allure.story("Builder contexts")
@allure.title("Require a Message for {context_type}")
@allure.description("Both context types reject objects that are not Message instances.")
@pytest.mark.parametrize("context_type", [OrderContext, ExecutionReportContext])
def test_context_requires_a_message(context_type):
    with allure.step("Expect a non-Message input to raise TypeError"):
        with pytest.raises(TypeError):
            context_type(None)
