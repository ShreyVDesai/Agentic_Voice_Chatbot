# Voice Agentic Chatbot

## 🧠 Overview

The **Voice Agentic Chatbot** is a Python-based, voice-enabled assistant built using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/voice/quickstart/). It routes user queries to specialized agents for **loans**, **investments**, or **general banking**, and connects users to a human agent if needed.

## ✨ Features

- **Loan Agent**  
  - Check loan eligibility  
  - View loan status  
  - Connect to a human

- **Investment Agent**  
  - Get investment portfolio valuation  
  - View profit/loss summary  
  - Connect to a human

- **Generic Banking Agent**  
  - Handle general banking inquiries  
  - Connect to a human

- **Fallback Agent**  
  - Handles out-of-domain questions

- **Guardrails & Routing**  
  - Uses input guardrails to verify banking-related queries  
  - Routes user input to the correct agent

## 🛠️ Prerequisites

- Python 3.12 or higher
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- Packages listed in `requirements.txt`

## 🚀 Installation

```bash
git clone https://github.com/yourusername/voice-agentic-chatbot.git
cd voice-agentic-chatbot
pip install -r requirements.txt
