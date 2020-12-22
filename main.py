import json
import utils
import os
import os.path
from datetime import timedelta, datetime
from sleeper_wrapper import League, User, Players, Stats


def resource_needs_update(path):
    five_days_ago = datetime.timestamp(datetime.now() - timedelta(days=5))
    ctime = os.path.getctime(path)
    if ctime < five_days_ago:
        return True
    else:
        return False


def update_players(path):
    print("Updating players.")
    p = Players()
    players = p.get_all_players()
    # resp_data = json.loads(resp.json())
    with open(path, 'w') as outfile:
        json.dump(players, outfile, indent=2)
    return players


def update_stats(path, week):
    print("Updating stats.")
    s = Stats()
    curr_stats = s.get_week_stats('regular', config['seasonYear'], week)
    with open(path, 'w') as outfile:
        json.dump(curr_stats, outfile, indent=2)
        outfile.close()
    return curr_stats


def update_projections(path, week):
    print("Updating Projections.")
    s = Stats()
    curr_projections = s.get_week_projections('regular', config['seasonYear'], week)
    with open(path, 'w') as outfile:
        json.dump(curr_projections, outfile, indent=2)
        outfile.close()
    return curr_projections


def get_users():
    raw_users = league.get_users()
    raw_rosters = league.get_rosters()

    users = {}
    for user in raw_users:
        users[user["user_id"]] = {
            "user_id": user["user_id"],
            "display_name": user['display_name']
        }
        if user['metadata'].get('team_name'):
            users[user["user_id"]]["team_name"] = user['metadata']['team_name']
        else:
            users[user["user_id"]]["team_name"] = "Team" + user['display_name']
    for roster in raw_rosters:
        users[roster['owner_id']]['current_starters'] = roster['starters']
        users[roster['owner_id']]['current_roster'] = roster['players']
        users[roster['owner_id']]['current_reserves'] = roster['reserve']
        users[roster['owner_id']]['roster_id'] = roster['roster_id']
        users[roster['owner_id']]['standings'] = {
            'wins': roster['settings']['wins'],
            'losses': roster['settings']['losses'],
            'ties': roster['settings']['ties'],
            'fpts': float(str(roster['settings']['fpts']) + '.' + str(roster['settings']['fpts_decimal'])),
            'ppts': float(str(roster['settings']['ppts']) + '.' + str(roster['settings']['ppts_decimal'])),
            'fpts_against': float(str(roster['settings']['fpts_against']) + '.' + str(roster['settings']['fpts_against_decimal'])),
            'waiver_budget_used': roster['settings']['waiver_budget_used']
        }
    w1m = league.get_matchups(1)
    print(users)


def get_players():
    players_path = 'resources/players.json'
    if os.path.exists(players_path):
        with open(players_path) as players_file:
            try:
                if not resource_needs_update(players_path):
                    return json.load(players_file)
                else:
                    return update_players(players_path)
            except:
                print("Error handling players.json file")
    else:
        print("No players json found. Gathering new one.")
        return update_players(players_path)



def get_stats_and_projections():
    all_weeks = range(1, int(config['seasonWeek']) + 1)
    all_weeks_stats = []
    all_weeks_projections = []
    for week in all_weeks:
        week = str(week)
        stats_path = 'resources/stats/' + week + '.json'
        projections_path = 'resources/projections/' + week + '.json'
        if os.path.exists(stats_path):
            with open(stats_path) as week_stats:
                try:
                    all_weeks_stats.append(json.load(week_stats))
                except:
                    print("Error handling " + stats_path + " file.")
                week_stats.close()
        else:
            print("No stats json found for week " + week + ".")
            all_weeks_stats.append(update_stats(stats_path, week))

        if os.path.exists(projections_path):
            with open(projections_path) as week_projections:
                try:
                    all_weeks_projections.append(json.load(week_projections))
                except:
                    print("Error handling " + projections_path + " file.")
                week_projections.close()
        else:
            print("No projections json found for week " + str(week) + ".")
            all_weeks_projections.append(update_projections(projections_path, week))
    return all_weeks_stats, all_weeks_projections


def get_stats_projections_and_diff_for_player(player_id, scoring_settings):
    stats = Stats()
    player_pts_by_week = {}

    for week in all_weeks_stats:
        player_week_stats = stats.get_player_week_stats(week, player_id)
        player_pts_by_week[week[0]['week']] = {
            "stats": {},
            "projections": {}
        }
        if player_week_stats is not None:
            pts = utils.calculate_points(scoring_settings, player_week_stats['stats'])
            player_pts_by_week[week[0]['week']]['stats'] = round(pts, 2)
        else:
            player_pts_by_week[week[0]['week']]['stats'] = 'BYE'

    for week in all_weeks_projections:
        player_week_projections = stats.get_player_week_projections(week, player_id)
        if player_week_projections is not None:
            pts = utils.calculate_points(scoring_settings, player_week_projections['stats'])
            player_pts_by_week[week[0]['week']]['projections'] = round(pts, 2)
        else:
            player_pts_by_week[week[0]['week']]['projections'] = 'BYE'

    for week, stats in player_pts_by_week.items():
        if stats['stats'] != 'BYE':
            player_pts_by_week[week]["difference"] = round(
                float(player_pts_by_week[week]['stats']) - float(player_pts_by_week[week]['projections']), 2)

    return player_pts_by_week


"""
MAIN CODE HERE
"""

with open('config.json') as config_file:
    config = json.load(config_file)

league = League(config['leagueId'])
scoring_settings = league.get_scoring_settings()
users = league.get_users()
rosters = league.get_rosters()

get_users()
all_weeks_stats, all_weeks_projections = get_stats_and_projections()
players = get_players()


s_p = get_stats_projections_and_diff_for_player(utils.search_for_player_by_name(players, 'D.J. Chark')['player_id'], scoring_settings)

utils.pprint(s_p)
# utils.pprint(player_pts_by_week)
#utils.pprint(players['96'])
