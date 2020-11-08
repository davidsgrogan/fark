#!/usr/bin/env python3

import numpy as np
import scoring
import copy
import pickle
import sys
import math
from multiprocessing import Pool
from multiprocessing import shared_memory

goal_score = 4000
resolution_store_every = 100
diff_threshold = 0.0002
#parallel = False
parallel = True

num_score_entries, remainder = divmod(goal_score, resolution_store_every)
assert remainder == 0, (goal_score, resolution_store_every)
W_shape = (num_score_entries, num_score_entries, num_score_entries, 6)

def r2i(raw):
  index = math.floor(raw / resolution_store_every)
#  index, remainder = divmod(raw, resolution_store_every)
#  assert remainder == 0, (raw, resolution_store_every)
  return index

# each row is
# my_score, your_score, turn_points, dice_remaining
# 300, 500, 250, 4
# 200, 150, 0, 2
def GetIndices(nparr):
  nparr[:, 0:3] = nparr[:, 0:3] / resolution_store_every
  nparr[:, 3] = nparr[:, 3] - 1

def GetProb(scores, turn_points, dice_remaining, local_W):
  assert dice_remaining > 0 and dice_remaining < 7
  if scores[0] + turn_points >= goal_score:
    return 1
  if scores[1] >= goal_score:
    return 0
  return local_W[r2i(scores[0]),
                 r2i(scores[1]),
                 r2i(turn_points),
                 dice_remaining - 1]

def SetProb(scores, turn_points, dice_remaining, this_W, local_W):
  assert dice_remaining > 0 and dice_remaining < 7
  # print("SetProb got", scores, turn_points, dice_remaining, this_W)
  local_W[r2i(scores[0]),
          r2i(scores[1]),
          r2i(turn_points),
          dice_remaining - 1] = this_W

# Speedups, in order:
# Multiprocess
  # Either smarter chunks with fewer function calls
    # Write out a matrix of matrices and see how to divide it up
    # Retrieve the W cells you need for a roll all in one swoop, not in a loop
  # Or locks
# Can do scores just 6000 apart, clamping the other parts
# Can do resolution of 100 for lower score states

def DoTurnPointsRange(my_score, your_score, turn_points, shm_name):
  local_W = W
  existing_shm = shared_memory.SharedMemory(name=shm_name)
  local_W = np.ndarray(W.shape, dtype=W.dtype, buffer=existing_shm.buf)
  results = []
  for num_dice in range(1, 7):
    if CanSkip(turn_points, num_dice):
      results.append(0)
      continue
    this_W = DoOneDie(my_score, your_score, turn_points, num_dice, local_W)
    results.append(this_W)
  existing_shm.close()
  return results
  # return np.array(results).reshape((-1, 6))

def DoOneDie(my_score, your_score, turn_points, num_dice, local_W):
  # iterate over the distribution of scoring options for this number of
  # dice. there will be a sequence of options mapped to a probability

  # print("Top of DoOne for", my_score, your_score, turn_points, num_dice)
  interest = False
  if my_score == 0 and your_score == 50 and turn_points == 0 and num_dice == 1:
    # print("Starting the interesting one")
    interest = True
    interest = False
  this_W_if_roll = 0
  # each row is
  # my_score, your_score, turn_points, dice_remaining
  # 300, 500, 250, 4
  # 200, 150, 0, 2
  indices_to_request = []
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
        print(f"for option {option}, value = {prob}, probability = {probability}")
      best_prob = max(prob, best_prob)
    this_W_if_roll += probability * best_prob
  this_W = this_W_if_roll
  if turn_points != 0:
    # We have the option to hold
    hold_prob = 1 - GetProb((your_score, my_score + turn_points), 0, 6, local_W)
    this_W = max(hold_prob, this_W)
    if this_W == hold_prob and k > 20:
      pass
      # print("Want to hold at", my_score, your_score, turn_points, num_dice)
  return this_W

def CanSkip(turn_points, num_dice):
  if resolution_store_every == 50:
    if num_dice == 1 and turn_points < 250:
      return True
    if num_dice == 2 and turn_points < 200:
      return True
    if num_dice == 3 and turn_points < 150:
      return True
    if num_dice == 4 and turn_points < 100:
      # Can also skip 250, 300, 350
      return True
    if num_dice == 5 and (turn_points == 0 or (turn_points < 350 and
                                               turn_points > 100)):
      return True
    if num_dice == 6 and turn_points < 300 and turn_points > 0:
      return True
  if resolution_store_every == 100:
    if num_dice == 1 and turn_points < 200:
      return True
    if num_dice == 2 and turn_points < 150:
      return True
    if num_dice == 6 and turn_points < 300 and turn_points > 50:
      return True
  return False

def RunValueIteration():
  global diff
  global W
  global k
  W = np.zeros(W_shape)
  diff = 1
  k = 0
  shm = shared_memory.SharedMemory(create=True, size=W.nbytes)
  W = np.ndarray(W_shape, dtype=W.dtype, buffer=shm.buf)
  if parallel:
    pool = Pool()
    print("starting %d processes" % pool._processes)
  while diff > diff_threshold:
    if k == 2:
      pass
      # break
    k += 1
    W_old = copy.deepcopy(W)
    for my_score in reversed(range(0, goal_score, resolution_store_every)):
      for your_score in reversed(range(0, goal_score, resolution_store_every)):
        #print(f"doing my_score = {my_score}, your_score = {your_score}")
        if parallel:
          turn_points_range = range(0, goal_score - my_score, resolution_store_every)
          processes = len(turn_points_range)
          lists_of_probs = pool.starmap(DoTurnPointsRange,
                                        zip(processes*[my_score],
                                            processes*[your_score],
                                            turn_points_range,
                                            processes*[shm.name]))
          assert len(lists_of_probs) == processes
          # print ("Just got back a list length %d where each is a turn_point" % processes)
          for index, turn_points in enumerate(turn_points_range):
            W[r2i(my_score), r2i(your_score), r2i(turn_points),
              :] = lists_of_probs[index]
        else:
          for turn_points in range(0, goal_score - my_score, resolution_store_every):
            for num_dice in range(1, 7):
              if CanSkip(turn_points, num_dice):
                continue
              this_W = DoOneDie(my_score, your_score, turn_points, num_dice, W)
              SetProb((my_score, your_score), turn_points, num_dice, this_W, W)
    diff = np.max(np.abs(W - W_old))
    biggest_cell = np.max(W)
    print(f"After iteration {k}, biggest cell difference is {diff}. Biggest " +
          f"is {biggest_cell}")

  with open(f'W_goal{goal_score}_res{resolution_store_every}_parallel.pkl', 'wb') as f:
    pickle.dump(W, f, 4)

  RunTests()

  golden_file_name = f'W_goal{goal_score}_res{resolution_store_every}.pkl'
  with open(golden_file_name, 'rb') as f:
    W2 = pickle.load(f)
    biggest_diff = np.max(np.abs((W-W2)))
    print(f"biggest difference between what I just ran and {golden_file_name}:", biggest_diff)
    assert biggest_diff < 2 * diff_threshold
  shm.close()
  shm.unlink()

def RunTests(test_only=False):
  global W
  if test_only:
    golden_file_name = f'W_goal{goal_score}_res{resolution_store_every}.pkl'
    with open(golden_file_name, 'rb') as f:
      W = pickle.load(f)
    print("Running tests against", golden_file_name, "\n")

  p_to_test = GetProb((0, 0), 0, 6, W)
  assert p_to_test > 0.5, f"Your prob when you go first is {p_to_test}"
  print(f"Your prob when you go first is {p_to_test}")

  p_to_test = GetProb((0, 0), 50, 5, W)
  assert p_to_test > 0.45, p_to_test
  if resolution_store_every == 100:
    assert p_to_test == GetProb((0, 0), 0, 5, W)
  print("First roll of game is a 5, probability of winning =", p_to_test)

  p_to_test = GetProb((0, 50), 0, 6, W)
  assert p_to_test > 0.5, f"Other guy has a 50 point lead when you start, prob is {p_to_test}"
  if resolution_store_every == 50:
    assert p_to_test < GetProb((0, 0), 0, 6, W)
  print(f"Other guy has a 50 point lead when you start, prob is {p_to_test}")

  p_to_test = GetProb((0, 0), resolution_store_every, 5, W)
  hold = 1 - GetProb((0, resolution_store_every), 0, 6, W)
  print("")
  print(p_to_test, "p_to_test from matrix")
  print(hold, "hold\n")
  assert p_to_test > hold

  p_to_test = GetProb((100, 0), 400, 1, W)
  hold = 1 - GetProb((0, 500), 0, 6, W)
  roll_1 = GetProb((100, 0), 500, 6, W)
  roll_5 = GetProb((100, 0), 450, 6, W)
  womp = 1 - GetProb((0, 100), 0, 6, W)
  manual = (2/3) * womp + (1/6) * roll_1 + (1/6) * roll_5
  print(p_to_test, "p_to_test from matrix")
  print(manual, "manual")
  print(hold, "hold\n")
  assert abs(p_to_test - max(hold, manual)) < diff_threshold
  
  p_to_test = GetProb((100, 0), 400, 2, W)
  hold = 1 - GetProb((0, 500), 0, 6, W)
  roll_11 = GetProb((100, 0), 600, 6, W)
  roll_15 = GetProb((100, 0), 550, 6, W)
  roll_55 = GetProb((100, 0), 500, 6, W)
  roll_5 = GetProb((100, 0), 450, 1, W)
  roll_1 = GetProb((100, 0), 500, 1, W)
  womp = 1 - GetProb((0, 100), 0, 6, W)
  manual = (8/36)*roll_1 + (8/36)*roll_5 + (1/36)*roll_55 + (1/36)*roll_11 + (2/36)*roll_15 + (16/36)*womp
  print(p_to_test, "p_to_test from matrix")
  print(manual, "manual")
  print(hold, "hold\n")
  assert abs(p_to_test - max(hold, manual)) < diff_threshold

  if goal_score >= 1200:
    p_to_test = GetProb((0, 0), 1050, 1, W)
    hold = 1 - GetProb((0, 1050), 0, 6, W)
    roll_1 = GetProb((100, 0), 500, 6, W)
    roll_5 = GetProb((100, 0), 450, 6, W)
    womp = 1 - GetProb((0, 100), 0, 6, W)
    manual = (2/3) * womp + (1/6) * roll_1 + (1/6) * roll_5
    print(p_to_test, "p_to_test from matrix")
    print(manual, "manual")
    print(hold, "hold\n")
    assert abs(p_to_test - max(hold, manual)) < diff_threshold

if __name__ == "__main__":
  test_only = False
  if len(sys.argv) > 1 and sys.argv[1] == "test":
    print("running tests only")
    RunTests(test_only=True)
  else:
    RunValueIteration()
