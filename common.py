import numpy as np
import pandas as pd
import trueskill
import itertools
import math


class RatingSystem:
    def __init__(self):
        self.system = trueskill.TrueSkill(draw_probability=0)

    def create_rating(self, mu, sigma):
        return self.system.create_rating(mu=mu, sigma=sigma)

    def win_probability(self, t1, t2):  # Возвращает шанс на победу первой команды
        team1 = []
        team2 = []
        for player in t1:
            team1.append(player.rating)
        for player in t2:
            team2.append(player.rating)

        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
        size = len(team1) + len(team2)
        denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
        return self.system.cdf(delta_mu / denom)


class Player:
    def __init__(self, account_id, mu, sigma, toxicity, rs: RatingSystem):
        self.account_id = account_id
        self.toxicity = toxicity
        self.rating = rs.create_rating(mu=mu, sigma=sigma)

    def __repr__(self):
        return "<id=" + str(self.account_id) + ", tox=" + str(self.toxicity) + ", mu=" + str(self.rating.mu) +\
               ", sigma=" + str(self.rating.sigma) + "> "

    def __str__(self):
        return self.__repr__()


class Lobby:
    def __init__(self, creation_tick):
        self.team1 = []
        self.team2 = []
        self.players = []
        self.creation_tick = creation_tick

    def add_player(self, player):
        self.players.append(player)

    def fill_teams(self):
        self.players.sort(reverse=True, key=lambda x: x.rating.mu)
        for i, player in enumerate(self.players):
            if i % 2 == 0:
                self.team1.append(player)
            else:
                self.team2.append(player)

    def balance_teams(self, rs: RatingSystem):
        best_win = abs(rs.win_probability(self.team1, self.team2) - 0.5)
        i = 0
        while best_win >= 0.01 and i < 20:
            i += 1
            new_wins = []
            new_teams = []
            for j in range(len(self.team1)):
                for l in range(len(self.team2)):
                    copy1 = self.team1.copy()
                    copy2 = self.team2.copy()
                    buff = copy1[j]
                    copy1[j] = copy2[l]
                    copy2[l] = buff
                    new_wins.append(abs(rs.win_probability(copy1, copy2) - 0.5))
                    new_teams.append([copy1, copy2])

            min_win = 1
            min_j = math.factorial(len(self.team1)) + 1
            for j, win in enumerate(new_wins):
                if win < min_win:
                    min_win = win
                    min_j = j

            if min_win < best_win:
                best_win = min_win
                self.team1 = new_teams[min_j][0]
                self.team2 = new_teams[min_j][1]


class Game:
    def __init__(self, lobby: Lobby, start_tick, game_duration):
        self.lobby = lobby
        self.end_tick = start_tick + game_duration
        self.start_tick = start_tick
        self.waiting_time = (start_tick - lobby.creation_tick)/2

    def end_game(self):
        return self.lobby.team1 + self.lobby.team2

    def generate_game_info(self, tick):
        return pd.DataFrame(data={"waiting_tine": self.waiting_time,}, index=[0])
