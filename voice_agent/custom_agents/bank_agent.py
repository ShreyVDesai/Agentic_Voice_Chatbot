


# async def run_workflow(user_question):
#     from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner, function_tool
#     from pydantic import BaseModel
#     import asyncio

#     load_dotenv()
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#     # Tools

#     # All function tools are only meant to simulate API calls, not acutally return answers

#     # Loan Tools

#     @function_tool
#     def check_loan_eligibility():
#         return "Based on the information we have on you, you are eligible to be sanctioned for a 45000 dollar loan."

#     @function_tool
#     def check_loan_status():
#         return "Your loan of 2000 dollars is being processed, please log on to your web-banking page or mobile app to view estimated time of completion."

#     @function_tool
#     def connect_to_human():
#         return "You are now being connected to a human. This is the last step of the agentic workflow, please hang up"

#     @function_tool
#     def check_investment_valuation():
#         return "As of today, your investment portfolio is valued at 2589053 dollars."

#     @function_tool
#     def check_profit_and_loss():
#         return "As of today, your year to date profit is 25134 dollars."



#     class BankOutput(BaseModel):
#         is_bank_question: bool
#         reasoning: str

#     guardrail_agent = Agent(
#         name="Guardrail check",
#         instructions="You are a helpful banking assistant. Check if the user is asking about loans, investments or general banking question that is usually asked to a bank's customer care agent.",
#         output_type=BankOutput,
#         model = 'gpt-4-turbo',
#     )

#     loan_agent = Agent(
#         name="Loan Agent",
#         handoff_description="Specialist agent for loan-related questions",
#         instructions="You provide help with loan-related customer questions. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal.",
#         model = 'gpt-4-turbo',
#         tools = [check_loan_eligibility, check_loan_status, connect_to_human]
#     )

#     investment_agent = Agent(
#         name="Investment Agent",
#         handoff_description="Specialist agent for investment-related questions for the investment portfolio that a customer has with a bank",
#         instructions="You provide help with investment-related customer questions for the investment portfolio that a customer has with a bank. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal.",
#         model = 'gpt-4-turbo',
#         tools = [check_investment_valuation, check_profit_and_loss, connect_to_human]
#     )

#     generic_banking_agent = Agent(
#         name="Generic Banking Agent",
#         handoff_description="Generic banking agent for banking related questions",
#         instructions="You provide help with general banking customer questions a customer can have with a bank agent. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal.",
#         model = 'gpt-4-turbo',
#         tools = [connect_to_human]
#     )

#     fallback_agent = Agent(
#         name="Fallback Agent",
#         handoff_description="Fallback banking agent for when the customer's question is not banking-related",
#         instructions="If the customer's question is not banking related, politely tell them to only ask banking related question. If it is banking related, ask them to visit our website www.banksite.com",
#         model = 'gpt-4-turbo'
#     )


#     async def bank_guardrail(ctx, agent, input_data):
#         result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
#         final_output = result.final_output_as(BankOutput)
#         return GuardrailFunctionOutput(
#             output_info=final_output,
#             tripwire_triggered=not final_output.is_bank_question,
#         )

#     triage_agent = Agent(
#         name="Triage Agent",
#         instructions="You determine which agent to use based on the user's question. If you cannot find an appropriate agent to use, you should determine that you need to use the fallback agent.",
#         handoffs=[loan_agent, investment_agent, generic_banking_agent, fallback_agent],
#         input_guardrails=[
#             InputGuardrail(guardrail_function=bank_guardrail),
#         ],
#     )

#     result = await Runner.run(triage_agent, user_question)
#     return result.final_output

from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner, function_tool
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loading environment variables")
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger.info("Environment variables loaded")

# Tools

@function_tool
def check_loan_eligibility():
    logger.info("Tool executed: check_loan_eligibility")
    return "Based on the information we have on you, you are eligible to be sanctioned for a 45000 dollar loan."

@function_tool
def check_loan_status():
    logger.info("Tool executed: check_loan_status")
    return "Your loan of 2000 dollars is being processed, please log on to your web-banking page or mobile app to view estimated time of completion."

@function_tool
def connect_to_human():
    logger.info("Tool executed: connect_to_human")
    return "You are now being connected to a human. This is the last step of the agentic workflow, please hang up"

@function_tool
def check_investment_valuation():
    logger.info("Tool executed: check_investment_valuation")
    return "As of today, your investment portfolio is valued at 2589053 dollars."

@function_tool
def check_profit_and_loss():
    logger.info("Tool executed: check_profit_and_loss")
    return "As of today, your year to date profit is 25134 dollars."

@function_tool
def check_balance():
    logger.info("Tool executed: check_balance")
    return "As of today, your bank balance is 2514 dollars."

class BankOutput(BaseModel):
    is_bank_question: bool
    reasoning: str

logger.info("Initializing agents")

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="You are a helpful assistant. You should check if the user's prompt contains anything obscene or inappropriate",
    output_type=BankOutput,
    
)

loan_agent = Agent(
    name="Loan Agent",
    handoff_description="Specialist agent for loan-related questions",
    instructions="You provide help with loan-related customer questions. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal.",
    
    tools=[check_loan_eligibility, check_loan_status, connect_to_human]
)

investment_agent = Agent(
    name="Investment Agent",
    handoff_description="Specialist agent for investment-related questions for the investment portfolio that a customer has with a bank",
    instructions="You provide help with investment-related customer questions for the investment portfolio that a customer has with a bank. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal.",
    tools=[check_investment_valuation, check_profit_and_loss, connect_to_human],
)

generic_banking_agent = Agent(
    name="Generic Banking Agent",
    handoff_description="Generic banking agent for banking related questions",
    instructions="You provide help with general banking customer questions a customer can have with a bank agent. Politely respond to the customer's queries when you are confident you know the answer. If you don't know the answer politely tell the user that you will connect them with a human agent and then do so. You are allowed to use the tools you need at your disposal. In a new conversation when the user say hi, hello or something similar, respond with Hello! I'm here to assist with:Loan status & eligibility,Investment performance,General banking help. Just ask me a question to get started!",
    tools=[connect_to_human, check_balance],
)

fallback_agent = Agent(
    name="Fallback Agent",
    handoff_description="Fallback banking agent for when the customer's question is not banking-related",
    instructions="If the customer's question is not banking related, politely tell them to only ask banking related question. If it is banking related, ask them to visit our website www.banksite.com. In a new conversation when the user say hi, hello or something similar, respond with Hello! I'm here to assist with:Loan status & eligibility,Investment performance,General banking help. Just ask me a question to get started!",

)

logger.info("Agents initialized successfully")

async def bank_guardrail(ctx, agent, input_data):
    logger.info("Running bank guardrail check")
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    logger.info("Guardrail agent finished execution")
    final_output = result.final_output_as(BankOutput)
    logger.info(f"Guardrail result: {final_output}")
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_bank_question,
    )

triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's question. If you cannot find an appropriate agent to use, you should determine that you need to use the fallback agent.",
    handoffs=[loan_agent, investment_agent, generic_banking_agent, fallback_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=bank_guardrail),
    ],
)


async def run_workflow(user_question):
    logger.info(f"Starting workflow for user question: {user_question}")
    result = await Runner.run(triage_agent, user_question)
    logger.info("Triage agent completed")
    logger.info(f"Final result: {result}")
    return result
