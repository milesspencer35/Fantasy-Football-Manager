from llm_agent import LlmAgent
from typing import Optional
from team_data import TeamData

SYSTEM_PROMPT = """
You are a expert at fantasy football. You task is to take a fantasy football roster with stats and return what
the starting line up should be. 
"""

class PickUpAgent(LlmAgent):
    def __init__(self, model: Optional[str] = None):
        super().__init__(system_prompt=SYSTEM_PROMPT, model=model)
        self.team_data = TeamData()


    async def evaluate(self):
        return await self.execute(
            prompt=f"Here is the player on roster with information about each of them: \n {self.team_data.team_analyzer_json_data()}"
        )
