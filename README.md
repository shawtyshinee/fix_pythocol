# FIX Pythocol

```bash
MADE WITH CODEX' HELP :)
```

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

## Building order messages

The builder contexts wrap and update a `Message`. State methods return the
context; call it to get the same message back. Supply the fields required by
your counterparty and FIX dictionary, including identifiers, side, quantities,
timestamps, and execution details as appropriate.

```python
from src import Message, OrderContext, ExecutionReportContext, build_default_fix_message

fields = build_default_fix_message("AAPL", quantity=2, lot_size=100, price=150.0)
order = OrderContext(fields).new({11: "order-1", 54: "1", 60: "20260101-12:00:00"})()
cancel = OrderContext(Message({41: "order-1", 11: "cancel-1", 55: "AAPL", 54: "1"})).cancel()()

report = ExecutionReportContext(Message({8: "FIX.4.4", 11: "order-1"}))
pending = report.pending_new()()
filled = report.fulfill({14: "200", 151: "0", 32: "200", 31: "150"})()
```

`OrderContext.new()` builds a NewOrderSingle request and `cancel()` builds an
OrderCancelRequest. `ExecutionReportContext` supports `new()`, `fulfill()`
(also spelled `fullfil()`), `partfill()`, `cancel()`, `reject()`,
`pending_new()`, `pending_cancel()`, and `pending_replace()`. These methods
set the message type and execution/order status fields; they do not fill in
all fields required for a complete FIX message. Both contexts mutate the
wrapped message, so create separate `Message` objects for independent reports.
Fill execution codes use FIX 4.4 conventions when tag 8 is absent, and use
the older fill codes for FIX 4.1 through 4.3. FIX 4.0 reports omit ExecType;
pending replace is unavailable in FIX 4.0 and 4.1.

You can provide your own implementation of either context. Subclass
`IOrderContext` for outgoing requests or `IExecutionReportContext` for
execution reports, and implement the corresponding methods for your
counterparty. Both base classes wrap a `Message`, expose it through `()`, and
provide `_update()` for applying field mappings and keyword arguments. For
example:

```python
from src import Message
from src.utils.builder.context.interface import IOrderContext

class CustomOrderContext(IOrderContext):
    def new(self, fields=None, **tags):
        self._update(fields, **tags)
        self.message.update({35: "D", 100: "MY_VENUE"})
        return self

    def cancel(self, fields=None, **tags):
        self._update(fields, **tags)
        self.message.update({35: "F", 100: "MY_VENUE"})
        return self

order = CustomOrderContext(Message({11: "order-1"})).new()()
```

For a custom execution-report context, implement its state methods in the same
way. If you use the `fullfil` or `partial_fill` aliases, define them in your
subclass as well.

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

To collect Allure results, run:

```bash
python -m pytest tests --alluredir=allure-results
```

Install the [Allure command-line tool](https://allurereport.org/docs/install/)
separately to view a report, then run `allure serve allure-results`. Results
are kept in the directory between runs; use a fresh directory for a new run.

The report includes text attachments for built messages, initiator sends,
acceptor and initiator receives, and configured default responses. Messages
are displayed as FIX `tag=value` lines; separately stored party groups are
included for constructed messages. Attachments contain message values,
including any credentials or trading data present, so protect the results and
reports accordingly. Allure steps and attachments are recorded when an Allure
listener is active, such as a pytest run with `--alluredir`.
