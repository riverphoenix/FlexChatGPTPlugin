# FlexChatGPTPlugin
ChatGPT Plugin for Twilio Flex

Sample code for Build a Twilio Flex ChatGPT Plugin blog post

## Insructions

Before you start, ensure that you configure your environment variables in the .env file:
- Account SID (get it from your Account dashboard)
- Auth Token (get it from your Account dashboard, as well)
- Conversation Flow SID (get it from your Conversation Flow SID [FWxxxxxxxxxxxxxxxx]; find the one you created in Studio by navigating to Studio > Flows in your Twilio Console)
- Hostname (ensure it is the same as in the 'ai-plugin.json' file)

You’ll need to also change the 'example.domain.com' url to the hostname you will proxy the running server behind in 'ai-plugin.json'

## Execute

pip install -r requirements.txt

python main.py &

ngrok http 5002
