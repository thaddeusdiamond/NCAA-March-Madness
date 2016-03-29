"""
Has the schema for the related Game By Game.csv file.  This file was extracted
from the data at:
http://www.hoopstournament.net/Database.html
"""

class Schema:
    (
        YEAR,
        TEAM,
        CURRENT_CONFERENCE,
        ACTUAL_CONFERENCE,
        TEAM_STATE,
        TEAM_CITY,
        COACH,
        RANKING,
        SEED,
        RPI,
        SCORE,
        OPPONENT_SCORE,
        SCORE_BUCKET,
        OPPONENT_SCORE_BUCKET,
        OPPONENT,
        OVERTIMES,
        ROUND,
        REGION,
        SEASON_WINS,
        SEASON_LOSSES,
        AUTOMATIC_AT_LARGE,
        OPPONENT_CURRENT_CONFERENCE,
        OPPONENT_ACTUAL_CONFERENCE,
        OPPONENT_STATE,
        OPPONENT_CITY,
        OPPONENT_RANKING,
        OPPONENT_SEED,
        OPPONENT_RPI,
        OPPONENT_REGION,
        LOCATION_CITY,
        LOCATION_STATE,
        DAY_OF_WEEK,
        DATE,
        DECADE,
        WINS,
        LOSSES
    ) = range(36)

    EAST = "East"
    MIDWEST = "Midwest"
    SOUTH = "South"
    WEST = "West"

    REGIONS = {
        EAST    : 0,
        MIDWEST : 1,
        SOUTH   : 2,
        WEST    : 3
    }

    OPENING_ROUND = "Opening Round"
    ROUND_OF_64 = "Round of 64"
    ROUND_OF_32 = "Round of 32"
    SWEET_SIXTEEN = "Sweet Sixteen"
    ELITE_EIGHT = "Elite Eight"
    NATIONAL_SEMIFINALS = "National Semifinals"
    NATIONAL_CHAMPIONSHIP = "National Championship"

    ROUND_ORDER = {
        OPENING_ROUND           : 0,
        ROUND_OF_64             : 1,
        ROUND_OF_32             : 2,
        SWEET_SIXTEEN           : 3,
        ELITE_EIGHT             : 4,
        NATIONAL_SEMIFINALS     : 5,
        NATIONAL_CHAMPIONSHIP   : 6
    }

    ORDERED_ROUNDS = dict((value, key) for (key, value) in ROUND_ORDER.items())
