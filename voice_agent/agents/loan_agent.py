# # agents/loan_agent.py

# from agents import Agent, function_tool

# @function_tool
# def check_loan_eligibility(user_income: int, credit_score: int) -> str:
#     """
#     Determines loan eligibility based on income and credit score.
#     """
#     if user_income > 40000 and credit_score > 650:
#         return "You are eligible for a personal loan up to $50,000."
#     return "Unfortunately, you're not eligible for a loan right now."

# @function_tool
# def loan_status(loan_id: str) -> str:
#     """
#     Provides the current status of a loan application.
#     """
#     return f"Loan ID {loan_id} is currently under review. You will be notified shortly."

# @function_tool
# def apply_for_loan(amount: float, duration: int) -> str:
#     """
#     Initiates a loan application for a specified amount and duration.
#     """
#     return f"Loan application for ${amount} over {duration} months has been received."

# loan_agent = Agent(
#     name="Loan Agent",
#     instructions="Handles loan eligibility, application, and status inquiries.",
#     tools=[check_loan_eligibility, loan_status, apply_for_loan]
# )

# agents/loan_agent.py



@function_tool
def check_loan_eligibility(user_income: int, credit_score: int) -> str:
    if user_income > 40000 and credit_score > 650:
        return "You are eligible for a personal loan up to $50,000."
    return "Unfortunately, you're not eligible for a loan right now."

@function_tool
def loan_status(loan_id: str) -> str:
    return f"Loan ID {loan_id} is currently under review. You will be notified shortly."

@function_tool
def apply_for_loan(amount: float, duration: int) -> str:
    return f"Loan application for ${amount:.2f} over {duration} months has been received."

def get_loan_agent():
    from agents import Agent, function_tool  # 👈 moved here to avoid circular import

    # Create and return a Loan Agent
    return Agent(
    name="Loan Agent",
    instructions="You are a bank’s loan assistant. Use your tools to answer loan queries.",
    tools=[check_loan_eligibility, loan_status, apply_for_loan]
    ) 
