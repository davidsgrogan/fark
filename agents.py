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