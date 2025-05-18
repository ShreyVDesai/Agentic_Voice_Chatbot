# workflows/base_workflow.py

from agents import Workflow, Step

class ResponseStep(Step):
    def run(self, context, tools, memory, config):
        prompt = (
            f"You are a helpful bank assistant. The user said: \"{context['input']}\".\n"
            "Use your tools when appropriate, and respond clearly and politely."
        )
        return tools.llm(prompt=prompt, temperature=0.4).text

generic_workflow = Workflow(
    name="generic",
    steps=[ResponseStep()]
)
