import allure

from ..interface import IExecutionReportContext
from src.allure_reporting import attach_message
from src.message import Message

__all__ = [
    "ExecutionReportContext"
]


class ExecutionReportContext(IExecutionReportContext):
    """Apply execution-report states to a message and return it with ``()``.

    State methods accept an optional mapping of tag IDs/names and keyword
    fields. They mutate the wrapped message and return this context. Tag 8
    selects the FIX version; an absent tag uses FIX 4.4 status conventions.
    Supply the remaining fields required by the counterparty.
    """

    def _state(self, status, fields=None, **tags) -> Message:
        states = {"0": "new", "1": "partially filled", "2": "filled", "4": "canceled",
                  "8": "rejected", "A": "pending new", "6": "pending cancel", "E": "pending replace"}
        with allure.step(f"Build {states[status]} execution report"):
            self._update(fields, **tags)
            version = self.message.get(8) or "FIX.4.4"
            if status == "E" and version in ("FIX.4.0", "FIX.4.1"):
                raise ValueError(f"Pending replace is not defined in {version}")
            exec_type = status
            if status in ("1", "2") and version not in ("FIX.4.0", "FIX.4.1", "FIX.4.2", "FIX.4.3"):
                exec_type = "F"
            state_fields = {35: "8", 39: status}
            if version == "FIX.4.0":
                if self.message.get(150) is not None:
                    self.message.pop(150)
            else:
                state_fields[150] = exec_type
            if version in ("FIX.4.0", "FIX.4.1", "FIX.4.2") and self.message.get(20) is None:
                state_fields[20] = "0"
            self.message.update(state_fields)
            attach_message(self.message, "Built execution report")
            return self

    def new(self, fields=None, **tags) -> Message:
        """Set the report state to new."""
        return self._state("0", fields, **tags)

    def fulfill(self, fields=None, **tags) -> Message:
        """Set the report state to filled; ``fullfil`` is an alias."""
        return self._state("2", fields, **tags)

    fullfil = fulfill

    def partfill(self, fields=None, **tags) -> Message:
        """Set the report state to partially filled; ``partial_fill`` is an alias."""
        return self._state("1", fields, **tags)

    partial_fill = partfill

    def cancel(self, fields=None, **tags) -> Message:
        """Set the report state to canceled."""
        return self._state("4", fields, **tags)

    def reject(self, fields=None, **tags) -> Message:
        """Set the report state to rejected."""
        return self._state("8", fields, **tags)

    def pending_new(self, fields=None, **tags) -> Message:
        """Set the report state to pending new."""
        return self._state("A", fields, **tags)

    def pending_cancel(self, fields=None, **tags) -> Message:
        """Set the report state to pending cancel."""
        return self._state("6", fields, **tags)

    def pending_replace(self, fields=None, **tags) -> Message:
        """Set pending replace; raise ValueError for FIX 4.0 or FIX 4.1."""
        return self._state("E", fields, **tags)
