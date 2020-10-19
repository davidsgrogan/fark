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
    if turn_points > self.turn_limit:
      return -1
    return max(scoring_options.keys())