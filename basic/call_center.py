#!/usr/bin/env python3

from collections import deque

# id, state and call
operators = {
    "A": {"state": "available", "call": None},
    "B": {"state": "available", "call": None},
}

# id, state and op_id
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


def receive_call(call_id):
    # receive new call and try to deliver to an operator
    if call_id in calls:
        print(f"Error: Call {call_id} already exists")
        return

    calls[call_id] = {"state": "waiting", "operator": None}
    print(f"Call {call_id} received")

    op_id = find_available_operator()
    if op_id:
        deliver_call(call_id, op_id)
    else:
        queue.append(call_id)
        print(f"Call {call_id} waiting in queue")


def answer_call(op_id):
    
    if op_id not in operators:
        print(f"Error: Operator {op_id} not found")
        return
    if operators[op_id]["state"] != "ringing":
        print(f"Error: Operator {op_id} is not ringing")
        return

    call_id = operators[op_id]["call"]
    operators[op_id]["state"] = "busy"
    calls[call_id]["state"] = "answered"
    print(f"Call {call_id} answered by operator {op_id}")


def reject_call(op_id):
    # operator reject the call. it goes to the next available operetor
    if op_id not in operators:
        print(f"Error: Operator {op_id} not found")
        return
    if operators[op_id]["state"] != "ringing":
        print(f"Error: Operator {op_id} is not ringing")
        return

    call_id = operators[op_id]["call"]

    # Libera o operador
    operators[op_id]["state"] = "available"
    operators[op_id]["call"] = None
    calls[call_id]["state"] = "waiting"
    calls[call_id]["operator"] = None
    print(f"Call {call_id} rejected by operator {op_id}")

    # Tenta entregar para outro (pulando quem rejeitou)
    next_op = find_available_operator(exclude=op_id)
    if next_op:
        deliver_call(call_id, next_op)
    else:
        queue.appendleft(call_id)
        print(f"Call {call_id} waiting in queue")


def hangup_call(call_id):
    # end a call. if answered: finished. if not answered: missed
    if call_id not in calls:
        print(f"Error: Call {call_id} not found")
        return

    call = calls[call_id]

    if call["state"] == "answered":
        op_id = call["operator"]
        operators[op_id]["state"] = "available"
        operators[op_id]["call"] = None
        del calls[call_id]
        print(f"Call {call_id} finished and operator {op_id} available")
        try_deliver_from_queue()

    elif call["state"] == "ringing":
        op_id = call["operator"]
        operators[op_id]["state"] = "available"
        operators[op_id]["call"] = None
        del calls[call_id]
        print(f"Call {call_id} missed")
        try_deliver_from_queue()

    elif call["state"] == "waiting":
        queue.remove(call_id)
        del calls[call_id]
        print(f"Call {call_id} missed")
