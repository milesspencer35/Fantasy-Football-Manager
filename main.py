# from openai import OpenAI
# from team_data import TeamData
#
# client = OpenAI()
# team_data = TeamData()
#
# response = client.responses.create(
#     model='gpt-5',
#     input='''
#     You are a expert at fantasy football. You task is to take a fantasy football roster with stats and return what
#     the starting line up should be. Here is the player on roster with information about each of them: \n
#     ''' + team_data.team_analyzer_json_data()
# )
#
# print(response.output_text)
# print(response.usage)

import asyncio
from lineup_agent.lineup_agent import LineupAgent

async def main():


    lineup_agent = LineupAgent(model="gpt-5")
    output = await lineup_agent.evaluate()
    print(output)



if __name__ == "__main__":
    asyncio.run(main())


