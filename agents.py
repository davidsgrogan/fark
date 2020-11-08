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
import scipy.interpolate
import numpy as np

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

class TwoPlayerLinearInteropolation:
  def __init__(self, goal_score):
    self.goal_score = goal_score
    self.resolution_store_every = 100

    W_file_name = f'W_goal{goal_score}_res{self.resolution_store_every}.pkl'
    with open(W_file_name, 'rb') as f:
      self.W = pickle.load(f)

    self.grid_points = self.make_points(self.W)
    self.max_interpolable_score = self.goal_score - self.resolution_store_every
    self.interpolator = scipy.interpolate.RegularGridInterpolator(self.grid_points, self.W)

  @staticmethod
  def h(n):
    if n == 0:
      return 6
    return n
 
  def make_points(self, multi_dimensional):
    ind = np.indices(multi_dimensional.shape, sparse=True)
    ind = [row.flatten() * self.resolution_store_every for row in ind[0:3]]
    ind.append(np.array(range(1, 7)))
    return ind

  def GetProb(self, scores, turn_points, dice_remaining):
    #print("GetProb called with", locals())
    assert dice_remaining > 0 and dice_remaining < 7
    if scores[0] + turn_points >= self.goal_score:
      return 1
    if scores[1] >= self.goal_score:
      return 0
    nn_scores = [min(x, self.max_interpolable_score) for x in scores]
    turn_points = min(turn_points, self.max_interpolable_score)
    to_ret = self.interpolator([*nn_scores, turn_points, dice_remaining])
    #print("  returning", to_ret)
    return float(to_ret)

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
  interp_player = TwoPlayerLinearInteropolation(2000)
  assert interp_player.max_interpolable_score == 1900, interp_player.max_interpolable_score

  # print(interp_player.grid_points)
  W = interp_player.W
  string = "Starting with a score of 50 has to be better than starting with 0 %f < %f" % (interp_player.GetProb((0, 0), 0, 6), interp_player.GetProb((50, 0), 0, 6))
  assert interp_player.GetProb((0, 0), 0, 6) < interp_player.GetProb((50, 0), 0, 6), string
  print(string)
  assert interp_player.GetProb((0, 0), 0, 6) == W[0, 0, 0, 5]
  string = "First roll of the game is a 50, chances of winning should be > 50: %f" % interp_player.GetProb((0, 0), 50, 5)
  assert interp_player.GetProb((0, 0), 50, 5) > 0.5, string
  print(string)
  manual = (W[0, 0, 0, 4] + W[0, 0, 1, 4]) / 2
  assert abs(interp_player.GetProb((0, 0), 50, 5) - manual) < 0.0001, "%f == %f" % (interp_player.GetProb((0, 0), 50, 5), manual)

  p_to_test = interp_player.GetProb((250, 350), 450, 3)
  manual =  W[2, 3, 4, 2]
  manual += W[2, 3, 5, 2]
  manual += W[2, 4, 4, 2]
  manual += W[2, 4, 5, 2]
  manual += W[3, 3, 4, 2]
  manual += W[3, 3, 5, 2]
  manual += W[3, 4, 4, 2]
  manual += W[3, 4, 5, 2]
  manual /= 8
  assert abs(manual - p_to_test) < 0.0001

  value_player = TwoPlayerValueIterated(2000)
  state = {
      "scores": [0, 0],
      "turn_points": 1000,
      "just_rolled": [4, 5],
      "scoring_options": {1: 50},
  }
  action = value_player.GetAction(state)
  assert action == -1, action

  state = {
      "scores": [0, 0],
      "turn_points": 50,
      "just_rolled": [2, 2, 3, 3, 4, 5],
      "scoring_options": {1: 50},
  }
  action = value_player.GetAction(state)
  assert action == 1, action

  print(interp_player.GetProb((500, 500), 200, 3))
  print(value_player.GetProb((500, 500), 200, 3))
