import json


def pprint(printable_str):
    print(json.dumps(printable_str, indent=2))


def calculate_points(scoring_settings, stats):
    pts = 0
    for setting, value in scoring_settings.items():
        if setting in stats.keys():
            pts += stats[setting] * value
    return pts


"""
Currently needs to be an exact match.
"""
def search_for_player_by_name(players, name):
    for player_id, player in players.items():
        if player.get('full_name') and player['full_name'] == name:
            return player
