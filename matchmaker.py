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

    def add_tickets(self, tickets):
        self.pool += tickets

    def process_tick(self):
        self.matchmake()
        self.check_games()
        if self.tick % 50 == 0:
            self.fix_incomplete()
        self.tick += 1

    def matchmake(self):
        pool_copy = self.pool.copy()
        self.incomplete_lobbies.sort(reverse=False, key=lambda x: x.creation_tick)
        for ticket in pool_copy:
            ticket_matched = False

            for lobby in self.incomplete_lobbies:
                if (len(ticket.players) + lobby.t1_party_counter > 5) and (len(ticket.players) + lobby.t2_party_counter > 5):
                    continue

                mult = 1
                if self.tick - lobby.creation_tick > 200:
                    mult = 8
                elif self.tick - lobby.creation_tick > 150:
                    mult = 5
                elif self.tick - lobby.creation_tick > 100:
                    mult = 3
                elif self.tick - lobby.creation_tick > 50:
                    mult = 2

                delta_mu = abs(ticket.mu - lobby.tickets[0].mu)
                delta_toxic = abs(ticket.toxicity - lobby.tickets[0].toxicity)

                if delta_mu <= (self.max_mu_diff * mult) and (
                        delta_toxic <= (self.max_toxic_diff * mult)) and (
                        lobby.players_count <= (10 - len(ticket.players))):
                # if delta_mu <= self.max_mu_diff and lobby.players_count <= (10 - len(ticket.players)):
                    lobby.add_ticket(ticket)
                    ticket_matched = True
                    self.pool.remove(ticket)

                    if lobby.players_count == 10:
                        lobby.fill_teams()
                        lobby.balance_teams(self.rs)
                        game_duration = self.match_times[np.random.randint(0, 50)]
                        game = common.Game(lobby, self.tick, game_duration)
                        self.incomplete_lobbies.remove(lobby)
                        self.playing.append(game)
                    break

            if not ticket_matched:
                new_lobby = common.Lobby(self.tick)
                new_lobby.add_ticket(ticket)
                self.pool.remove(ticket)
                self.incomplete_lobbies.append(new_lobby)

    def fix_incomplete(self):
        to_fix = []
        for lobby in self.incomplete_lobbies:
            if self.tick - lobby.creation_tick > 200:
                to_fix.append(lobby)
        if len(to_fix) > 0:
            to_delete_ind = []
            for i in range(0, len(to_fix) - 1):
                if i in to_delete_ind:
                    continue
                lobby1 = to_fix[i]
                for j in range(i + 1, len(to_fix)):
                    if j in to_delete_ind or i == j:
                        continue
                    lobby2 = to_fix[j]
                    delta_mu = abs(lobby1.tickets[0].mu - lobby2.tickets[0].mu)
                    delta_toxic = abs(lobby1.tickets[0].toxicity - lobby2.tickets[0].toxicity)
                    if delta_mu <= (self.max_mu_diff * 8) and (delta_toxic <= (self.max_toxic_diff * 8)):
                        if len(lobby1.tickets) > len(lobby2.tickets):
                            to_delete_ind.append(j)
                        else:
                            to_delete_ind.append(i)
                    if i in to_delete_ind:
                        break

            for i in range(0, len(to_fix)):
                if i in to_delete_ind:
                    tickets = to_fix[i].tickets
                    self.incomplete_lobbies.remove(to_fix[i])
                    self.pool += tickets
                elif len(to_fix[i].tickets) > 1:
                    tickets = to_fix[i].tickets[1::]
                    remaining_ticket = to_fix[i].tickets[0]
                    to_fix[i].tickets = []
                    to_fix[i].team1 = []
                    to_fix[i].team2 = []
                    to_fix[i].players_count = 0
                    to_fix[i].t1_party_counter = 0
                    to_fix[i].t2_party_counter = 0
                    to_fix[i].add_ticket(remaining_ticket)
                    self.pool += tickets

    def check_games(self):
        for game in self.playing:
            if self.tick >= game.end_tick:
                radiant_win_predict = self.rs.win_probability(game.team1, game.team2)
                radiant_win = np.random.choice([False, True])

                radiant_mu = 0
                dire_mu = 0
                radiant_sigma = 0
                dire_sigma = 0
                radiant_players = []
                dire_players = []

                for player in game.team1:
                    radiant_players.append(player.rating)
                    radiant_mu += player.rating.mu / len(game.team1)
                    radiant_sigma += player.rating.sigma / len(game.team1)

                for player in game.team2:
                    dire_players.append(player.rating)
                    dire_mu += player.rating.mu / len(game.team2)
                    dire_sigma += player.rating.sigma / len(game.team2)

                radiant_party = ""
                dire_party = ""

                for ticket in game.lobby.team1:
                    radiant_party += str(len(ticket.players))
                for ticket in game.lobby.team2:
                    dire_party += str(len(ticket.players))

                mult = 1

                if game.start_tick - game.lobby.creation_tick > 200:
                    mult = 8
                elif game.start_tick - game.lobby.creation_tick > 150:
                    mult = 5
                elif game.start_tick - game.lobby.creation_tick > 100:
                    mult = 3
                elif game.start_tick - game.lobby.creation_tick > 50:
                    mult = 2

                game_info = pd.DataFrame(data={"waiting_time": game.waiting_time, "radiant_win": radiant_win,
                                               "radiant_win_chance": radiant_win_predict,
                                               "radiant_party": radiant_party, "dire_party": dire_party,
                                               "radiant_mu": radiant_mu, "radiant_sigma": radiant_sigma,
                                               "dire_mu": dire_mu, "dire_sigma": dire_sigma, "diff_mult": mult,
                                               "account_id_1": game.team1[0].account_id,
                                               "account_id_2": game.team1[1].account_id,
                                               "account_id_3": game.team1[2].account_id,
                                               "account_id_4": game.team1[3].account_id,
                                               "account_id_5": game.team1[4].account_id,
                                               "account_id_6": game.team2[0].account_id,
                                               "account_id_7": game.team2[1].account_id,
                                               "account_id_8": game.team2[2].account_id,
                                               "account_id_9": game.team2[3].account_id,
                                               "account_id_10": game.team2[4].account_id}, index=[0])

                game_info.to_csv("data/test_2_party_toxic_mult_lobbyfix.csv", mode="a", index=False, header=False)

                if radiant_win:  # 0 - победитель
                    updated_radiant, updated_dire = self.rs.system.rate([radiant_players, dire_players], ranks=[0, 1])
                else:
                    updated_radiant, updated_dire = self.rs.system.rate([radiant_players, dire_players], ranks=[1, 0])

                for i, player in enumerate(game.team1):
                    player.rating = updated_radiant[i]
                for i, player in enumerate(game.team2):
                    player.rating = updated_dire[i]

                played = game.end_game()
                new_tickets = []
                for ticket in played:
                    new_tickets.append(common.Ticket(ticket.players))

                self.pool += random.sample(new_tickets, int(len(new_tickets) / 2))
                self.playing.remove(game)
