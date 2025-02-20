import requests
import openai
import json

def getData(payload):
  # openai.api_key = "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"
  openai.api_key = "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"
  URL = "https://api.openai.com/v1/chat/completions"

  data = payload

  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai.api_key}"
  }

  response = requests.post(URL, headers=headers, json=data)
  response = response.json()
  if "choices" in response:
    y = json.dumps({'status': True, 'message': response['choices'][0]['message']['content']})
    return y
  elif "error" in response:
    y = json.dumps({'status': False, 'message': response['error']['message']})
    return y