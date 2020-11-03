#!/usr/bin/env python3

import numpy as np
import scoring
import copy
import pickle
from multiprocessing import Pool
from multiprocessing import shared_memory

goal_score = 600
resolution_store_every = 50
diff_threshold = 0.0002
parallel = False

num_score_entries, remainder = divmod(goal_score, resolution_store_every)
assert remainder == 0, (goal_score, resolution_store_every)
W_shape = (num_score_entries, num_score_entries, num_score_entries, 6)

def r2i(raw):
  index = int(raw / resolution_store_every)
#  index, remainder = divmod(raw, resolution_store_every)
#  assert remainder == 0, (raw, resolution_store_every)
  return index

def GetProb(scores, turn_points, dice_remaining, local_W):
  assert dice_remaining > 0 and dice_remaining < 7
  if scores[0] + turn_points >= goal_score:
    return 1
  if scores[1] >= goal_score:
    return 0
  return local_W[r2i(scores[0]), r2i(scores[1]), r2i(turn_points), dice_remaining - 1]

def SetProb(scores, turn_points, dice_remaining, this_W, local_W):
  assert dice_remaining > 0 and dice_remaining < 7
  # print("SetProb got", scores, turn_points, dice_remaining, this_W)
  local_W[r2i(scores[0]), r2i(scores[1]), r2i(turn_points), dice_remaining - 1] = this_W


# Speedups, in order:
# Record results to compare against optimizations
# Do L-shaped convergence so that we don't have to run over the
# already-converged pieces
# Multiprocess
  # Can sync up the matrix from one level higher after each of its iterations
  # so you don't have to do locking
# Can do scores just 6000 apart, clamping the other parts
# Can do resolution of 100 for lower score states

def DoOne(my_score, your_score, turn_points, num_dice, shm_name):
  # iterate over the distribution of scoring options for this number of
  # dice. there will be a sequence of options mapped to a probability

  local_W = W  
  if parallel:
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    local_W = np.ndarray(W.shape, dtype=W.dtype, buffer=existing_shm.buf)
  # print("Top of DoOne for", my_score, your_score, turn_points, num_dice)
  interest = False
  if my_score == 0 and your_score == 50 and turn_points == 0 and num_dice == 1:
    # print("Starting the interesting one")
    interest = True
    interest = False
  this_W_if_roll = 0
  for options, probability in (
      scoring.distribution_over_scoring_options(num_dice).items()):
    if options == ():
      # Womped
      if interest:
        val = 1 - GetProb((your_score, my_score), 0, 6, local_W)
        print(f"womp prob = {probability}, value = {val}")
      this_W_if_roll += probability * (
        1 - GetProb((your_score, my_score, local_W), 0, 6, local_W))
      continue
    best_prob = 0
    for option in options:
      dice_to_roll = num_dice - option[0]
      if dice_to_roll == 0:
        dice_to_roll = 6
      prob = GetProb((my_score, your_score), turn_points + option[1],
                     dice_to_roll, local_W)
      if interest:
        pass
        print(f"for option {option}, value = {prob}, probability = {probability}")
      best_prob = max(prob, best_prob)
    this_W_if_roll += probability * best_prob
  this_W = this_W_if_roll
  if turn_points != 0:
    # We have the option to hold
    hold_prob = 1 - GetProb((your_score, my_score + turn_points), 0, 6, local_W)
    this_W = max(hold_prob, this_W)
#              if this_W == hold_prob and k > 20:
#                print("Want to hold at", my_score, your_score, turn_points, num_dice)
  return this_W

def main():
  global diff
  global W
  W = np.zeros(W_shape)
  diff = 1
  k = 0
  shm = shared_memory.SharedMemory(create=True, size=W.nbytes)
  W = np.ndarray(W_shape, dtype=W.dtype, buffer=shm.buf)
  if parallel:
    pool = Pool(6)
    print("starting %d processes" % pool._processes)
  while diff > diff_threshold:
    if k == 2:
      pass
      # break
    k += 1
    print("Starting iteration", k)
    W_old = copy.deepcopy(W)
    for my_score in reversed(range(0, goal_score, resolution_store_every)):
      for your_score in reversed(range(0, goal_score, resolution_store_every)):
        #print(f"doing my_score = {my_score}, your_score = {your_score}")
        for turn_points in range(0, goal_score - my_score, resolution_store_every):
          if parallel:
            probs = pool.starmap(DoOne, zip(6*[my_score], 6*[your_score], 6*[turn_points], range(1,7), 6*[shm.name]))
            assert len(probs) == 6
            for num_dice, this_W in enumerate(probs):
              SetProb((my_score, your_score), turn_points, num_dice + 1, this_W, W)
          else:
            for num_dice in range(1, 7):
              this_W = DoOne(my_score, your_score, turn_points, num_dice, "unused")
              SetProb((my_score, your_score), turn_points, num_dice, this_W, W)
    diff = np.max(np.abs(W - W_old))
    biggest_cell = np.max(W)
    print(f"After, biggest cell difference is {diff}. Biggest " +
          f"is {biggest_cell}")

  with open(f'W_goal{goal_score}_res{resolution_store_every}_parallel.pkl', 'wb') as f:
    pickle.dump(W, f, 4)
#%%
  p_to_test = GetProb((100, 0), 100, 1, W)
  # hold
  hold = 1 - GetProb((0, 200), 0, 6, W)
  # Roll 1
  roll_1 = GetProb((100, 0), 200, 6, W)
  # Roll 5
  roll_5 = GetProb((100, 0), 150, 6, W)
  # Womp
  womp = 1 - GetProb((0, 100), 0, 6, W)
  print(p_to_test, "p_to_test from matrix")
  manual = (2/3) * womp + (1/6) * roll_1 + (1/6) * roll_5
  print(manual, "manual")
  print(hold, "hold")
  assert abs(p_to_test - manual) < diff_threshold
  with open(f'W_goal{goal_score}_res{resolution_store_every}.pkl', 'rb') as f:
    W2 = pickle.load(f)
    biggest_diff = np.max(np.abs((W-W2)))
    print("biggest difference between L and regular:", biggest_diff)
    assert biggest_diff < 2 * diff_threshold
#%%    
if __name__ == "__main__":
  main()