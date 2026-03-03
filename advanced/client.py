#!/usr/bin/env python3

import cmd
import json
import threading
from twisted.internet import reactor, protocol

# connection reference
connection = None

# save responses and event to sinalize them
responses = []
response_event = threading.Event()

class ClientProtocol(protocol.Protocol):

    def connectionMade(self):
        # when connects, save reference to send data after
        global connection
        connection = self

    # save partial data
    def __init__(self):
        self.buffer = ""  

    def dataReceived(self, data):
        # receive json from server and saves it
        
        # accumulate in buffer
        self.buffer += data.decode("utf-8")

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            msg = json.loads(line).get("response", "")
            responses.append(msg)

        # tells cmd thread the response arrived
        response_event.set()

    def connectionLost(self, reason):
        reactor.callFromThread(reactor.stop)


class ClientFactory(protocol.ClientFactory):

    def buildProtocol(self, addr):
        return ClientProtocol()

    def clientConnectionFailed(self, connector, reason):
        print("Error: Could not connect to server")
        reactor.stop()

def send_and_wait(command, id_value):
    if connection is None:
        print("Error: Not connected")
        return

    # set json as requested
    command_json = json.dumps({"command": command, "id": id_value})

    # clean previosu answers
    responses.clear()
    response_event.clear()

    # send to server (callFromThread = thread-safe)
    reactor.callFromThread(connection.transport.write,
                        (command_json + "\n").encode("utf-8"))

    # wait for it to arrive
    response_event.wait(timeout=5.0)

    for msg in responses:
        print(msg)


class CallCenterCmd(cmd.Cmd):
    prompt = "call center > "
    intro = (
        "=== Call Center Client ===\n"
        "Commands: call <id>, answer <id>, reject <id>, hangup <id>\n"
        "Type 'quit' to exit.\n"
    )

    def do_call(self, arg):
        if arg.strip():
            send_and_wait("call", arg.strip())

    def do_answer(self, arg):
        if arg.strip():
            send_and_wait("answer", arg.strip())

    def do_reject(self, arg):
        if arg.strip():
            send_and_wait("reject", arg.strip())

    def do_hangup(self, arg):
        if arg.strip():
            send_and_wait("hangup", arg.strip())

    def do_quit(self, arg):
        reactor.callFromThread(reactor.stop)
        return True

    def emptyline(self):
        pass


if __name__ == "__main__":
    reactor.connectTCP("localhost", 5678, ClientFactory())
    reactor.callInThread(CallCenterCmd().cmdloop)
    reactor.run()