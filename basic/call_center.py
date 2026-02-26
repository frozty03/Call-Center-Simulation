#!/usr/bin/env python3

from collections import deque

# id, state and call
operators = {
    "A": {"state": "available", "call": None},
    "B": {"state": "available", "call": None},
}

# state and op_id
calls = {}

# wait list
queue = deque()


def find_available_operator(exclude=None):
    # return first availavle operator or None
    for op_id, op in operators.items():
        if op["state"] == "available" and op_id != exclude:
            return op_id
    return None


def deliver_call(call_id, op_id):
    # deliver a call to an operator, both in ringing state
    calls[call_id]["state"] = "ringing"
    calls[call_id]["operator"] = op_id
    operators[op_id]["state"] = "ringing"
    operators[op_id]["call"] = call_id
    print(f"Call {call_id} ringing for operator {op_id}")


def try_deliver_from_queue():
    # deliver a call from queue if there is an operator available
    if queue:
        op_id = find_available_operator()
        if op_id:
            call_id = queue.popleft()
            if call_id in calls:
                deliver_call(call_id, op_id)

