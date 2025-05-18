# workflows/combined.py

from agents import Runner
from workflows.router import router_workflow
from workflows.base_workflow import generic_workflow
from agents.loan_agent import loan_agent
from agents.banking_agent import banking_agent
from agents.investment_agent import investment_agent

# Map category to the appropriate agent’s workflow
WORKFLOW_MAP = {
    "loan":      loan_agent,
    "banking":   banking_agent,
    "investment":investment_agent
}

async def route_and_run(user_text: str):
    # Step 1: Classify
    router_result = Runner.run_sync(router_workflow, {"input": user_text})
    category = router_result["category"]
    # Fallback
    agent = WORKFLOW_MAP.get(category, banking_agent)
    # Step 2: Run the domain agent
    agent_result = Runner.run_sync(agent, user_text)
    return agent_result  # has `.final_output`
