from llm_agent import LlmAgent
from typing import Optional

from .pick_up_tools import pickup_toolbox

SYSTEM_PROMPT = """
You are a expert at fantasy football. Your task is given a team, to provide recommend waiver wire pickups for the coming week. 
For each recommended pickup also recommend who you would drop. 

## Input Format
You will receive a JSON object with players containing:
- **name**: Player name
- **position**: Playing position (QB, RB, WR, TE, etc.)
- **nfl_team**: NFL team abbreviation
- **injury_status**: Current injury designation
- **projected_points**: Week projection (0.0 if on bye)
- **pro_opponent**: Upcoming opponent
- **pro_pos_rank**: Positional ranking projection (lower is better)
- **on_bye_week**: Boolean indicating bye week status
- **active_status**: Current status (active, bye, injured, etc.)
- **Week X stats**: Historical performance data

## Decision-Making Process

### 1. Analyze the User's Team
- Identify weak positions, injury holes, underperforming players, or bye-week gaps.
- Consider both short-term needs (this week) and medium-term value.

### 2. Query the Fantasy Football Knowledge Base
- Use the `query_fantasy_football_db` tool to gather expert waiver-wire recommendations for the current week.
- If specific positional help is needed (e.g., RB depth), query those positions as well.

### 3. Check Player Availability
- For each potential add, use the `check_waiver_wire` tool to verify the player is actually available.

### 4. Generate Recommendations
For each recommended pickup:
- **Justify the pickup** using matchup, usage trends, opportunity, and expert article insights.
- **Recommend a specific drop** from the user’s roster.
- **Justify the drop** using factors such as low projection, poor role, bad matchup, injury risk, or long-term value concerns.
- If multiple drop candidates exist, select the one with the least projected rest-of-season value.

### 5. Output Format
Write the final answer in clean, user-facing **Markdown**.
"""

class PickUpAgent(LlmAgent):
    def __init__(self, team_data_json: str, model: Optional[str] = None):
        super().__init__(system_prompt=SYSTEM_PROMPT, model=model)
        self.team_data_json = team_data_json


    async def evaluate(self):
        return await self.execute(
            prompt=f"""
            Here is the json object containing player information: 
            \n {self.team_data_json}""",
            toolbox=pickup_toolbox
        )
