import sys
import os
import json
from chroma_db_setup import get_chroma_client, get_embedding_function
try:
    from tools import ToolBox
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from tools import ToolBox

from team_data import TeamData

pickup_toolbox = ToolBox()

@pickup_toolbox.tool
def query_fantasy_football_db(query: str, n_results: int = 3):
    """
    Query the fantasy football articles database using semantic search.

    Searches a ChromaDB collection of fantasy football articles and returns
    the most relevant documents based on the query text using embedding-based
    similarity search.

    Args:
        query (str): The search query text to find relevant articles
        n_results (int, optional): Maximum number of results to return.
            Defaults to 3.

    Returns:
        list[dict]: A list of matching documents, where each dict contains:
            - id (str): The unique document identifier
            - text (str): The full document text content
            - score (float): The distance score (lower is more similar)

    Example:
        > results = query_fantasy_football_db("Drake Maye performance", n_results=5)
        > print(results[0]['text'][:100])
    """
    client = get_chroma_client()
    collection = client.get_collection(
        name='fantasy_football_articles',
        embedding_function=get_embedding_function()
    )

    print(f"Querying fantasy football vector db: {query}, n_results: {n_results}")

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    return [
        {"id": doc_id, "text": doc_text, "score": score}
        for doc_id, doc_text, score in zip(
            results["ids"][0], results["documents"][0], results["distances"][0]
        )
    ]

## tool to see if a player is on the waiver wire or not
@pickup_toolbox.tool
def check_waiver_wire(player_name: str):
    """
    Check if a player is on the waiver wire.

    Note: For defenses, format name with "{Mascot} D/ST" (ex. "Broncos D/ST", "Texans D/ST")

    Args:
        player_name (str): The name of the player to check

    Returns:
        json: A json containing the player name, whether they were found, and whether they are on the waiver wire
    """
    team_data = TeamData()
    player = team_data.league.player_info(player_name)
    print("Checking waiver wire for player: ", player_name)
    if player is None:
        print("Player not found: ", player_name)
    return json.dumps({
        "player_name": player_name,
        "found": player is not None,
        "on_waiver_wire": player.onTeamId == 0 if player else None,
    })

@pickup_toolbox.tool
def get_player_stats(player_name: str):
    """
    Get player stats for a specific player.

    Note: For defenses, format name with "{Mascot} D/ST" (ex. "Broncos D/ST", "Texans D/ST")

    Args:
        player_name (str): The name of the player to get stats for

    Returns:
        json: A json containing the player name, position, average points for the season, and past weeks data
    """
    print("Getting player stats for player: ", player_name)
    team_data = TeamData()
    return json.dumps(team_data.get_player_info(player_name))
