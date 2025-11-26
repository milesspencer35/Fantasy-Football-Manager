import os
from dotenv import load_dotenv
import json
import sys
sys.path.insert(0, r"./espn-api")
from espn_api.football import League, Team

load_dotenv()

LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
LEAGUE_YEAR = int(os.getenv("LEAGUE_YEAR"))
ESPN_S2 = os.getenv("ESPN_S2")
ESPN_SWID = os.getenv("ESPN_SWID")
TEAM_NAME = os.getenv("TEAM_NAME")

BENCH_COUNT = 7
IR_COUNT = 1
SCORING_TYPE = "Full PPR"


def kicking_get_breakdown(breakdown):
	return {
		"made_field_goals": int(breakdown.get("madeFieldGoals", 0)),
		"attempted_field_goals": int(breakdown.get("attemptedFieldGoals", 0)),
		"made_extra_points": int(breakdown.get("madeExtraPoints", 0)),
		"attempted_extra_points": int(breakdown.get("attemptedExtraPoints", 0))
	}


def passing_get_breakdown(breakdown):
	return {
		"passing_attempts": int(breakdown.get("passingAttempts", 0)),
		"passing_completions": int(breakdown.get("passingCompletions", 0)),
		"pass_yards": int(breakdown.get("passingYards", 0)),
		"pass_touchdowns": int(breakdown.get("passingTouchdowns", 0)),
		"pass_interceptions": int(breakdown.get("passingInterceptions", 0)),
	}


def rushing_get_breakdown(breakdown):
	return {
		"rushing_attempts": int(breakdown.get("rushingAttempts", 0)),
		"rushing_yards": int(breakdown.get("rushingYards", 0)),
		"rushing_touchdowns": int(breakdown.get("rushingTouchdowns", 0)),
	}


def receiving_get_breakdown(breakdown):
	return {
		"receiving_receptions": int(breakdown.get("receivingReceptions", 0)),
		"receiving_yards": int(breakdown.get("receivingYards", 0)),
		"receiving_touchdowns": int(breakdown.get("receivingTouchdowns", 0)),
		"receiving_targets": int(breakdown.get("receivingTargets", 0)),
	}


def defense_get_breakdown(breakdown):
	return {
		"points_allowed": int(breakdown.get("defensivePointsAllowed", 0)),
		"yards_allowed": int(breakdown.get("defensiveYardsAllowed", 0)),
		"sacks": int(breakdown.get("defensiveSacks", 0)),
		"interceptions": int(breakdown.get("defensiveInterceptions", 0)),
		"fumble_recoveries": int(breakdown.get("defensiveFumbles", 0)),  # sometimes listed as defensiveFumbles
		"defensive_and_special_teams_touchdowns": int(breakdown.get("defensivePlusSpecialTeamsTouchdowns", 0)),
	}


class TeamData(object):
	def __init__(self):
		self.league = League(
    		league_id=LEAGUE_ID,
    		year=LEAGUE_YEAR,
    		espn_s2=ESPN_S2,
    		swid=ESPN_SWID
		)

		self.userTeamIndex = None
		self.userTeam = None
		for team in self.league.teams:
			if team.team_name == TEAM_NAME:
				self.userTeamIndex = self.league.teams.index(team)
				self.userTeam = team

	def team_analyzer_json_data(self):
		data = {
			"league": self.league_data(),
			"players": self.players_data()
		}

		# print(json.dumps(data, indent=2))

		return json.dumps(data, indent=2)

	def players_data(self):
		players = []

		players_past_data = self.players_past_weeks_fantasy_data()
		players_current_data = self.players_current_info_data()

		for player in self.userTeam.roster:
			player_data = {
				"name": player.name,
				**players_current_data[player.name],
				**players_past_data[player.name],
			}
			players.append(player_data)

		return players

	def players_past_weeks_fantasy_data(self) -> dict:
		players = {}
		for player in self.userTeam.roster:
			pastWeeksData = {}

			year_stats = self.league.player_info(player.name).stats

			for week, stats in year_stats.items():
				# skip the projected (week 0) entry if present
				if week == 0 or week >= self.league.current_week:
					continue

				breakdown = stats.get("breakdown", {})

				position_stats = None
				if player.position == 'QB':
					position_stats = {**passing_get_breakdown(breakdown), **rushing_get_breakdown(breakdown)}
				elif player.position == 'RB':
					position_stats = {**rushing_get_breakdown(breakdown), **receiving_get_breakdown(breakdown)}
				elif player.position == 'WR' or player.position == 'TE':
					position_stats = receiving_get_breakdown(breakdown)
				elif player.position == 'D/ST':
					position_stats = defense_get_breakdown(breakdown)
				else:
					position_stats = kicking_get_breakdown(breakdown)

				pastWeeksData[f"Week {week}"] = {
					"fantasy_points": round(stats.get("points", 0), 2),
					**position_stats
				}

			players[player.name] = pastWeeksData

		return players

	def players_current_info_data(self):
		boxScoreLineup = self.get_box_score_lineup()
		players = {}
		for player in boxScoreLineup:
			players[player.name] = {
				"position": player.position,
				"nfl_team": player.proTeam,
				"injury_status": player.injuryStatus,
				# "eligible_slots": player.eligibleSlots,
				# "position_rank": player.posRank,
				"projected_points": player.projected_points,
				"pro_opponent": player.pro_opponent,
				"opponent_rank_vs_player_position (1 = toughest matchup, 32 = easiest matchup)": player.pro_pos_rank,
				"on_bye_week": player.on_bye_week,
				# "active_status": player.active_status,

			}

		return players

	def get_box_score_lineup(self):
		teamBoxScore = self.get_box_score()

		boxScoreLineup = None
		if teamBoxScore.home_team == self.userTeam:
			boxScoreLineup = teamBoxScore.home_lineup
		else:
			boxScoreLineup = teamBoxScore.away_lineup

		return boxScoreLineup

	def get_box_score(self):
		teamBoxScore = None
		for box_score in self.league.box_scores(self.league.current_week):
			if box_score.home_team == self.userTeam:
				teamBoxScore = box_score
				break
			elif box_score.away_team == self.userTeam:
				teamBoxScore = box_score
				break

		return teamBoxScore

	def league_data(self):
		data = {
			"current_week": self.league.current_week,
			"scoring_type": SCORING_TYPE,
			"roster_positions": [
				"QB",
				"RB",
				"RB",
				"WR",
				"WR",
				"TE",
				{"FLEX": ["RB", "WR", "TE"]},
				"DST",
				"K"
			],
			"bench_count": BENCH_COUNT,
			"IR_count": IR_COUNT
		}

		return data
