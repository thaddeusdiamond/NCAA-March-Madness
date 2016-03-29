"""
Describes a strategy for picking the winner of a game.
"""

from schema import Schema

class Strategy:

    def __init__(self, name, seed, favorite_bias, protected_function):
        self.name = name
        self.seed = seed
        self.favorite_bias = favorite_bias
        self.protected_function = protected_function

class DefaultStrategies:

    @staticmethod
    def exponential_before_sweet_sixteen(base, round):
        if Schema.ROUND_ORDER[round] > Schema.ROUND_ORDER[Schema.SWEET_SIXTEEN]:
            return 0
        return pow(base, Schema.ROUND_ORDER[Schema.SWEET_SIXTEEN] - Schema.ROUND_ORDER[round])

    __LUCKY_SEED = 0x9272015

    STRATEGIES = [
        # Simple strategies: all win, all lose, coin toss
        Strategy('All Favorites', __LUCKY_SEED, 1.0, None),
        Strategy('All Underdogs', __LUCKY_SEED, 0.0, None),
        Strategy('Coin Toss', __LUCKY_SEED, 0.5, None),

        # Complex, during each round protect a set of "chosen ones"
        Strategy('50/50 w/POW(2) Protection', __LUCKY_SEED, 0.5, lambda round: DefaultStrategies.exponential_before_sweet_sixteen(2, round)),
        Strategy('75% w/POW(2) Protection', __LUCKY_SEED, 0.75, lambda round: DefaultStrategies.exponential_before_sweet_sixteen(2, round)),
        Strategy('50/50 w/POW(3) Protection', __LUCKY_SEED, 0.5, lambda round: DefaultStrategies.exponential_before_sweet_sixteen(3, round)),
        Strategy('75% w/POW(3) Protection', __LUCKY_SEED, 0.75, lambda round: DefaultStrategies.exponential_before_sweet_sixteen(3, round))
    ]
