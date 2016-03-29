#!/usr/bin/env python3

"""
Some simulations for NCAA March Madness.
"""

import argparse
import csv
import operator
import random
import statistics
import sys

from collections import deque
from queue import PriorityQueue

from schema import Schema
from strategy import Strategy, DefaultStrategies
from game import Game

TOTAL_TEAMS = 64
MAX_SCORE = (TOTAL_TEAMS / 2) * (len(Schema.ORDERED_ROUNDS) - 1)

COLOR_FORMAT = "\033[%dm"
COLOR_ENDING = "\033[0m"
JUSTIFICATION_SIZE = 33
EMPTY_SPACE = ''.ljust(JUSTIFICATION_SIZE)
TEAM_HEADER = '|_ '
LOSS_COLOR = 31
WIN_COLOR = 32
NEUTRAL_COLOR = 0

(
    TRACE,
    DEBUG,
    INFO,
    WARN,
    ERROR
) = range(5)
LOG_LEVEL = INFO


def log(level, log_msg):
    if level >= LOG_LEVEL:
        print(log_msg)


def compute_score(predicted_bracket, actual_bracket, strategy):
    if not actual_bracket or not predicted_bracket:
        raise ValueError("Received a null predicted or actual bracket")

    total_score = 0
    round_information = {}
    for round_index in range(1, len(Schema.ORDERED_ROUNDS)):
        round = Schema.ORDERED_ROUNDS[round_index]

        predicted_winners = [game.winner_name for game in get_round_games(predicted_bracket, round)]
        actual_winners = [game.winner_name for game in get_round_games(actual_bracket, round)]
        overlap_winners = [winner for winner in predicted_winners if winner in actual_winners]

        round_score = pow(2, round_index - 1) * len(overlap_winners)
        total_score += round_score

        round_information[round] = {
            'score': round_score,
            'predicted': predicted_winners,
            'actual': actual_winners,
            'intersection': overlap_winners
        }

    log(INFO, "%s %d/%d" % ((strategy.name + ':').ljust(JUSTIFICATION_SIZE), total_score, MAX_SCORE))
    log(DEBUG,
"""
  SEED = %d
  FAVORITE_BIAS = %f
  PROTECTED_FUN = %s
""" % (strategy.seed, strategy.favorite_bias, strategy.protected_function))

    for round_index in range(1, len(Schema.ORDERED_ROUNDS)):
        round = Schema.ORDERED_ROUNDS[round_index]
        information = round_information[round]
        log(DEBUG, "    %s: %d" % (round, information['score']))
        log(DEBUG,
"""      PREDICTED: %s
      ACTUAL: %s
      INTERSECTION: %s""" % (information['predicted'], information['actual'], information['intersection']))

    return total_score

def perform_predictions(game, strategy, season_rankings):
    if not game:
        return

    perform_predictions(game.winner_previous_game, strategy, season_rankings)
    perform_predictions(game.loser_previous_game, strategy, season_rankings)

    # Hack for opening round games
    if not game.winner_previous_game:
        favorite_game = Game(Schema.ORDERED_ROUNDS[Schema.ROUND_ORDER[game.round] - 1], None, 1, None, game.winner_name, game.winner_seed, game.winner_region, None, None, None)
        underdog_game = Game(Schema.ORDERED_ROUNDS[Schema.ROUND_ORDER[game.round] - 1], None, 1, None, game.loser_name, game.loser_seed, game.loser_region, None, None, None)

    elif game.winner_previous_game.winner_seed < game.loser_previous_game.winner_seed:
        favorite_game = game.winner_previous_game
        underdog_game = game.loser_previous_game
    elif game.winner_previous_game.winner_seed > game.loser_previous_game.winner_seed:
        favorite_game = game.loser_previous_game
        underdog_game = game.winner_previous_game
    else:
        winner_previous_ranking = int(season_rankings[game.winner_previous_game.winner_name])
        loser_previous_ranking = int(season_rankings[game.loser_previous_game.winner_name])

        if winner_previous_ranking == 0 and loser_previous_ranking == 0:
            # BOTH UNRANKED TEAMS... PICK THE LEFT ONE
            favorite_game = game.winner_previous_game
            underdog_game = game.loser_previous_game
        elif (winner_previous_ranking > loser_previous_ranking) or winner_previous_ranking == 0:
            favorite_game = game.loser_previous_game
            underdog_game = game.winner_previous_game
        elif (loser_previous_ranking > winner_previous_ranking) or loser_previous_ranking == 0:
            favorite_game = game.winner_previous_game
            underdog_game = game.loser_previous_game
        else:
            raise ValueError("Inception")

    # PICK THE CHOSEN ONES
    number_protected = 0
    if strategy.protected_function:
        number_protected = strategy.protected_function(game.round)

    # PERFORM THE COIN TOSS
    coin_toss = random.random()
    winner = favorite_game
    loser = underdog_game
    if favorite_game.winner_seed <= number_protected:
        log(DEBUG,
                "PROTECTED %s: %s [%d] OVER %s [%d]" %
                (game.round, favorite_game.winner_name, favorite_game.winner_seed, underdog_game.winner_name, underdog_game.winner_seed)
        )
    elif coin_toss > strategy.favorite_bias:
        log(DEBUG,
                "UPSET %s: %s [%d] OVER %s [%d]" %
                (game.round, underdog_game.winner_name, underdog_game.winner_seed, favorite_game.winner_name, favorite_game.winner_seed)
        )
        winner = underdog_game
        loser = favorite_game

    if game.winner_previous_game:
        game.winner_previous_game = winner
    game.winner_name = winner.winner_name
    game.winner_seed = winner.winner_seed
    game.winner_region = winner.winner_region
    if game.loser_previous_game:
        game.loser_previous_game = loser
    game.loser_name = loser.winner_name
    game.loser_seed = loser.winner_seed
    game.loser_region = loser.winner_region


def wipe_game_recursively(game):
    if game.round == Schema.ROUND_OF_64:
        if game.loser_seed < game.winner_seed:
            favorite_name = game.loser_name
            favorite_seed = game.loser_seed
            favorite_region = game.loser_region
            game.loser_name = game.winner_name
            game.loser_seed = game.winner_seed
            game.loser_region = game.winner_region
            game.winner_name = favorite_name
            game.winner_seed = favorite_seed
            game.winner_region = favorite_region
        return

    wipe_game_recursively(game.winner_previous_game)
    wipe_game_recursively(game.loser_previous_game)
    game.winner_name = game.winner_seed = game.winner_region = game.loser_name = game.loser_seed = game.loser_region = ''


def deep_copy(game):
    if game is None:
        return None


    clone_game = Game(
        game.round,
        game.loser_name,
        game.loser_seed,
        game.loser_region,
        game.winner_name,
        game.winner_seed,
        game.winner_region,
        None,
        None,
        None
    )

    winner_previous_game = deep_copy(game.winner_previous_game)
    if winner_previous_game:
        clone_game.winner_previous_game = winner_previous_game
        clone_game.winner_previous_game.next_game = clone_game

    loser_previous_game = deep_copy(game.loser_previous_game)
    if loser_previous_game:
        clone_game.loser_previous_game = loser_previous_game
        clone_game.loser_previous_game.next_game = clone_game

    return clone_game


def get_round_games(bracket_root, round):
    to_search = deque([bracket_root])
    collected = []
    while True:
        try:
            next_game = to_search.pop()
            if next_game.round == round:
                collected.append(next_game)
                continue
            if next_game.winner_previous_game:
                to_search.append(next_game.winner_previous_game)
            if next_game.loser_previous_game:
                to_search.append(next_game.loser_previous_game)
        except IndexError:
            break
    return collected


def create_decorated_string(team, ranking, color):
    decorated_string = "%s [%s] " % (team, ranking)
    padding = '_' * (JUSTIFICATION_SIZE - len(decorated_string) - len(TEAM_HEADER))
    color_string = COLOR_FORMAT % color
    decorated_string = TEAM_HEADER + color_string + decorated_string + COLOR_ENDING + padding
    return decorated_string


def determine_print_color(team_name, previous_round_winners):
    if not previous_round_winners:
        return NEUTRAL_COLOR
    if team_name in previous_round_winners:
        return WIN_COLOR
    return LOSS_COLOR


def print_as_bracket(bracket_root, actual_root=None):
    validate_championship_game(bracket_root)

    # Initialize your output with the national champion (not represented in the dataset)
    national_championship_winner = []
    if actual_root:
        national_championship_winner = [actual_root.winner_name]
    national_champion_color = determine_print_color(bracket_root.winner_name, national_championship_winner)

    national_champion_output = []
    national_champion_output.extend([EMPTY_SPACE] * (pow(2, Schema.ROUND_ORDER[Schema.NATIONAL_CHAMPIONSHIP]) - 1))
    national_champion_output.append(create_decorated_string(bracket_root.winner_name, bracket_root.winner_seed, national_champion_color))
    national_champion_output.extend([EMPTY_SPACE] * (pow(2, Schema.ROUND_ORDER[Schema.NATIONAL_CHAMPIONSHIP]) - 1))
    total_output = [national_champion_output]

    # Walk the graph from national championship game out to the branches (round of 64)
    current_games = [bracket_root]
    next_games = []
    while current_games:
        # Used to match up predicted with actual.  I know this is slow, but whatever
        previous_round_winners = []
        if actual_root and Schema.ROUND_ORDER[current_games[0].round] > 1:
            previous_round = current_games[0].winner_previous_game.round
            previous_round_winners = [game.winner_name for game in get_round_games(actual_root, previous_round)]

        my_output = deque([])
        for game in current_games:
            winner_color = determine_print_color(game.winner_name, previous_round_winners)
            my_output.append(create_decorated_string(game.winner_name, game.winner_seed, winner_color))
            my_output.extend([EMPTY_SPACE] * (pow(2, Schema.ROUND_ORDER[game.round]) - 1))
            if game.winner_previous_game:
                next_games.append(game.winner_previous_game)

            loser_color = determine_print_color(game.loser_name, previous_round_winners)
            my_output.append(create_decorated_string(game.loser_name, game.loser_seed, loser_color))
            my_output.extend([EMPTY_SPACE] * (pow(2, Schema.ROUND_ORDER[game.round]) - 1))
            if game.loser_previous_game:
                next_games.append(game.loser_previous_game)

        # Perform a shift so they align in a diamond-ish shape
        my_output.rotate(pow(2, Schema.ROUND_ORDER[game.round] - 1) - 1)
        total_output.append(my_output)

        # Move onto the next list of games (if there are any in the previous round)
        current_games = next_games
        next_games = []

    # Write vertical representation out horizontally (assumes all vertical slices are same size)
    for index in range(len(total_output[0])):
        horizontal_slice = ''
        for inner_index in range(len(total_output)):
            horizontal_slice += total_output[inner_index][index]
        log(DEBUG, horizontal_slice)


def validate_championship_game(game):
    if game.round != Schema.NATIONAL_CHAMPIONSHIP:
        raise ValueError("Expecting national championship game, but found %s" % game.round)


def get_national_championship_game(games):
    championship_games = [game for game in games if game.round == Schema.NATIONAL_CHAMPIONSHIP]
    if len(championship_games) != 1:
        raise ValueError("Found more than one national championship game")
    return championship_games[0]


def build_year_mapping_for(data_filename):
    year_mapping = {}
    with open(data_filename, 'r') as data_file:
        reader = csv.reader(data_file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        headers = next(reader, None)
        for game in reader:
            year = game[Schema.YEAR]
            if year not in year_mapping:
                year_mapping[year] = []
            year_mapping[year].append(game)
    return year_mapping


def main(data_file, years, strategies):
    year_mapping = build_year_mapping_for(data_file)

    aggregated_strategies = dict((strategy.name, {}) for strategy in strategies)
    for year in years:
        # Check that our data set has the required number of games at least
        log(INFO, "%s\n----" % year)
        tournament_games = year_mapping[str(year)]
        if len(tournament_games) < 63:
            raise ValueError("Incomplete year set for year %d (%d entries)" % (year, len(tournament_games)))

        # Construct game objects from the input file
        games = []
        season_rankings = {}
        for entry in tournament_games:
            if entry[Schema.WINS] != '0' or entry[Schema.LOSSES] != '1':
                raise ValueError("Encountered unexpected win/loss entry %s" % entry)
            if entry[Schema.ROUND] == Schema.OPENING_ROUND:
                continue
            game = Game(
                entry[Schema.ROUND].strip(),
                entry[Schema.TEAM].strip(), entry[Schema.SEED].strip(), entry[Schema.REGION].strip(),
                entry[Schema.OPPONENT].strip(), entry[Schema.OPPONENT_SEED].strip(), entry[Schema.OPPONENT_REGION].strip(),
                None, None, None
            )
            games.append(game)

            if game.winner_name in season_rankings and season_rankings[game.winner_name] != entry[Schema.OPPONENT_RANKING]:
                raise ValueError("Ranking mismatch %s has %d and %d" % (game.winner_name, season_rankings[game.winner_name], entry[Schema.OPPONENT_RANKING]))
            season_rankings[game.winner_name] = entry[Schema.OPPONENT_RANKING]
            if game.loser_name in season_rankings and season_rankings[game.loser_name] != entry[Schema.RANKING]:
                raise ValueError("Ranking mismatch %s has %d and %d" % (game.winner_name, season_rankings[game.winner_name], entry[Schema.RANKING]))
            season_rankings[game.loser_name] = entry[Schema.RANKING]

        # Build out the doubly-linked tree (beginning at the root)
        for game in games:
            for other_game in games:
                if Schema.ROUND_ORDER[other_game.round] == (Schema.ROUND_ORDER[game.round] + 1):
                    if other_game.winner_name == game.winner_name:
                        game.next_game = other_game
                        game.next_game.winner_previous_game = game
                    if other_game.loser_name == game.winner_name:
                        game.next_game = other_game
                        game.next_game.loser_previous_game = game

        log(DEBUG, "------------------- ACTUAL BRACKET ----------------".center(JUSTIFICATION_SIZE * len(Schema.ROUND_ORDER)))
        bracket_root = get_national_championship_game(games)
        print_as_bracket(bracket_root)

        for strategy in strategies:
            log(DEBUG, "------------------- PREDICTED BRACKET ----------------".center(JUSTIFICATION_SIZE * len(Schema.ROUND_ORDER)))
            predicted_games = deep_copy(bracket_root)
            wipe_game_recursively(predicted_games)
            random.seed(strategy.seed)
            perform_predictions(predicted_games, strategy, season_rankings)
            print_as_bracket(predicted_games, bracket_root)
            aggregated_strategies[strategy.name][year] = compute_score(predicted_games, bracket_root, strategy)
        log(INFO, "")

    for strategy, years in aggregated_strategies.items():
        log(INFO, strategy)
        log(INFO, '-' * len(strategy))

        max_with_year = max(years.items(), key=operator.itemgetter(1))
        min_with_year = min(years.items(), key=operator.itemgetter(1))
        mean = statistics.mean(years.values())
        median = statistics.median(years.values())
        log(INFO,
                "\tMAX: %d (%d)\tMIN: %d (%d)\tMEDIAN: %2.1f\tMEAN: %2.1f\n" %
                (
                    max_with_year[1], max_with_year[0],
                    min_with_year[1], min_with_year[0],
                    median, mean
                )
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="The data file to read in", required=True)
    parser.add_argument("-y", "--years", help="A list of years to perform the simulation on", nargs='+', type=int, required=True)
    args = parser.parse_args()
    main(args.file, args.years, DefaultStrategies.STRATEGIES)
