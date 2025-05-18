# bank_agent.py

from openai.agents import Workflow, tools, AgentStep, ToolCall
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)

client = OpenAI()

# Tool 1: Account balance retrieval
@tools.register
def get_account_balance(account_id: str) -> str:
    # Simulate a DB/API call
    return f"The balance for the account linked with phone number {account_id} is $3,482.12"

# Tool 2: Card blocking
@tools.register
def block_card(account_id: str) -> str:
    return f"The card with card number 12345678 linked linked with phone number {account_id} has been blocked."

# Define workflow step
class BankSupportStep(AgentStep):
    def run(self, state, tools, memory, config):
        prompt = f"""
        You are a helpful banking assistant. The customer said: "{state['input']}".
        
        1. If they mention 'balance', call get_account_balance(account_id="1234").
        2. If they mention 'lost card', call block_card(account_id="1234").
        3. Respond in a friendly tone.

        Output only the assistant's response or tool results.
        """
        result = tools.llm(prompt=prompt, temperature=0.4)
        return result.text

# Assemble workflow
voice_workflow = Workflow(
    name="bank_customer_support",
    steps=[BankSupportStep()],
)
