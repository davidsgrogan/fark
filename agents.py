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


class TurnLimitPlayer:
  def __init__(self, turn_limit):
    self.turn_limit = turn_limit

  def GetAction(self, state):
    scoring_options = state["scoring_options"]
    turn_points = state["turn_points"] + max(scoring_options.values())
    num_dice_rolled = len(state["just_rolled"])
    if num_dice_rolled in scoring_options:
      # We always re-roll 6 dice
      return num_dice_rolled
    if turn_points > self.turn_limit:
      return -1
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
  @staticmethod
  def h(n):
    if n == 0:
      return 6
    return n
  
  @staticmethod
  def WinProbability(my_score, opp_score, num_dice_you_can_roll, turn_points):
    pass
  
  def GetBestActionAndValue(self, state):
    assert len(state["scores"]) == 2, state["scores"]
    goal_score = 10000
    scoring_options = state["scoring_options"]
    num_dice_rolled = len(state["just_rolled"])
    scores = state["scores"]
    turn_points = state["turn_points"]
    
    # Extract the best action from the value function
    
    if scores[0] + turn_points + max(scoring_options.values()) > goal_score:
      # We just won.
      return -1
    score_if_I_bank = scores[0] + turn_points + max(scoring_options.values())
    WinProbability = self.WinProbability
    bank_u = 1 - WinProbability(scores[1], score_if_I_bank, 6, 0)
    best_u = -1
    best_action = -10
    for action, score in scoring_options.items():
      u = WinProbability(scores[0], scores[1], self.h(num_dice_rolled - action),
                         turn_points + score)
      if u > best_u:
        best_u = u
        best_action = action
    if bank_u > best_u:
      return -1
    return best_action
  
    def GetAction(self, state):
      return self.GetBestActionAndValue(state)[0]