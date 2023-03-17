from awpy import DemoParser
from awpy.analytics.stats import player_stats
import json
import numpy as np

from flask import Flask

app = Flask(__name__)


@app.route('/match', methods=['GET'])
def get_match():
    # Your code to handle the GET request goes here
    # You can replace the following line with your own implementation
    def mapPlayers(player):
        # return player
        mainData = {
            **player, 
            "kills": sumArray([mapRound(round, player["steamID"], "attackerSteamID") for round in data["gameRounds"]]),
            "deaths": sumArray([mapRound(round, player["steamID"], "victimSteamID") for round in data["gameRounds"]]),
            "assists": sumArray([mapRound(round, player["steamID"], "assisterSteamID") for round in data["gameRounds"]]),
            }
        return {
            **mainData,
            "difference": mainData["kills"] - mainData["deaths"],
            "K/D": mainData["kills"] / mainData["deaths"],
        }

    def mapRound(round, steamId, keyType):
        return len([kill for kill in round["kills"] if kill[keyType] == steamId])

    def sumArray(arr):
        sum = 0
        for i in arr:
            sum = sum + i
        return sum
    
    parser = DemoParser("match.dem")
    parser.parse()
    data = parser.clean_rounds()

    match = {
        "teams": {
            "A": {
                "players": list(map(mapPlayers, data["gameRounds"][0]["ctSide"]["players"])),
                "teamStarted": "CT",
            },
            "B": {
                "players": list(map(mapPlayers, data["gameRounds"][0]["tSide"]["players"])),
                "teamStarted": "T",
            }
        }
    }

    return match


if __name__ == '__main__':
    app.run(debug=True)

# def filterKDAPlayer():
#     return


# def mapKDA(player):
#     # return player
#     return {**player, "kills": len([d for d in match_deaths if d['attacker_steamid'] == player["steamid"]]), "deaths": len([d for d in match_deaths if d["player_steamid"] == player["steamid"]])}


# def mapCT(player):
#     if ("CT" == player["starting_side"]):
#         return True
#     else:
#         return False


# def mapT(player):
#     if ("T" == player["starting_side"]):
#         return True
#     else:
#         return False


# total_deaths = parser.parse_events("player_death", props=["X", "Y", "health"])
# match_deaths = total_deaths[total_deaths.index(
#     next(death for death in total_deaths if death['weapon'] == "world")) + 1:]
# total_assists = [parser.parse_events("player_hurt")]

# total_deaths = []
# players = list(map(mapKDA, parser.parse_players()))
# teams = {"CT": list(filter(mapCT, players)), "T": list(filter(mapT, players))}
# rounds = match_deaths[len(match_deaths) - 1]["round"] + 1


# data = {"players": players, "teams": teams, }

# print(json.dumps(parser.parse_events("team_info")))

# # print(
# #     json.dumps(data)
# # )
