# # agents/banking_agent.py

# # agents/banking_agent.py

# from agents import Agent, function_tool

# @function_tool
# def get_balance(account_id: str) -> str:
#     """
#     Retrieves the balance for a given account.
#     """
#     return f"The balance for account {account_id} is $3,482.12"

# @function_tool
# def block_card(account_id: str) -> str:
#     """
#     Blocks the card associated with the specified account.
#     """
#     return f"The card linked to account {account_id} has been blocked."

# @function_tool
# def get_branch_hours(branch_name: str) -> str:
#     """
#     Provides the operating hours of a specified bank branch.
#     """
#     return f"{branch_name} branch is open from 9 AM to 5 PM, Monday to Friday."

# banking_agent = Agent(
#     name="Banking Agent",
#     instructions="Handles account balance inquiries, card issues, and branch information.",
#     tools=[get_balance, block_card, get_branch_hours]
# )


# agents/banking_agent.py


@function_tool
def get_balance(account_id: str) -> str:
    return f"The balance for account {account_id} is $3,482.12."

@function_tool
def block_card(account_id: str) -> str:
    return f"The card linked to account {account_id} has been blocked."

@function_tool
def get_branch_hours(branch_name: str) -> str:
    return f"{branch_name} branch is open from 9 AM to 5 PM, Monday to Friday."

def get_banking_agent():
    from agents import Agent, function_tool  # 👈 moved here to avoid circular import

    # Create and return a  Agent
    return Agent(
    name="Banking Agent",
    instructions="You are a bank assistant. Use your tools to answer general banking queries.",
    tools=[get_balance, block_card, get_branch_hours]
)
