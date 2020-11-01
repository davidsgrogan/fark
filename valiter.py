#!/usr/bin/env python3

import numpy as np
import scoring

goal_score = 10000
resolution_store_every = 50
num_score_entries, remainder = divmod(goal_score, resolution_store_every)
assert remainder == 0, (goal_score, resolution_store_every)

def r2i(raw):
  index, remainder = divmod(raw, resolution_store_every)
  assert remainder == 0, (raw, resolution_store_every)
  return index

def GetProb(scores, dice_remaining, turn_points):
  if scores[0] + turn_points > goal_score:
    return 1
  return W[r2i(scores[0]), r2i(scores[1]), r2i(turn_points), dice_remaining]

# Speedups, in order:
# Lower limit to 5000
# Profile, looks for blatant idiocy
# Multiprocess, but need to run a complete 5000 run with recorded results first
# to make sure the parallel algorithm matches
# Can limit turn_points to 10000 - my_score
# Can do scores just 6000 apart, clamping the other parts
# Can do resolution of 100 for lower score states


if __name__ == "__main__":
  W = np.zeros((num_score_entries, num_score_entries, num_score_entries, 7))
  for my_score in reversed(range(0, goal_score, resolution_store_every)):
    for your_score in reversed(range(0, goal_score, resolution_store_every)):
      print(f"doing your_score = {your_score}, my_score = {my_score}")
      for turn_points in range(0, goal_score, resolution_store_every):
        for num_dice in range(1, 7):
          # iterate over the distribution of scoring options for this number of
          # dice. there will be a sequence of options mapped to a probability
          this_W = 0
          for options, probability in scoring.distribution_over_scoring_options(num_dice).items():
            best_prob = 0
            for option in options:
              prob = GetProb((my_score, your_score), num_dice - option[0], turn_points + option[1])
              best_prob = max(prob, best_prob)
            this_W += probability * best_prob
        # Now do hold
        # Now do first turn

