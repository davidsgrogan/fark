#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import sys
import copy

import numpy as np
import matplotlib.pyplot as plt

import scoring
import agents

seed = 1234
random.seed(seed)
np.random.seed(seed)

goal_score = 10000

players = [agents.TurnLimitPlayer(400),
           agents.HeuristicPlayer()]
num_players = len(players)
winners = [0] * num_players
NUM_GAMES = 5000

turn_scores_banked = []

for x in range(NUM_GAMES):
  if x < 2500:
    turn = -1
  else:
    turn = 0
  scores = [0] * num_players
  while max(scores) < goal_score:
    turn = (turn + 1) % num_players
    dice_left = 6
    turn_points = 0
    print(f"\nplayer {turn} starts rolling, scores are ", scores)
    while True:
      roll_result = np.random.randint(1, 7, dice_left)
      print("roll", sorted(roll_result))
      scoring_options = scoring.get_score_options(roll_result)
      if len(scoring_options) == 0:
        print ("that's a womp")
        turn_scores_banked.append(0)
        break
      state = {
        # Rotate scores so that yours is first
        "scores": scores[turn:] + scores[:turn],
        "turn_points": turn_points,
        "just_rolled": roll_result,
        "scoring_options": scoring_options,
        }
      num_dice_to_score = players[turn].GetAction(state)
      if num_dice_to_score == -1:
        # Dude wants to bank and end his turn.
        turn_points += max(scoring_options.values())
        scores[turn] += turn_points
        print (f"He banked his {turn_points} points")
        turn_scores_banked.append(turn_points)
        break
      assert num_dice_to_score in scoring_options
      dice_left -= num_dice_to_score
      turn_points += scoring_options[num_dice_to_score]
      if dice_left == 0:
        print(f"{turn_points} AND ROLLING")
        dice_left = 6
      else:
        print("turn points are now", turn_points)
  print (f"\nplayer {turn} won, with {scores[turn]} points")
  winners[turn] += 1

print ("winner counts are", winners)