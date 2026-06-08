K = 32

def expected(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

def update(winner_elo, loser_elo):
    new_winner = round(winner_elo + K * (1 - expected(winner_elo, loser_elo)))
    new_loser = round(loser_elo + K * (0 - expected(loser_elo, winner_elo)))
    return new_winner, new_loser
