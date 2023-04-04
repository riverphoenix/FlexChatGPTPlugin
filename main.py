import json
import os, sys
from twilio.rest import Client
import sqlite3
import hashlib
import time

import quart
import quart_cors
from quart import request

# required for all twilio access tokens
# To set up environmental variables, see http://twil.io/secure
account_sid = 'ACxxxxxxxxxxxxxxxxxxxx'
auth_token = 'xxxxxxxxxxxxxxxxxxxx'
conv_flow ='FWxxxxxxxxxxxxxxxxxxxx'
hostname = 'https://example.domain.com/'

# Note: Setting CORS to allow chat.openapi.com is required for ChatGPT to access your plugin
app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

def create_conv(client,identity):
    conversation = client.conversations \
                         .v1 \
                         .conversations \
                         .create(friendly_name='chatgpt_hash')

    participant = client.conversations \
                        .v1 \
                        .conversations(conversation.sid) \
                        .participants \
                        .create(identity=identity)

    webhook = client.conversations \
        .v1 \
        .conversations(conversation.sid) \
        .webhooks \
        .create(
             configuration_filters='onMessageAdded',
             target='studio',
             configuration_flow_sid=conv_flow,
         )
    return conversation.sid

def check_state(client,sid):
    conversation = client.conversations \
                     .v1 \
                     .conversations(sid) \
                     .fetch()
    return conversation.state

def get_resp(client,sid,m_sid):
    replies = []
    while (len(replies)<1):
        messages = client.conversations \
                     .v1 \
                     .conversations(sid) \
                     .messages \
                     .list(order='desc', limit=10)

        for msg in messages:
            if (msg.sid == m_sid):
                break
            else:
                replies.append(msg.body)
        if (len(replies)>0):
            break
        else:
            if (check_state(client,sid) == 'closed'):
                break
            else:
                time.sleep(15)
    return list(reversed(replies))

def send_msg(user_id,msg):
    identity = str(hashlib.md5(user_id.encode()).hexdigest())

    conn = sqlite3.connect('convs.db')
    c = conn.cursor()

    client = Client(account_sid, auth_token)
    sid = ''

    c.execute("SELECT * FROM convs WHERE user = '" + identity +"'")
    res = c.fetchall()
    if len(res) == 0:
        sid = create_conv(client,user_id)
        c.execute("INSERT INTO convs (user,conv) VALUES ('" + identity + "', '" + str(sid) + "')")
        conn.commit()
    else:
        sid = res[0][1]
        if (check_state(client,sid) == 'closed'):
            sid = create_conv(client,user_id)
            c.execute("UPDATE convs SET conv ='"+str(sid)+"' WHERE user = '"+identity+"'")
            conn.commit()
    conn.close()

    message = client.conversations \
                .v1 \
                .conversations(sid) \
                .messages \
                .create(author=user_id, body=msg,x_twilio_webhook_enabled='true')

    return get_resp(client,sid,message.sid)

@app.post("/send/<string:username>")
async def send_Msg(username):
    request = await quart.request.get_json(force=True)
    ret = send_msg(username,request["msg"])
    return quart.Response(response=json.dumps(ret), status=200)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')


@app.get("/legal")
async def plugin_legal():
    filename = 'legal.txt'
    return await quart.send_file(filename, mimetype="text/json")


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    filename = 'ai-plugin.json'
    return await quart.send_file(filename, mimetype="text/json")

@app.get("/openapi.yaml")
@app.get("/")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", hostname)
        return quart.Response(text, mimetype="text/yaml")


def main():
    app.run(debug=True, host="localhost", port=5002)


if __name__ == "__main__":
    main()