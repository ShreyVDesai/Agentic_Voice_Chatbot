from custom_agents.bank_agent import run_workflow

# Simply re-export so main.py can import
async def route_and_run(user_text: str):
    return await run_workflow(user_text)
