# workflows/combined.py

from openai_agents import run_workflow
from workflows.router import router_workflow
from agents.loan_agent import loan_agent
from agents.banking_agent import banking_agent
from agents.investment_agent import investment_agent
from workflows.base_workflow import fallback_workflow

# Map category → Agent
AGENT_MAP = {
    "loan": loan_agent,
    "banking": banking_agent,
    "investment": investment_agent
}

async def route_and_run(input_text: str):
    # 1) Route
    router_out = await run_workflow(router_workflow, input={"input": input_text})
    category = router_out.output["category"]
    agent = AGENT_MAP.get(category, None)

    # 2) Execute agent or fallback
    if agent:
        # Agent.invoke returns an object with `.output`
        result = await agent.invoke(input={"input": input_text})
        return result
    else:
        return await run_workflow(fallback_workflow, input={"input": input_text})
