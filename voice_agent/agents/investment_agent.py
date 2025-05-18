# # agents/investment_agent.py

# from agents import Agent, function_tool

# @function_tool
# def get_portfolio_summary(user_id: str) -> str:
#     """
#     Provides a summary of the user's investment portfolio.
#     """
#     return f"Your portfolio includes $10,000 in mutual funds, $5,000 in stocks, and $2,000 in crypto."

# @function_tool
# def get_market_update() -> str:
#     """
#     Offers the latest market updates.
#     """
#     return "Markets are stable today. S&P is up 0.5%, NASDAQ up 0.2%."

# @function_tool
# def book_advisor_appointment(date: str) -> str:
#     """
#     Schedules an appointment with a financial advisor on the specified date.
#     """
#     return f"Appointment with a financial advisor has been booked for {date}."

# investment_agent = Agent(
#     name="Investment Agent",
#     instructions="Handles portfolio summaries, market updates, and advisor appointments.",
#     tools=[get_portfolio_summary, get_market_update, book_advisor_appointment]
# )

# agents/investment_agent.py



@function_tool
def get_portfolio_summary(user_id: str) -> str:
    return ("Your portfolio: $10,000 in mutual funds, $5,000 in stocks, "
            "and $2,000 in crypto.")

@function_tool
def get_market_update() -> str:
    return "Markets are stable today. S&P is up 0.5%, NASDAQ up 0.2%."

@function_tool
def book_advisor_appointment(date: str) -> str:
    return f"Appointment with a financial advisor has been booked for {date}."

def get_investment_agent():
    from agents import Agent, function_tool  # 👈 moved here to avoid circular import

    # Create and return a  Agent
    return Agent(
    name="Investment Agent",
    instructions="You are an investment advisor. Use your tools to answer investment queries.",
    tools=[get_portfolio_summary, get_market_update, book_advisor_appointment]
)
