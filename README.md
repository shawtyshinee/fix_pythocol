# FIX Pythocol

FIX Pythocol is a small Python wrapper around [QuickFIX](https://www.quickfixengine.org/).
It provides `Initiator`, `Acceptor`, and `Message` classes for opening a FIX
session, exchanging application messages, and writing simple response rules.
FIX 4.4 is the usual starting point; FIX 4.2, FIX 5.0, and FIXT 1.1 are also
accepted by the constructors.

## Installation

Clone the repository, create a virtual environment, and install the runtime
dependency (and pytest if you want to run the examples):

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

The project is used directly from the checkout, so run commands from the
repository root. The import package is currently named `src`.

## Usage

An acceptor listens on a port and an initiator connects to it. Start the
acceptor in a background thread (or in a separate process), then start the
initiator:

```python
import threading

from src import Acceptor, Initiator, Message

acceptor = Acceptor("FIX.4.4", "SERVER", "CLIENT", 9876)
threading.Thread(target=acceptor.start, daemon=True).start()

initiator = Initiator("FIX.4.4", "CLIENT", "SERVER", 9876, host="127.0.0.1")
initiator.start()

acceptor.add_rule(
    lambda message: message.get(35) == "D",
    lambda application, message: application.send(
        Message({
            8: "FIX.4.4", 35: "8", 49: "SERVER", 56: "CLIENT",
            11: message.get(11), 37: "order-1", 39: "0", 150: "0",
        })
    ),
)

initiator.send(Message({35: "D", 11: "order-1", 55: "AAPL", 54: "1", 40: "1"}))
order = acceptor.wait_message()[0]
print(order.get(11))

report = initiator.wait_message()[0]
print(report.get(39))

initiator.stop()
acceptor.stop()
```

`Initiator.send` fills in missing `BeginString (8)`, `SenderCompID (49)`,
and `TargetCompID (56)` fields. Use `wait_admin_message()` for logon and other
administrative messages, and `wait_message()` for application messages.

QuickFIX stores session state in `FixPythocolSession/` and writes logs to
`FixPythocolLogs/` relative to the working directory. Pass settings such as
`FileStorePath`, `FileLogPath`, or `HeartBtInt` as additional constructor
arguments when needed.

## Tests

The pytest suite starts a real local FIX 4.4 acceptor and initiator. It covers
logon, order delivery, rule-based and default responses, and timeout behavior:

```bash
python -m pytest tests
```
