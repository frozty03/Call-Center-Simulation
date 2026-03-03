#!/usr/bin/env python3

import json
from twisted.internet import reactor, protocol
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


def find_available_operator():
    # return first availavle operator or None
    for op_id, op in operators.items():
        if op["state"] == "available":
            return op_id
    return None


# sending msgs instead of printing
def deliver_call(call_id, op_id, msgs):
    # deliver a call to an operator, both in ringing state
    # sending msg to client.py
    calls[call_id]["state"] = "ringing"
    calls[call_id]["operator"] = op_id
    operators[op_id]["state"] = "ringing"
    operators[op_id]["call"] = call_id
    msgs.append(f"Call {call_id} ringing for operator {op_id}")


def verify_queue(msgs):
    # deliver a call from queue if there is an operator available
    if queue:
        op_id = find_available_operator()
        if op_id:
            call_id = queue.popleft()
            if call_id in calls:
                deliver_call(call_id, op_id, msgs)


def receive_call(call_id):
    # receive new call and try to deliver to an operator
    msgs = []
    if call_id in calls:
        # returning because im not printing anymore, but sending it to the client
        return [f"Error: Call {call_id} already exists"]

    calls[call_id] = {"state": "waiting", "operator": None}
    msgs.append(f"Call {call_id} received")

    op_id = find_available_operator()
    if op_id:
        deliver_call(call_id, op_id, msgs)
    else:
        queue.append(call_id)
        msgs.append(f"Call {call_id} waiting in queue")
    return msgs


def answer_call(op_id):
    
    if op_id not in operators:
        return [f"Error: Operator {op_id} not found"]
        
    if operators[op_id]["state"] != "ringing":
        return [f"Error: Operator {op_id} is not ringing"]
        

    call_id = operators[op_id]["call"]
    operators[op_id]["state"] = "busy"
    calls[call_id]["state"] = "answered"
    return [f"Call {call_id} answered by operator {op_id}"]


def reject_call(op_id):
    # operator reject the call. it goes to the next available operetor
    msgs = []
    if op_id not in operators:
        return [f"Error: Operator {op_id} not found"]
        
    if operators[op_id]["state"] != "ringing":
        return [f"Error: Operator {op_id} is not ringing"]
        

    call_id = operators[op_id]["call"]

    operators[op_id]["state"] = "available"
    operators[op_id]["call"] = None
    calls[call_id]["state"] = "waiting"
    calls[call_id]["operator"] = None
    msgs.append(f"Call {call_id} rejected by operator {op_id}")

    # try to deliver again
    next_op = find_available_operator()
    if next_op:
        deliver_call(call_id, next_op, msgs)
    else:
        queue.appendleft(call_id)
        msgs.append(f"Call {call_id} waiting in queue")
    return msgs


def hangup_call(call_id):
    # end a call. if answered: finished. if not answered: missed
    msgs = []
    if call_id not in calls:
        return [f"Error: Call {call_id} not found"]
        

    call = calls[call_id]

    if call["state"] == "answered":
        op_id = call["operator"]
        operators[op_id]["state"] = "available"
        operators[op_id]["call"] = None
        del calls[call_id]
        msgs.append(f"Call {call_id} finished and operator {op_id} available")
        verify_queue(msgs)

    elif call["state"] == "ringing":
        op_id = call["operator"]
        operators[op_id]["state"] = "available"
        operators[op_id]["call"] = None
        del calls[call_id]
        msgs.append(f"Call {call_id} missed")
        verify_queue(msgs)

    elif call["state"] == "waiting":
        queue.remove(call_id)
        del calls[call_id]
        msgs.append(f"Call {call_id} missed")
    
    return msgs


class CallCenterProtocol(protocol.Protocol):
    # every customer "is" a instance of this class
    # twisted calls dataReceived() instantly when it has data

    def dataReceived(self, data):
        #transform into string
        text = data.decode("utf-8").strip()

        # separate if it comes in more than one line
        for line in text.split("\n"):
            if not line.strip():
                continue

            # convert json in python dict
            # json struscture: {"command": "<commadnd>", "id": "<id>"}
            command_data = json.loads(line)

            # to discover which command is going to be used
            command = command_data["command"]
            id_value = command_data["id"]

            if command == "call":
                msgs = receive_call(id_value)
            elif command == "answer":
                msgs = answer_call(id_value)
            elif command == "reject":
                msgs = reject_call(id_value)
            elif command == "hangup":
                msgs = hangup_call(id_value)

            # sending the each message back as json
            for msg in msgs:
                response = json.dumps({"response": msg}) + "\n"
                self.transport.write(response.encode("utf-8"))

class CallCenterFactory(protocol.Factory):
    # building a CallCenterProtocol to every client connected

    def buildProtocol(self, addr):
        return CallCenterProtocol()

# to keep the common architecture of python programs
if __name__ == "__main__":
    print("Server running on port 5678...")
    reactor.listenTCP(5678, CallCenterFactory())
    reactor.run()