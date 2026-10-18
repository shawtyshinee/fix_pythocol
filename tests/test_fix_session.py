"""End-to-end examples using a local FIX 4.4 acceptor and initiator."""

import socket
import threading
import uuid
from pathlib import Path

import pytest
import quickfix as fix

from src import Acceptor, Initiator, Message, MessageNotFound


FIX_VERSION = "FIX.4.4"


@pytest.fixture
def session_pair(monkeypatch):
    project_dir = Path(__file__).resolve().parents[1]
    # QuickFIX also creates global logs relative to the working directory.
    monkeypatch.chdir(project_dir)
    # Ask the OS for an available port.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    store = project_dir / "FixPythocolSession"
    log = project_dir / "FixPythocolLogs"
    store.mkdir(exist_ok=True)
    log.mkdir(exist_ok=True)
    config = {"FileStorePath": str(store), "FileLogPath": str(log)}

    suffix = uuid.uuid4().hex[:8]
    server, client = f"SERVER{suffix}", f"CLIENT{suffix}"
    acceptor = Acceptor(FIX_VERSION, server, client, port, **config)
    initiator = Initiator(FIX_VERSION, client, server, port, host="127.0.0.1", ReconnectInterval=1, **config)
    errors = []

    def start_acceptor():
        try:
            acceptor.start()
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=start_acceptor, daemon=True)
    thread.start()
    try:
        initiator.start()
        thread.join(timeout=6)
        assert not thread.is_alive(), "acceptor did not finish logging on"
        assert not errors, f"acceptor failed to start: {errors}"
        yield acceptor, initiator
    finally:
        initiator.stop()
        acceptor.stop()
        thread.join(timeout=6)


def order(order_id="order-1"):
    return Message({35: "D", 11: order_id, 55: "AAPL", 54: "1", 60: "20260101-12:00:00", 40: "1"})


def execution_report(order_id, sender, target):
    return Message({8: FIX_VERSION, 49: sender, 56: target, 35: "8", 37: "server-1", 17: "exec-1", 150: "0", 39: "0", 11: order_id, 55: "AAPL", 54: "1", 151: "10", 14: "0", 6: "0"})


def ids(session):
    return session.getSenderCompID().getValue(), session.getTargetCompID().getValue()


def test_logon_and_admin_messages(session_pair):
    acceptor, initiator = session_pair
    assert fix.Session.lookupSession(acceptor.session).isLoggedOn()
    assert fix.Session.lookupSession(initiator.session).isLoggedOn()
    logon = initiator.wait_admin_message(timeout=3)[0]
    assert logon.get(35) == "A"
    assert logon.get(8) == FIX_VERSION
    assert (logon.get(49), logon.get(56)) == ids(acceptor.session)


def test_initiator_sends_order_to_acceptor(session_pair):
    acceptor, initiator = session_pair
    message = order()
    initiator.send(message)
    received = acceptor.wait_message(timeout=3)[0]
    assert (received.get(35), received.get(11), received.get(55)) == ("D", "order-1", "AAPL")
    assert (received.get(8), received.get(49), received.get(56)) == (FIX_VERSION, *ids(initiator.session))
    assert (message.get(8), message.get(49), message.get(56)) == (FIX_VERSION, *ids(initiator.session))


def test_acceptor_rule_sends_execution_report(session_pair):
    acceptor, initiator = session_pair
    acceptor.add_rule(lambda message: message.get(35) == "D", lambda app, message: app.send(execution_report(message.get(11), *ids(acceptor.session))))
    initiator.send(order("order-2"))
    received_order = acceptor.wait_message(timeout=3)[0]
    report = initiator.wait_message(timeout=3)[0]
    assert received_order.get(11) == "order-2"
    assert (report.get(35), report.get(11), report.get(39)) == ("8", "order-2", "0")
    assert (report.get(49), report.get(56)) == ids(acceptor.session)


def test_acceptor_default_response(session_pair):
    acceptor, initiator = session_pair
    acceptor.add_default_response(execution_report("default", *ids(acceptor.session)))
    initiator.send(order())
    assert acceptor.wait_message(timeout=3)[0].get(11) == "order-1"
    assert initiator.wait_message(timeout=3)[0].get(11) == "default"


def test_wait_message_times_out_when_no_application_message_arrives(session_pair):
    acceptor, initiator = session_pair
    with pytest.raises(MessageNotFound):
        acceptor.wait_message(timeout=0)
    with pytest.raises(MessageNotFound):
        initiator.wait_message(timeout=0)
