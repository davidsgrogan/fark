#!/usr/bin/env python3

import numpy as np
import scoring
import copy
import pickle

goal_score = 3000
resolution_store_every = 50
num_score_entries, remainder = divmod(goal_score, resolution_store_every)
assert remainder == 0, (goal_score, resolution_store_every)

def r2i(raw):
  index = int(raw / resolution_store_every)
#  index, remainder = divmod(raw, resolution_store_every)
#  assert remainder == 0, (raw, resolution_store_every)
  return index

def GetProb(scores, turn_points, dice_remaining):
  assert dice_remaining > 0 and dice_remaining < 7
  if scores[0] + turn_points >= goal_score:
    return 1
  if scores[1] >= goal_score:
    return 0
  return W[r2i(scores[0]), r2i(scores[1]), r2i(turn_points), dice_remaining - 1]

def SetProb(scores, turn_points, dice_remaining, this_W):
  W[r2i(scores[0]), r2i(scores[1]), r2i(turn_points), dice_remaining - 1] = this_W


# Speedups, in order:
# Record results to compare against optimizations
# Multiprocess
# Can do scores just 6000 apart, clamping the other parts
# Can do resolution of 100 for lower score states

W = np.zeros((num_score_entries, num_score_entries, num_score_entries, 6))

def main():
  diff = 1
  k = 0
  diff_threshold = 0.0002
  while diff > diff_threshold:
  #for k in range(0, 25):
    k += 1
    print("\nStarting iteration", k)
    W_old = copy.deepcopy(W)
    for my_score in reversed(range(0, goal_score, resolution_store_every)):
      for your_score in reversed(range(0, goal_score, resolution_store_every)):
        #print(f"doing your_score = {your_score}, my_score = {my_score}")
        for turn_points in range(0, goal_score - my_score, resolution_store_every):
          for num_dice in range(1, 7):
            # iterate over the distribution of scoring options for this number of
            # dice. there will be a sequence of options mapped to a probability
            interest = False
            if my_score == 100 and your_score == 0 and turn_points == 100 and num_dice == 1:
              #print("Starting the interesting one")
              interest = True
            this_W_if_roll = 0
            for options, probability in (
                scoring.distribution_over_scoring_options(num_dice).items()):
              if options == ():
                # Womped
                if interest:
                  val = 1 - GetProb((your_score, my_score), 0, 6)
                  #print(f"womp prob = {probability}, value = {val}")
                this_W_if_roll += probability * (
                  1 - GetProb((your_score, my_score), 0, 6))
                continue
              best_prob = 0
              for option in options:
                dice_to_roll = num_dice - option[0]
                if dice_to_roll == 0:
                  dice_to_roll = 6
                prob = GetProb((my_score, your_score), turn_points + option[1],
                               dice_to_roll)
                if interest:
                  pass
#                  print(f"for option {option}, value = {prob}, probability = {probability}")
                best_prob = max(prob, best_prob)
              this_W_if_roll += probability * best_prob
            this_W = this_W_if_roll
            if turn_points != 0:
              # We have the option to hold
              hold_prob = 1 - GetProb((your_score, my_score + turn_points), 0, 6)
              this_W = max(hold_prob, this_W)
#              if this_W == hold_prob and k > 20:
#                print("Want to hold at", my_score, your_score, turn_points, num_dice)
            SetProb((my_score, your_score), turn_points, num_dice, this_W)
    diff = np.max(np.abs(W - W_old))
    biggest_cell = np.max(W)
    print(f"After, biggest cell difference is {diff}. Biggest " +
          f"is {biggest_cell}")
    # print(GetProb((550, 0), 0, 6))
    # print(GetProb((0, 550), 0, 1))
    
  with open(f'W_goal{goal_score}_res{resolution_store_every}.pkl', 'wb') as f:
    pickle.dump(W, f, 4)
#%%
  p_to_test = GetProb((100, 0), 100, 1)
  # hold
  hold = 1 - GetProb((0, 200), 0, 6)
  # Roll 1
  roll_1 = GetProb((100, 0), 200, 6)
  # Roll 5
  roll_5 = GetProb((100, 0), 150, 6)
  # Womp
  womp = 1 - GetProb((0, 100), 0, 6)
  print(p_to_test, "p_to_test from matrix")
  manual = (2/3) * womp + (1/6) * roll_1 + (1/6) * roll_5
  print(manual, "manual")
  print(hold, "hold")
  assert abs(p_to_test - manual) < diff_threshold
#%%    
if __name__ == "__main__":
  main()