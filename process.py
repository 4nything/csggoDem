from awpy import DemoParser
from awpy.analytics.stats import player_stats
import json
import numpy as np
from enum import Enum
from flask import Flask


class RANKS(Enum):
    Unranked = 0
    Silver_1 = 1
    Silver_2 = 2
    Silver_3 = 3
    Silver_4 = 4
    Silver_Elite = 5
    Silver_Elite_Master = 6
    Gold_Nova_1 = 7
    Gold_Nova_2 = 8
    Gold_Nova_3 = 9
    Gold_Nova_Master = 10
    Master_Guardian_1 = 11
    Master_Guardian_2 = 12
    Master_Guardian_Elite = 13
    Distinguished_Master_Guardian = 14
    Legendary_Eagle = 15
    Legendary_Eagle_Master = 16
    Supreme_Master_First_Class = 17
    Global_Elite = 18


app = Flask(__name__)


@app.route('/match', methods=['GET'])
def get_match():
    # Your code to handle the GET request goes here
    # You can replace the following line with your own implementation
    def mapPlayers(player):
        # return player
        playerStats = {
            **player,
            "kills": sumArray([mapKills(round, player["steamID"], "attackerSteamID") for round in data["gameRounds"]]),
            "deaths": sumArray([mapKills(round, player["steamID"], "victimSteamID") for round in data["gameRounds"]]),
            "assists": sumArray([mapKills(round, player["steamID"], "assisterSteamID") for round in data["gameRounds"]]),
            "adr": sumArray([mapADR(round, player["steamID"]) for round in data["gameRounds"]]) / len(data["gameRounds"]),
            "rank": getRank(player["steamID"]),
            "promoted": getPromotion(True, player["steamID"]),
            "demoted": getPromotion(False, player["steamID"]),
            "enemy_flashed": sumArray([getFlashes(round, player["steamID"]) for round in data["gameRounds"]]),
            "flash_assists": sumArray([isFlashedAssist(round, player["steamID"]) for round in data["gameRounds"]]),
            "enemy_flash_duration": sumArray([getFlashDuration(round, player["steamID"]) for round in data["gameRounds"]]),
            "utility_damage": sumArray([getUtilityDamage(round, player["steamID"]) for round in data["gameRounds"]]),
            "first_kills": {
                "asCT": sumArray([getFirst(round, 'attacker', player["steamID"], 'CT') for round in data["gameRounds"]]),
                "asT": sumArray([getFirst(round, 'attacker', player["steamID"], 'T') for round in data["gameRounds"]])
            },
            "first_deaths": {
                "asCT": sumArray([getFirst(round, 'victim', player["steamID"], 'CT') for round in data["gameRounds"]]),
                "asT": sumArray([getFirst(round, 'victim', player["steamID"], 'T') for round in data["gameRounds"]]),
            },
            "trades": {
                "kills": {
                    "asCT": sumArray([getTrades(round, player["steamID"], "CT") for round in data["gameRounds"]]),
                    "asT": sumArray([getTrades(round, player["steamID"], "T") for round in data["gameRounds"]])
                },
                 "deaths": {
                    "asCT": sumArray([getTraded(round, player["steamID"], "CT") for round in data["gameRounds"]]),
                    "asT": sumArray([getTraded(round, player["steamID"], "T") for round in data["gameRounds"]]),
                }
            },
            "clutches": {
                "1v1": [getOneVOne(round, player["steamID"]) for round in data["gameRounds"]]
            }
        }
        return {
            **playerStats,
            "difference": playerStats["kills"] - playerStats["deaths"],
            "K/D": playerStats["kills"] / playerStats["deaths"] if playerStats["deaths"] > 0 else playerStats["kills"],
            "HS%": str(int(sumArray([mapHeadshot(round, player["steamID"]) for round in data["gameRounds"]]) / playerStats["kills"] * 100)) + '%',
            "KAST": str(int(sumArray([mapKAST(round, player["steamID"]) for round in data["gameRounds"]]) / len(data["gameRounds"]) * 100)) + '%'
        }

    def mapKills(round, steamID, keyType):
        return len([kill for kill in round["kills"] if kill[keyType] == steamID])

    def sumArray(arr):
        sum = 0
        for i in arr:
            sum = sum + i
        return sum

    def mapADR(round, steamID):
        return sumArray([damage["hpDamageTaken"] for damage in round["damages"] if damage["isFriendlyFire"] == False and damage["attackerSteamID"] == steamID])

    def getRank(steamID):
        rank = ""
        for r in data["matchmakingRanks"]:
            if (r["steamID"] == steamID):
                rank = r["rankNew"]
        return rank

    def getPromotion(promoted, steamID):
        isPromoted = False
        isDemoted = False
        for r in data["matchmakingRanks"]:
            if (r["steamID"] == steamID):
                isPromoted = RANKS[r["rankNew"].replace(
                    ' ', '_')].value > RANKS[r["rankOld"].replace(' ', '_')].value
                isDemoted = RANKS[r["rankNew"].replace(
                    ' ', '_')].value > RANKS[r["rankOld"].replace(' ', '_')].value
        return isPromoted if promoted else isDemoted

    def mapHeadshot(round, steamdID):
        return len([kill for kill in round["kills"] if kill["attackerSteamID"] == steamdID and kill["isHeadshot"] == True])

    def mapKAST(round, steamID):
        return 1 if len([kill for kill in round["kills"]
                         if kill["attackerSteamID"] == steamID
                         or kill["assisterSteamID"] == steamID
                         or len([k for k in round["kills"] if k["victimSteamID"] == steamID]) == 0
                         or (kill["playerTradedSteamID"] == steamID and kill["attackerSteamID"] != steamID)]) > 0 else 0

    def getFlashes(round, steamID):
        return len([flash for flash in round["flashes"] if flash["attackerSteamID"] == steamID and isEnemy(steamID, flash["playerSteamID"])])

    def isEnemy(steamID, victimSteamID):
        return True if ((next((player for player in data["gameRounds"][0]["ctSide"]["players"] if player["steamID"] == steamID), False)
                        and next((player for player in data["gameRounds"][0]["tSide"]["players"] if player["steamID"] == victimSteamID), False))
                        or
                        (next((player for player in data["gameRounds"][0]["tSide"]["players"] if player["steamID"] == steamID), False)
                        and next((player for player in data["gameRounds"][0]["ctSide"]["players"] if player["steamID"] == victimSteamID), False))) else False

    def isFlashedAssist(round, steamID):
        return len([kill for kill in round["kills"] if kill["flashThrowerSteamID"] == steamID and kill["flashThrowerSide"] == kill["attackerSide"] and kill["flashThrowerSteamID"] != kill["attackerSteamID"]])

    def getFlashDuration(round, steamID):
        return sumArray([flash["flashDuration"] for flash in round["flashes"] if flash["attackerSteamID"] == steamID and isEnemy(steamID, flash["playerSteamID"])])
    
    def getUtilityDamage(round, steamID):
        return sumArray([damage["hpDamage"] for damage in round["damages"] if damage["attackerSteamID"] == steamID and damage["victimSide"] != damage["attackerSide"] and damage["weaponClass"] == "Grenade"])

    def getFirst(round, action, steamID, side):
        return len([kill for kill in round["kills"] if kill[action + "SteamID"] == steamID and kill["isFirstKill"] == True and kill[action + "Side"] == side])

    def getTrades(round, steamID, side):
        return len([kill for kill in round["kills"] if next((k["victimSteamID"] for k in round["kills"] if k["isFirstKill"]), None) == kill["playerTradedSteamID"] and kill["attackerSteamID"] == steamID and kill["attackerSide"] == side])
    
    def getTraded(round, steamID, side):
        return len([kill for kill in round["kills"] if next((k["attackerSteamID"] for k in round["kills"] if k["victimSteamID"] == steamID and k["isFirstKill"] == True), None) == kill["victimSteamID"] and kill["playerTradedSteamID"] == steamID and kill["playerTradedSide"] == side])

    def getOneVOne(round, steamID):
        return

    parser = DemoParser("match.dem")
    # parser.parse()
    data = parser.parse()

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
        },
        "matchInfo": {
            "map": data["mapName"]
        }
    }

    # return data["gameRounds"][0]["frames"]
    return match


if __name__ == '__main__':
    app.run(debug=True)
