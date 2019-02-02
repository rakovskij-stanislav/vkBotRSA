from vkBotRSA import *
import example_config

token = example_config.token
gID = example_config.gID

server = vkRSA(token, gID)

@server.message_event()
def ans(body):
    print(body)
    return "vkBotRSA by reganel"

@server.message_event(texts=["привет", "хой"])
def ans(body):
    return "О, и тебе привет"

server.run()
