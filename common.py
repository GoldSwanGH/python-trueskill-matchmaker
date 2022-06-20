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


class Ticket:
    def __init__(self, players):
        self.players = players
        self.mu = 0
        self.toxicity = 0
        for player in players:
            self.mu += player.rating.mu
            self.toxicity += player.toxicity
        self.mu = self.mu / len(players)
        self.toxicity = self.toxicity / len(players)


class Lobby:
    def __init__(self, creation_tick):
        self.team1 = []
        self.team2 = []
        self.tickets = []
        self.players_count = 0
        self.creation_tick = creation_tick
        self.t1_party_counter = 0
        self.t2_party_counter = 0

    def add_ticket(self, ticket):
        if len(ticket.players) > 1:
            if len(ticket.players) + self.t1_party_counter <= 5:
                self.tickets.append(ticket)
                self.players_count += len(ticket.players)
                self.t1_party_counter += len(ticket.players)
            elif len(ticket.players) + self.t2_party_counter <= 5:
                self.tickets.append(ticket)
                self.players_count += len(ticket.players)
                self.t2_party_counter += len(ticket.players)
        elif len(ticket.players) == 1:
            self.tickets.append(ticket)
            self.players_count += len(ticket.players)

    def fill_teams(self):
        test = []
        for ticket in self.tickets:
            test.append("ticket mu: " + str(ticket.mu) + ", player mu: " + str(ticket.players[0].rating.mu))

        self.tickets.sort(reverse=True, key=lambda x: len(x.players))
        team1_count = 0
        team2_count = 0
        i = 0
        for ticket in self.tickets:
            if len(ticket.players) > 1:
                if (team1_count + len(ticket.players) <= 5) and (team1_count <= team2_count):
                    self.team1.append(ticket)
                    team1_count += len(ticket.players)
                    i += 1
                else:
                    self.team2.append(ticket)
                    team2_count += len(ticket.players)
                    i += 1

        self.tickets.sort(reverse=True, key=lambda x: x.mu)
        for ticket in self.tickets:
            if len(ticket.players) == 1:
                if team1_count <= team2_count:
                    self.team1.append(ticket)
                    team1_count += len(ticket.players)
                else:
                    self.team2.append(ticket)
                    team2_count += len(ticket.players)

    def tickets_to_players(self, tickets):
        players = []
        for ticket in tickets:
            for player in ticket.players:
                players.append(player)
        return players

    def balance_teams(self, rs: RatingSystem):
        best_win = abs(rs.win_probability(self.tickets_to_players(self.team1), self.tickets_to_players(self.team2)) - 0.5)
        i = 0
        while best_win >= 0.01 and i < 20:
            i += 1
            new_wins = []
            new_teams = []
            for ticket1 in self.team1:
                if len(ticket1.players) > 1:
                    continue
                for ticket2 in self.team2:
                    if len(ticket2.players) > 1:
                        continue
                    copy1 = self.team1.copy()
                    copy2 = self.team2.copy()
                    copy1.remove(ticket1)
                    copy2.remove(ticket2)
                    copy1.append(ticket2)
                    copy2.append(ticket1)
                    new_wins.append(abs(rs.win_probability(self.tickets_to_players(copy1), self.tickets_to_players(copy2)) - 0.5))
                    new_teams.append([copy1, copy2])

            min_win = 1
            min_j = 0
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
        self.team1 = lobby.tickets_to_players(lobby.team1)
        self.team2 = lobby.tickets_to_players(lobby.team2)

    def end_game(self):
        return self.lobby.team1 + self.lobby.team2
