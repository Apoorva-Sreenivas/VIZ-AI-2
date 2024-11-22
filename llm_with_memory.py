import requests
import json 

url = "http://localhost:11434/api/chat"

# Initialize chat history
chat_history = []

def llama3_mem(prompt):
    # Append user message to chat history
    chat_history.append({"role": "user", "content": prompt})

    data = {
        "model": "llama3",
        "messages": chat_history,  # Send the entire chat history
        "stream": False,
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=data)
    
    # Extract the response message and append it to chat history
    assistant_message = response.json()["message"]["content"]
    chat_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message