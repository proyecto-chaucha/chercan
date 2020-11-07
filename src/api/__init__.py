import persistqueue
import logging

from sanic import Sanic
from sanic.response import json, text
from sanic.log import logger
from chaucha import opreturn
from os import getenv
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

queue = persistqueue.UniqueAckQ("txs")
app = Sanic(name="cl.chaucha.tx")

# Notarize Log
logpath = "notary.txt"
notary = logging.getLogger('notary')
notary.setLevel(logging.INFO)

ch = logging.FileHandler(logpath)
ch.setFormatter(logging.Formatter('%(message)s'))

notary.addHandler(ch)

# Save history of previous tx
logpath2 = "history.txt"
history = logging.getLogger('history')
history.setLevel(logging.INFO)

ch2 = logging.FileHandler(logpath2)
ch2.setFormatter(logging.Formatter('%(message)s'))

history.addHandler(ch2)


def send_opreturn(message):
    logger.info("OP_RETURN initiated")

    privkey = getenv("INPUT_PRIVKEY")
    if not privkey:
        raise Exception("Private Key not found")

    pubkey = getenv("INPUT_PUBKEY")

    if not pubkey:
        raise Exception("Public Key not found")

    sendkey = getenv("INPUT_SENDKEY")

    if not sendkey:
        raise Exception("Send Key not found")

    message = message or getenv("INPUT_MESSAGE")

    if not message:
        raise Exception("Message not found")

    logger.debug("Sending the OP_RETURN")
    response = opreturn.send(privkey, pubkey, sendkey, message)

    if not response:
        raise Exception("Could not send OP_RETURN")

    logger.debug(response)
    return response

@app.route("/", methods=["POST","GET",])
async def handle_index(request):
    success = False
    message = None

    last_count = queue.size

    try:
        if 'message' in request.args:
            message = request.args['message'][0]
            success = message is not None

        if not success:
            message = request.json['message']
            success = message is not None
        
        queue.put(message)

    except Exception as e:
        logger.error(e)
        pass

    if last_count == queue.size or not success:
        response = "nothing was added."
        success = False
    else:
        success = False
        if message:
            response = f"added message '{message}' to queue"
            now = datetime.now().strftime('%Y/%m/%d')
            history.info(f"{now} | {message}")
            success = True

    return json({"success":success, "message": message, "response": response, "queue":queue.size})

@app.route("/notary", methods=["GET"])
async def handle_notary(request):
    with open("notary.txt", "r") as f:
        return text(f.read())

@app.route("/history", methods=["GET"])
async def handle_notary(request):
    with open("history.txt", "r") as f:
        return text(f.read())

@app.route("/cron", methods=["GET",])
async def handle_cron(request):
    
    logger.info("Cron triggered")

    if queue.size <= 0:
        logger.info("No Items in Queue")
        return json({"success":False, "item":None})
    
    item = queue.get()
    ack = False

    logger.info("Processing item: " + item)
    
    try:
        response = send_opreturn(item)
        logger.info("Acknowledge item: " + item)
        queue.ack(item)
        
        # TODO: Check this use case
        # If the tx is not confirmed in a long time it could be wiped out
        # its best to check the confirmations before truly considering
        # the tx as success
        notary.info(f"item: {item} | certification: {response}")
        ack = True
    
    except Exception as e:
        logger.error(e)
        logger.info("Item: " + item + " not acknowledged.")
        queue.nack(item)
    
    return json({"success":ack, "item":item, "queue":queue.size})


if __name__ == "__main__":
    app.run(debug=True, access_log=True, host="0.0.0.0", port=8000)