#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import copy
import itertools
import pickle

def remove_junk_die(orig_counts):
  counts = copy.deepcopy(orig_counts)
  for junk_die in [2, 3, 4, 6]:
    if counts[junk_die] < 3:
      del counts[junk_die]
  return counts

def count_em(dice_list):
  counts = collections.Counter(dice_list)
  orig_counts = len(counts)
  counts = remove_junk_die(counts)
  if len(counts) != orig_counts:
    return 0
  score = 0
#  print ("count_em for ", dice_list, "counts are", (counts))
  for die, count in counts.items():
    #print ("start of ", die, count, "score =", score)
    if count == 5:
      score += 2000
    elif count == 4:
      score += 1000
    elif count == 3:
      score += 100 * die
      if die == 1:
        score += 200 # 3 1s are 300
    elif die == 1:
      score += 100 * count
    elif die == 5:
      score += 50 * count
    else:
      assert(False), f"what did I get to?, die: {die} count:{count}"
#  print ("returning", score)
  return score

# inspired by https://codereview.stackexchange.com/questions/116051/scoring-solution-for-farkle-dice-game/116055
# returns a list of tuples where the tuple is (dice used, score)
def _get_score_options(roll_result):
  counts = collections.Counter(roll_result)
  # print(len(counts), "     ", counts)
  dice_rolled = len(roll_result)
  # The dice values are 1 based, not 0 based.
  # Do the special 6-dice combos first
  if dice_rolled == 6:
    # six of a kind
    if max(counts.values()) == 6:
      return {6: 3000}
    # straight
    if max(counts.values()) == 1:
      return {6: 1500}
    # 3 pairs
    if max(counts.values()) == 2 and len(counts) == 3:
      return {6: 1500}
    # 2 triplets
    if max(counts.values()) == 3 and len(counts) == 2:
      return {6: 2500}
    # 4 of a kind and a pair
    if len(counts) == 2 and max(counts.values()) == 4 and min(counts.values()) == 2:
      return {6: 1500}
  counts = remove_junk_die(counts)
#  print ("after removing junk die, counts = ", counts)
  if len(counts) == 0:
    return {}
  if dice_rolled == 1:
    if counts[1] == 1:
      return {1: 100}
    assert(counts[5] == 1)
    return {1: 50}
  # We didn't womp and have rolled 2 to 6 dice

  # This is embarrassingly stupid, but 2^6 is only 64.
  elements = sorted(counts.elements())
  # num dice kept -> score
  best = {}
  for num_to_keep in range(1, len(elements) + 1):
    best[num_to_keep] = 0
    for dice_to_score in itertools.combinations(elements, num_to_keep):
      # print("scoring ", dice_to_score)
      score = count_em(dice_to_score)
      best[num_to_keep] = max(best[num_to_keep], score)
    if best[num_to_keep] == 0:
      del best[num_to_keep]
  # print(best)
  if dice_rolled in best:
    return {dice_rolled: best[dice_rolled]}
  return best
#%%
def index_to_roll(idx, num_dice):
  assert idx < 6**num_dice, f"{idx, 6**num_dice}"
  roll = []
  mod = idx
  for i in reversed(range(0, num_dice)):
    (div, mod) = divmod(mod, 6**i)
#    print("div, mod is ", div, mod)
    roll.append(1+div)
  assert mod == 0, mod
  return roll
#%%
    
if __name__ == "__main__":
  tests = {
    range(1,7) : {6: 1500},
    (1, 2, 3, 3, 6) : {1: 100},
    (1, 4, 4, 4) : {4: 500},
    (1, 1, 1, 1, 1, 1): {6: 3000},
    (1, 1, 1, 1, 1): {5: 2000},
    (1, 1, 1, 1): {4: 1000},
    (5, 5, 5, 1): {4: 600},
    (1, 4, 4, 4, 5, 6): {1: 100, 2: 150, 3: 400, 4: 500, 5: 550},
    (1, 4, 4, 4, 5, 5): {6: 600},
    (1,): {1: 100},
    (3, 4): {},
    (2, 2, 3, 3, 4, 6): {},
    (1, 1, 1, 1, 4, 4): {6: 1500},
    (2, 2, 2, 5, 5, 5): {6: 2500},
    (3, 5, 6): {1: 50},
    (1, 4): {1: 100},
    (2, 3, 3, 4, 4): {},
    (1, 2, 2, 2): {4: 300},
    (1, 2, 2, 2, 6): {1: 100, 3: 200, 4: 300},
    (1, 1, 2, 3, 4, 5): {1: 100, 2: 200, 3: 250},
    (1, 1, 3, 5, 5, 6): {1: 100, 2: 200, 3: 250, 4: 300},
    (2, 2, 2, 2, 4): {4: 1000, 3: 200},
    (1, 1, 1, 1, 5, 6): {1: 100, 2: 200, 3: 300, 4: 1000, 5: 1050},
    (6,): {},
    (3, 3, 3): {3: 300},
    (3, 3, 3, 4): {3: 300},
    (1, 1, 2, 2, 2, 4): {1: 100, 2: 200, 3: 200, 4: 300, 5: 400},
    (1, 5): {2: 150}
    }
  for dice, expected in tests.items():
    assert _get_score_options(dice) == expected, (f'{dice} got\n{_get_score_options(dice)} ' +
                                                 f'was expecting \n{expected}')
  roll_to_options = {}
  num_dice_to_distribution = []
  for num_dice in range(1, 7):
    print(f"recording rolls for {num_dice} dice")
    options_to_counts = collections.defaultdict(int)
    num_rolls_for_this_number_of_dice = 6**num_dice
    for roll_index in range(num_rolls_for_this_number_of_dice):
      roll = index_to_roll(roll_index, num_dice)
      score_options_dict = _get_score_options(roll)
      roll_to_options[tuple(roll)] = score_options_dict
      options_as_tuple = tuple(score_options_dict.items())
      # print(roll)
      # print(score_options_dict)
      # print(options_as_tuple)
      # print("\n")
      options_to_counts[options_as_tuple] += 1
#    print(dict(options_to_counts))
    options_to_counts.update((k, v / num_rolls_for_this_number_of_dice) for k, v in options_to_counts.items())
    #print(sum(counts for tup, counts in options_to_counts.items()))
    num_dice_to_distribution.append(options_to_counts)
    
  #%%
  with open('num_dice_to_distribution.pkl', 'wb') as f:
    pickle.dump(num_dice_to_distribution, f, pickle.HIGHEST_PROTOCOL)
  with open('roll_to_options.pkl', 'wb') as f:
    pickle.dump(roll_to_options, f, pickle.HIGHEST_PROTOCOL)

distro = []
with open('num_dice_to_distribution.pkl', 'rb') as f:
  distro = pickle.load(f)
roll_to_options = {}
with open('roll_to_options.pkl', 'rb') as f:
  roll_to_options = pickle.load(f)

def distribution_over_scoring_options(num_dice):
  return distro[num_dice - 1]

def get_score_options(roll):
  return roll_to_options[tuple(roll)]
