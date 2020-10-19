#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import numpy as np
import sys
import copy

import scoring
import agents

seed = 12
random.seed(seed)
np.random.seed(seed)

goal_score = 5000

players = [agents.TurnLimitPlayer(300), agents.TurnLimitPlayer(500),
           agents.TurnLimitPlayer(800)]
num_players = len(players)
scores = [0] * num_players

turn = -1
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