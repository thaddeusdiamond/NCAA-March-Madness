"""
Data structures related to the in-memory processing of the bracket.  Represents
roughly the data read in using the Schema from schema.py
"""

from schema import Schema

class Game:
    """
    Represents a game played in the NCAA tournament.

    :param round:
    :param loser_name:
    :param loser_seed:
    :param loser_region:
    :param winner_name:
    :param winner_seed:
    :param winner_region:
    :param next_game:
    :param previous_games:
    """
    def __init__(self, round, loser_name, loser_seed, loser_region, winner_name, winner_seed, winner_region, next_game, winner_previous_game, loser_previous_game):
        self.round = round
        self.loser_name = loser_name
        self.loser_seed = int(loser_seed)
        self.loser_region = loser_region
        self.winner_name = winner_name
        self.winner_seed = int(winner_seed)
        self.winner_region = winner_region
        self.next_game = next_game
        self.winner_previous_game = winner_previous_game
        self.loser_previous_game = loser_previous_game

    def __str__(self):
        return "%s (%s): %s [%s] vs. %s [%s]" % (
            self.round,
            self.region,
            self.winner_name,
            self.winner_seed,
            self.loser_name,
            self.loser_seed
        )

    @staticmethod
    def compare(game_one, game_two):
        if game_one.round != game_two.round:
            return Schema.ROUND_ORDER[game_one.round] - Schema.ROUND_ORDER[game_two.round]
        if game_one.region != game_two.region:
            return 1 if game_one.region > game_two.region else -1
        return Schema.BRACKET_LOCATIONS[game_one.round][game_one.loser_seed] - Schema.BRACKET_LOCATIONS[game_two.round][game_two.loser_seed]

    @property
    def region(self):
        if self.loser_region == self.winner_region:
            return self.loser_region
        return "%s/%s" % (self.loser_region, self.winner_region)
