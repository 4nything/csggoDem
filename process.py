from awpy import DemoParser
import numpy as np
from enum import Enum
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone
import json
import requests
import pymongo
import os

load_dotenv(dotenv_path="./.env")
mongo_user = os.environ.get("MONGO_USER")
mongo_password = os.environ.get("MONGO_PASSWORD")
mongo_name = os.environ.get("MONGO_NAME")
mongo_port = os.environ.get("MONGO_PORT")
mongo_url_matches = os.environ.get("MONGO_URL_CSGO_MATCHES")

client = pymongo.MongoClient(mongo_url_matches)

db = client["CSGO"]
collection = db["Matches"]


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


def get_match():
    # Players Map
    def get_players():
        def mapKills(round, steamID, keyType):
            return len([kill for kill in round["kills"] if kill[keyType] == steamID])

        def mapADR(round, steamID):
            return sum([damage["hpDamageTaken"] for damage in round["damages"] if damage["isFriendlyFire"] == False and damage["attackerSteamID"] == steamID])

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
            return sum([flash["flashDuration"] for flash in round["flashes"] if flash["attackerSteamID"] == steamID and isEnemy(steamID, flash["playerSteamID"])])

        def getUtilityDamage(round, steamID):
            return sum([damage["hpDamage"] for damage in round["damages"] if damage["attackerSteamID"] == steamID and damage["victimSide"] != damage["attackerSide"] and damage["weaponClass"] == "Grenade"])

        def getFirst(round, action, steamID, side):
            return len([kill for kill in round["kills"] if kill[action + "SteamID"] == steamID and kill["isFirstKill"] == True and kill[action + "Side"] == side])

        def getTrades(round, steamID, side):
            return len([kill for kill in round["kills"] if next((k["victimSteamID"] for k in round["kills"] if k["isFirstKill"]), None) == kill["playerTradedSteamID"] and kill["attackerSteamID"] == steamID and kill["attackerSide"] == side])

        def getTraded(round, steamID, side):
            return len([kill for kill in round["kills"] if next((k["attackerSteamID"] for k in round["kills"] if k["victimSteamID"] == steamID and k["isFirstKill"] == True), None) == kill["victimSteamID"] and kill["playerTradedSteamID"] == steamID and kill["playerTradedSide"] == side])

        def getClutch(round, steamID, vX):
            side = "ct" if next((frame for frame in round["frames"] if next(
                (player for player in frame["ct"]["players"] if player["steamID"] == steamID), None) != None), None) != None else "t"
            clutchCount = 0
            isAlive = True
            for frame in round["frames"]:
                isAlive = next((player for player in frame[side]["players"] if player["steamID"]
                                == steamID and player["isAlive"] == True), None) != None

                if frame[side]["alivePlayers"] == 1 and isAlive:
                    clutchCount = 1
                else:
                    clutchCount = 0

            return 1 if clutchCount == vX else 0

        def getMultikill(round, steamID, multikill):
            return 1 if len([kill for kill in round["kills"] if kill["attackerSteamID"] == steamID and kill["isSuicide"] == False]) == multikill else 0

        def get_impact(round, steamID):
            kills = len([kill for kill in round["kills"]
                        if kill["attackerSteamID"] == steamID])
            deaths = len([kill for kill in round["kills"]
                         if kill["victimSteamID"] == steamID])
            assists = len([kill for kill in round["kills"]
                          if kill["assisterSteamID"] == steamID])
            damage = sum([damage["hpDamageTaken"]
                         for damage in round["damages"] if damage["attackerSteamID"] == steamID])
            headshots = sum([mapHeadshot(round, steamID)
                            for round in data["gameRounds"]])
            return headshots + (0.7 * kills) - (0.3 * deaths) + (0.5 * assists) + (0.01 * damage)

        # impact_rating = sum([get_impact(round, player["steamID"]) for round in data["gameRounds"]]) / len(data["gameRounds"])
        # variance = sum((get_impact(round, player["steamID"]) - impact_rating) ** 2 for round in data["gameRounds"]) / len(data["gameRounds"])
        # rating = ((1.3 * ((len(data["gameRounds"] / )))))
        # rating = 0
        def map_player_stats(player):
            p = {
                "kills": sum([mapKills(round, player["steamID"], "attackerSteamID") for round in data["gameRounds"]]),
                "deaths": sum([mapKills(round, player["steamID"], "victimSteamID") for round in data["gameRounds"]]),
                "assists": sum([mapKills(round, player["steamID"], "assisterSteamID") for round in data["gameRounds"]]),
                "adr": sum([mapADR(round, player["steamID"]) for round in data["gameRounds"]]) / len(data["gameRounds"]),
                "rank": getRank(player["steamID"]),
                "promoted": getPromotion(True, player["steamID"]),
                "demoted": getPromotion(False, player["steamID"]),
                "enemy_flashed": sum([getFlashes(round, player["steamID"]) for round in data["gameRounds"]]),
                "flash_assists": sum([isFlashedAssist(round, player["steamID"]) for round in data["gameRounds"]]),
                "enemy_flash_duration": sum([getFlashDuration(round, player["steamID"]) for round in data["gameRounds"]]),
                "utility_damage": sum([getUtilityDamage(round, player["steamID"]) for round in data["gameRounds"]]),
                "first_kills": {
                    "asCT": sum([getFirst(round, 'attacker', player["steamID"], 'CT') for round in data["gameRounds"]]),
                    "asT": sum([getFirst(round, 'attacker', player["steamID"], 'T') for round in data["gameRounds"]])
                },
                "first_deaths": {
                    "asCT": sum([getFirst(round, 'victim', player["steamID"], 'CT') for round in data["gameRounds"]]),
                    "asT": sum([getFirst(round, 'victim', player["steamID"], 'T') for round in data["gameRounds"]]),
                },
                "trades":  {
                    "kills": {
                        "asCT": sum([getTrades(round, player["steamID"], "CT") for round in data["gameRounds"]]),
                        "asT": sum([getTrades(round, player["steamID"], "T") for round in data["gameRounds"]])
                    },
                    "deaths": {
                        "asCT": sum([getTraded(round, player["steamID"], "CT") for round in data["gameRounds"]]),
                        "asT": sum([getTraded(round, player["steamID"], "T") for round in data["gameRounds"]]),
                    }
                },
                "clutches": {
                    "vOne": sum([getClutch(round, player["steamID"], 1) for round in data["gameRounds"]]),
                    "vTwo": sum([getClutch(round, player["steamID"], 2) for round in data["gameRounds"]]),
                    "vThree": sum([getClutch(round, player["steamID"], 3) for round in data["gameRounds"]]),
                    "vFour": sum([getClutch(round, player["steamID"], 4) for round in data["gameRounds"]]),
                    "vFive": sum([getClutch(round, player["steamID"], 5) for round in data["gameRounds"]]),
                },
                "multi_kills": {
                    "kOne": sum([getMultikill(round, player["steamID"], 1) for round in data["gameRounds"]]),
                    "kTwo": sum([getMultikill(round, player["steamID"], 2) for round in data["gameRounds"]]),
                    "kThree": sum([getMultikill(round, player["steamID"], 3) for round in data["gameRounds"]]),
                    "kFour": sum([getMultikill(round, player["steamID"], 4) for round in data["gameRounds"]]),
                    "kFive": sum([getMultikill(round, player["steamID"], 5) for round in data["gameRounds"]]),
                },
            }

            return {
                **p,
                "difference": p["kills"] - p["deaths"],
                "kd": p["kills"] / p["deaths"] if p["deaths"] > 0 else p["kills"],
                "hs": int(sum([mapHeadshot(round, player["steamID"])for round in data["gameRounds"]]) / p["kills"] * 100),
                "kast": int(sum([mapKAST(round, player["steamID"])for round in data["gameRounds"]]) / len(data["gameRounds"]) * 100),
            }

        return [map_player_stats(player) for player in [*[{**player, "teamStarted": "ct"} for player in data["gameRounds"][0]["ctSide"]["players"]], *[{**player, "teamStarted": "t"} for player in data["gameRounds"][0]["tSide"]["players"]]]]

    # Round Map
    def get_rounds():
        def map_round_kill(kill):
            return {
                "attacker": kill["attackerName"],
                "attackerSteamId": kill["attackerSteamID"],
                "assister": kill["assisterName"],
                "assisterSteamId": kill["assisterSteamID"],
                "victim": kill["victimName"],
                "victimSteamId": kill["victimSteamID"],
                "isHeadshot": kill["isHeadshot"],
                "isSuicide": kill["isSuicide"],
                "isWallbang": kill["isWallbang"],
                "isFlashed": kill["flashThrowerSteamID"] != None,
                "time": '00:00' if kill["clockTime"] == '02:00' or kill["clockTime"] == '00:00' else ('00' if kill["clockTime"].split(":")[0] == '01' else '01') + ':' + (str(60 - int(kill["clockTime"].split(":")[1])) if int(kill["clockTime"].split(":")[1]) >= 10 else "0" + str(60 - int(kill["clockTime"].split(":")[1]))),
                "weapon": kill["weapon"],
            }

        def map_round(round):
            return {
                "ct": {
                    "cash_spent": round["ctRoundSpendMoney"],
                    "equipment_value": round["ctFreezeTimeEndEqVal"],
                    "players_alive": round["frames"][len(round["frames"]) - 1]["ct"]["alivePlayers"],
                },
                "t": {
                    "cash_spent": round["tRoundSpendMoney"],
                    "equipment_value": round["tFreezeTimeEndEqVal"],
                    "players_alive": round["frames"][len(round["frames"]) - 1]["t"]["alivePlayers"],
                },
                "kills": [map_round_kill(kill) for kill in round["kills"]]
            }

        return [map_round(round) for round in data["gameRounds"]]

    # Weapons Map
    def get_weapons():
        def map_weapons_item(weapon):
            players = [*[{**player, "side": "A"} for player in data["gameRounds"][0]["ctSide"]["players"]],
                       *[{**player, "side": "B"} for player in data["gameRounds"][0]["tSide"]["players"]]]
            return {
                weapon: [map_weapons_player_stats(
                    player, weapon) for player in players if weapons_player_used(player["steamID"], weapon)]
            }

        def map_weapons_player_stats(player, weapon):
            kills = len([kill for round in data["gameRounds"] for kill in round["kills"]
                        if kill["attackerSteamID"] == player["steamID"] and kill["weapon"] == weapon])
            shots = len([shot for round in data["gameRounds"] for shot in round["weaponFires"]
                        if shot["playerSteamID"] == player["steamID"] and shot["weapon"] == weapon])
            damage = sum([damage["hpDamageTaken"] for round in data["gameRounds"] for damage in round["damages"]
                         if damage["attackerSteamID"] == player["steamID"] and damage["weapon"] == weapon])
            return {
                "player": player["playerName"],
                "steamID": player["steamID"],
                "kills": kills,
                "hs": round(len([kill for round in data["gameRounds"] for kill in round["kills"] if kill["attackerSteamID"] == player["steamID"] and kill["weapon"] == weapon and kill["isHeadshot"] == True]) * 100 / kills) if kills > 0 else 0,
                "shots": shots,
                "accuracy": round(len([damage for round in data["gameRounds"] for damage in round["damages"] if damage["attackerSteamID"] == player["steamID"] and damage["isFriendlyFire"] == False and damage["weapon"] == weapon]) * 100 / shots) if shots > 0 else 0,
                "damage": damage if damage != None else 0
            }

        def weapons_player_used(steamID, weapon):
            return len([shot for round in data["gameRounds"] for shot in round["weaponFires"]
                        if shot["playerSteamID"] == steamID and shot["weapon"] == weapon]) > 0

        weapons = list(np.unique([kill["weapon"] for round in data["gameRounds"]
                                  for kill in round["kills"] if kill["weapon"] != "World"]))

        return [map_weapons_item(weapon) for weapon in weapons]

    # HeatMaps Map
    def get_heatmaps():
        return {
            "first_half": {
                "ct": {
                    "killer_locations": [{"x": kill["attackerX"], "y": kill["attackerY"]} for round in data["gameRounds"] for kill in round["kills"] if any(player for player in data["gameRounds"][0]["ctSide"]["players"] if kill["attackerSteamID"] == player["steamID"])],
                    "death_locations": [{"x": kill["victimX"], "y": kill["victimY"]} for round in data["gameRounds"] for kill in round["kills"] if any(player for player in data["gameRounds"][0]["ctSide"]["players"] if kill["victimSteamID"] == player["steamID"])],
                    "shots": [{"x": shot["playerX"], "y": shot["playerY"]} for round in data["gameRounds"] for shot in round["weaponFires"] if any(player for player in data["gameRounds"][0]["ctSide"]["players"] if player["steamID"] == shot["playerSteamID"])],
                    "damage_dealt": [{"x": damage["attackerX"], "y": damage["attackerY"]} for round in data["gameRounds"] for damage in round["damages"] if any(player for player in data["gameRounds"][0]["ctSide"]["players"] if player["steamID"] == damage["attackerSteamID"])],
                    "damage_taken": [{"x": damage["victimX"], "y": damage["victimY"]} for round in data["gameRounds"] for damage in round["damages"] if any(player for player in data["gameRounds"][0]["ctSide"]["players"] if player["steamID"] == damage["victimSteamID"])],
                    "smoke": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Smoke Grenade" and any(player for player in data["gameRounds"][0]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "flash": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"]
                              == "Flashbang" and any(player for player in data["gameRounds"][0]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "he": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] ==
                           "HE Grenade" and any(player for player in data["gameRounds"][0]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                },
                "t": {
                    "killer_locations": [{"x": kill["attackerX"], "y": kill["attackerY"]} for round in data["gameRounds"] for kill in round["kills"] if any(player for player in data["gameRounds"][0]["tSide"]["players"] if kill["attackerSteamID"] == player["steamID"])],
                    "death_locations": [{"x": kill["victimX"], "y": kill["victimY"]} for round in data["gameRounds"] for kill in round["kills"] if any(player for player in data["gameRounds"][0]["tSide"]["players"] if kill["victimSteamID"] == player["steamID"])],
                    "shots": [{"x": shot["playerX"], "y": shot["playerY"]} for round in data["gameRounds"] for shot in round["weaponFires"] if any(player for player in data["gameRounds"][0]["tSide"]["players"] if player["steamID"] == shot["playerSteamID"])],
                    "damage_dealt": [{"x": damage["attackerX"], "y": damage["attackerY"]} for round in data["gameRounds"] for damage in round["damages"] if any(player for player in data["gameRounds"][0]["tSide"]["players"] if player["steamID"] == damage["attackerSteamID"])],
                    "damage_taken": [{"x": damage["victimX"], "y": damage["victimY"]} for round in data["gameRounds"] for damage in round["damages"] if any(player for player in data["gameRounds"][0]["tSide"]["players"] if player["steamID"] == damage["victimSteamID"])],
                    "smoke": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Smoke Grenade" and any(player for player in data["gameRounds"][0]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "flash": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Flashbang" and any(player for player in data["gameRounds"][0]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "he": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "HE Grenade" and any(player for player in data["gameRounds"][0]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                }
            },
            "second_half": {
                "ct": {
                    "killer_locations":  [{"x": kill["attackerX"], "y": kill["attackerY"]} for round in data["gameRounds"] for kill in round["kills"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if kill["attackerSteamID"] == player["steamID"])],
                    "death_locations":   [{"x": kill["victimX"], "y": kill["victimY"]} for round in data["gameRounds"] for kill in round["kills"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if kill["victimSteamID"] == player["steamID"])],
                    "shots":  [{"x": shot["playerX"], "y": shot["playerY"]} for round in data["gameRounds"] for shot in round["weaponFires"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if player["steamID"] == shot["playerSteamID"])],
                    "damage_dealt":  [{"x": damage["attackerX"], "y": damage["attackerY"]} for round in data["gameRounds"] for damage in round["damages"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if player["steamID"] == damage["attackerSteamID"])],
                    "damage_taken":  [{"x": damage["victimX"], "y": damage["victimY"]} for round in data["gameRounds"] for damage in round["damages"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if player["steamID"] == damage["victimSteamID"])],
                    "smoke":  [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Smoke Grenade" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "flash":  [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Flashbang" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "he":  [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "HE Grenade" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["ctSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                },
                "t": {
                    "killer_locations": [{"x": kill["attackerX"], "y": kill["attackerY"]} for round in data["gameRounds"] for kill in round["kills"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if kill["attackerSteamID"] == player["steamID"])],
                    "death_locations": [{"x": kill["victimX"], "y": kill["victimY"]} for round in data["gameRounds"] for kill in round["kills"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if kill["victimSteamID"] == player["steamID"])],
                    "shots": [{"x": shot["playerX"], "y": shot["playerY"]} for round in data["gameRounds"] for shot in round["weaponFires"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if player["steamID"] == shot["playerSteamID"])],
                    "damage_dealt": [{"x": damage["attackerX"], "y": damage["attackerY"]} for round in data["gameRounds"] for damage in round["damages"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if player["steamID"] == damage["attackerSteamID"])],
                    "damage_taken": [{"x": damage["victimX"], "y": damage["victimY"]} for round in data["gameRounds"] for damage in round["damages"] if len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if player["steamID"] == damage["victimSteamID"])],
                    "smoke": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Smoke Grenade" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "flash": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "Flashbang" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                    "he": [{"x": smoke["throwerX"], "y": smoke["throwerY"]} for round in data["gameRounds"] for smoke in round["grenades"] if smoke["grenadeType"] == "HE Grenade" and len(data["gameRounds"]) > 15 and any(player for player in data["gameRounds"][15]["tSide"]["players"] if smoke["throwerSteamID"] == player["steamID"])],
                }
            }
        }

    # Duels Map
    def get_duels():
        def map_player_duels(player, enemyTeam):
            return {player["playerName"]: [map_player_duel_player(player, enemy) for enemy in enemyTeam]}

        def map_player_duel_player(player, enemy):
            kills = len([kill for round in data["gameRounds"] for kill in round["kills"]
                        if kill["attackerSteamID"] == player["steamID"] and kill["victimSteamID"] == enemy["steamID"]])
            deaths = len([kill for round in data["gameRounds"] for kill in round["kills"]
                          if kill["attackerSteamID"] == enemy["steamID"] and kill["victimSteamID"] == player["steamID"]])
            return {
                enemy["playerName"]: {
                    "enemySteamID": enemy["steamID"],
                    "kills": kills,
                    "deaths":  deaths,
                    "rate": round((kills) * 100 / (kills+deaths)) if kills+deaths > 0 else 0
                }
            }

        teamA = data["gameRounds"][0]["ctSide"]["players"]
        teamB = data["gameRounds"][0]["tSide"]["players"]

        return [*[map_player_duels(player, teamB) for player in teamA], *[map_player_duels(player, teamA) for player in teamB]]

    # Define Global Variables
    parser = DemoParser("match.dem")
    data = parser.parse()
    return {
        "mapName": data["mapName"],
        "teams": [*[player["steamID"] for player in data["gameRounds"][0]["ctSide"]["players"]], *[player["steamID"] for player in data["gameRounds"][0]["tSide"]["players"]]],
        "rounds": get_rounds(),
        "players": get_players(),
        "weapons": get_weapons(),
        "duels": get_duels(),
        "heatmaps": get_heatmaps(),
    }


match = get_match()
print(collection.insert_one(match))
