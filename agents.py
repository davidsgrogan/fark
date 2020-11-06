#!/usr/bin/env python3
# -*- coding: utf-8 -*-

    # state = {
    #   # Rotate scores so that yours is first
    #   "scores": scores[turn:] + scores[:turn],
    #   "turn_points": turn_points,
    #   "just_rolled": roll_result,
    #   "scoring_options": scoring_options,
    #   }
    # num_dice_to_score = players[turn].GetAction(state)

import pickle

class TurnLimitPlayer:
  def __init__(self, turn_limit):
    self.turn_limit = turn_limit

  def GetAction(self, state):
    scoring_options = state["scoring_options"]
    turn_points = state["turn_points"] + max(scoring_options.values())
    num_dice_rolled = len(state["just_rolled"])
    if turn_points > self.turn_limit:
      return -1
    if num_dice_rolled in scoring_options:
      # We always re-roll 6 dice
      return num_dice_rolled
    if num_dice_rolled - max(scoring_options.keys()) == 1:
      # We don't roll 1 die
      return -1
    return max(scoring_options.keys())

class HeuristicPlayer:
  def GetAction(self, state):
    scoring_options = state["scoring_options"]
    num_dice_rolled = len(state["just_rolled"])
    scores = state["scores"]
    if num_dice_rolled in scoring_options:
      # We always re-roll 6 dice
      return num_dice_rolled

    way_behind = False
    points_ahead = scores[0] - max(scores[1:])
    if points_ahead > 1500:
      turn_limit = 350
    elif points_ahead > -2000:
      turn_limit = 500
    else:
      way_behind = True
      turn_limit = 600

    turn_points = state["turn_points"] + max(scoring_options.values())
    if turn_points > turn_limit:
      return -1
    if num_dice_rolled - max(scoring_options.keys()) == 1:
      # We don't roll 1 die
      return -1
    return max(scoring_options.keys())

class TwoPlayerValueIterated:
  def __init__(self, goal_score):
    self.goal_score = goal_score
    self.resolution_store_every = 50

    W_file_name = f'W_goal{goal_score}_res{self.resolution_store_every}.pkl'
    with open(W_file_name, 'rb') as f:
      self.W = pickle.load(f)

  def r2i(self, raw):
    index = int(raw / self.resolution_store_every)
  #  index, remainder = divmod(raw, resolution_store_every)
  #  assert remainder == 0, (raw, resolution_store_every)
    return index

  def GetProb(self, scores, turn_points, dice_remaining):
    #print("GetProb called with", locals())
    assert dice_remaining > 0 and dice_remaining < 7
    if scores[0] + turn_points >= self.goal_score:
      return 1
    if scores[1] >= self.goal_score:
      return 0
    to_ret = self.W[self.r2i(scores[0]),
                  self.r2i(scores[1]),
                  self.r2i(turn_points),
                  dice_remaining - 1]
    #print("  returning", to_ret)
    return to_ret
  @staticmethod
  def h(n):
    if n == 0:
      return 6
    return n
 
  def GetAction(self, state):
    assert len(state["scores"]) == 2, state["scores"]
    scoring_options = state["scoring_options"]
    num_dice_rolled = len(state["just_rolled"])
    scores = state["scores"]
    turn_points = state["turn_points"]
    
    # Extract the best action from the value function
    
    if scores[0] + turn_points + max(scoring_options.values()) >= self.goal_score:
      # We just won.
      return -1
    score_if_I_bank = scores[0] + turn_points + max(scoring_options.values())
    #print(score_if_I_bank)
    WinProbability = self.GetProb
    bank_u = 1 - WinProbability((scores[1], score_if_I_bank), 0, 6)
    #print(bank_u)
    best_roll_u = -1
    best_action = -10
    for action, score in scoring_options.items():
    #  print(action, score)
      u = WinProbability((scores[0], scores[1]), turn_points + score,
                         self.h(num_dice_rolled - action))
      #print(u)
      if u > best_roll_u:
        best_roll_u = u
        best_action = action
    #print("best_roll_u =", best_roll_u)
    if bank_u >= best_roll_u:
      return -1
    return best_action

if __name__ == "__main__":
  value_player = TwoPlayerValueIterated(2000)
  state = {
      "scores": [0, 0],
      "turn_points": 1000,
      "just_rolled": [4, 5],
      "scoring_options": {1: 50},
  }
  action = value_player.GetAction(state)
  print(action)
