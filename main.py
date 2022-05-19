import pandas as pd
import common
import matchmaker
import random
from statistics import mean

rating_system = common.RatingSystem()
players_data = pd.read_csv("data/players_data.csv")
max_mu_diff = 0.3
max_toxic_diff = 1000
mm = matchmaker.Matchmaker(rating_system, max_mu_diff, max_toxic_diff)
players = []

players_data.apply(lambda x: players.append(common.Player(account_id=x.account_id, mu=x.trueskill_mu,
                                                          sigma=x.trueskill_sigma, toxicity=x.toxicity,
                                                          rs=rating_system)), axis=1)

games_info = pd.DataFrame(columns=["waiting_time", "radiant_win", "radiant_win_chance", "radiant_mu", "radiant_sigma",
                                   "dire_mu", "dire_sigma", "account_id_1", "account_id_2", "account_id_3",
                                   "account_id_4", "account_id_5", "account_id_6", "account_id_7",
                                   "account_id_8", "account_id_9", "account_id_10"], index=[0])

games_info.dropna(inplace=True)
games_info.to_csv("data/generated_match_data_2.csv", index=False)

for i in range(5000):
    print("Tick " + str(i))
    mm.add_players(random.sample(players, 10))
    mm.process_tick()

incomplete_lobbies_waiting_times = []

for lobby in mm.incomplete_lobbies:
    incomplete_lobbies_waiting_times.append(5000 - lobby.creation_tick)

print("Медиана по времени ожидания матча для незаполненных лобби: " + str(mean(incomplete_lobbies_waiting_times)))
print("Незаполненных лобби: " + str(len(incomplete_lobbies_waiting_times)))
print("Минимальное время ожидания для незаполненных лобби: " + str(min(incomplete_lobbies_waiting_times)))
print("Максимальное время ожидания для незаполненных лобби: " + str(max(incomplete_lobbies_waiting_times)))
