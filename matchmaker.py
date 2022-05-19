import random

import common
import pandas as pd
import numpy as np


class Matchmaker:
    def __init__(self, rs: common.RatingSystem, max_mu_diff, max_toxic_diff):
        self.rs = rs
        self.pool = []
        self.tick = 0
        self.max_mu_diff = max_mu_diff
        self.max_toxic_diff = max_toxic_diff
        self.incomplete_lobbies = []
        self.playing = []
        values = np.random.normal(456, 142, size=(1, 50))
        self.match_times = []
        for elem in values[0]:
            self.match_times.append(round(abs(elem)))

    def add_players(self, players):
        self.pool += players

    def process_tick(self):
        self.matchmake()
        self.check_games()
        self.tick += 1

    def matchmake(self):
        for player in self.pool:
            player_matched = False

            for lobby in self.incomplete_lobbies:
                delta_mu = abs(player.rating.mu - lobby.players[0].rating.mu)
                delta_toxic = abs(player.rating.mu - lobby.players[0].rating.mu)

                if delta_mu <= self.max_mu_diff and delta_toxic <= self.max_toxic_diff and len(lobby.players) < 10:
                    lobby.add_player(player)
                    player_matched = True
                    self.pool.remove(player)

                    if len(lobby.players) == 10:
                        lobby.fill_teams()
                        lobby.balance_teams(self.rs)
                        game_duration = self.match_times[np.random.randint(0, 50)]
                        game = common.Game(lobby, self.tick, game_duration)
                        self.incomplete_lobbies.remove(lobby)
                        self.playing.append(game)
                    break

            if not player_matched:
                new_lobby = common.Lobby(self.tick)
                new_lobby.add_player(player)
                self.pool.remove(player)
                self.incomplete_lobbies.append(new_lobby)

    def check_games(self):
        for game in self.playing:
            if self.tick >= game.end_tick:
                radiant_win_predict = self.rs.win_probability(game.lobby.team1, game.lobby.team2)
                radiant_win = np.random.choice([False, True])

                radiant_mu = 0
                dire_mu = 0
                radiant_sigma = 0
                dire_sigma = 0
                radiant_players = []
                dire_players = []

                for player in game.lobby.team1:
                    radiant_players.append(player.rating)
                    radiant_mu += player.rating.mu / len(game.lobby.team1)
                    radiant_sigma += player.rating.sigma / len(game.lobby.team1)

                for player in game.lobby.team2:
                    dire_players.append(player.rating)
                    dire_mu += player.rating.mu / len(game.lobby.team2)
                    dire_sigma += player.rating.sigma / len(game.lobby.team2)

                game_info = pd.DataFrame(data={"waiting_time": game.waiting_time, "radiant_win": radiant_win,
                                               "radiant_win_chance": radiant_win_predict,
                                               "radiant_mu": radiant_mu, "radiant_sigma": radiant_sigma,
                                               "dire_mu": dire_mu, "dire_sigma": dire_sigma,
                                               "account_id_1": game.lobby.team1[0].account_id,
                                               "account_id_2": game.lobby.team1[1].account_id,
                                               "account_id_3": game.lobby.team1[2].account_id,
                                               "account_id_4": game.lobby.team1[3].account_id,
                                               "account_id_5": game.lobby.team1[4].account_id,
                                               "account_id_6": game.lobby.team2[0].account_id,
                                               "account_id_7": game.lobby.team2[1].account_id,
                                               "account_id_8": game.lobby.team2[2].account_id,
                                               "account_id_9": game.lobby.team2[3].account_id,
                                               "account_id_10": game.lobby.team2[4].account_id}, index=[0])

                game_info.to_csv("data/generated_match_data_2.csv", mode="a", index=False, header=False)

                if radiant_win:  # 0 - победитель
                    updated_radiant, updated_dire = self.rs.system.rate([radiant_players, dire_players], ranks=[0, 1])
                else:
                    updated_radiant, updated_dire = self.rs.system.rate([radiant_players, dire_players], ranks=[1, 0])

                for i, player in enumerate(game.lobby.team1):
                    player.rating = updated_radiant[i]
                for i, player in enumerate(game.lobby.team2):
                    player.rating = updated_dire[i]

                self.pool += random.sample(game.end_game(), 5)
                self.playing.remove(game)
