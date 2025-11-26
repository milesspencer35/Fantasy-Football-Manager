
import asyncio
from team_data import TeamData
from lineup_agent.lineup_agent import LineupAgent
from pick_up_agent.pick_up_agent import PickUpAgent
from pick_up_agent.pick_up_tools import check_waiver_wire
import json

async def main():
    team_data = TeamData()
    team_data_json = team_data.team_analyzer_json_data()

    print ("********************** LINEUP AGENT **********************")
    lineup_agent = LineupAgent(team_data_json=team_data_json, model="gpt-5-mini")
    output = await lineup_agent.evaluate()
    print(output)

    print ("********************** PICK UP AGENT **********************")
    pick_up_agent = PickUpAgent(team_data_json=team_data_json, model="gpt-5-mini")
    output = await pick_up_agent.evaluate()
    print(output)


if __name__ == "__main__":
    asyncio.run(main())


