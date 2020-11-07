#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 22:37:01 2020

@author: dgrogan
"""


import scipy.interpolate
import numpy as np

a = np.array(range(0, 8)).reshape(-1, 2)

x_gold = np.array([
  [0, 0],
  [0, 1],
  [1, 0],
  [1, 1],
  [2, 0],
  [2, 1],
  [3, 0],
  [3, 1],
  ])
y_gold = np.array(range(0, 8)).reshape(8,)

y = a.flatten()
assert (y == y_gold).all()

# https://stackoverflow.com/a/49071149/681070
def cartprod(*arrays):
  N = len(arrays)
  return np.transpose(np.meshgrid(*arrays, indexing='ij'), 
                      np.roll(np.arange(N + 1), -1)).reshape(-1, N)

ind = np.indices(a.shape, sparse=True)
ind = [row.flatten() for row in ind]
dogs = cartprod(*ind)
assert (x_gold == dogs).all()

assert scipy.interpolate.griddata(dogs, y, np.array([1.5, 1])) == 4
assert scipy.interpolate.griddata(dogs, y, np.array([1.5, 0.5])) == 3.5
assert scipy.interpolate.griddata(dogs, y, np.array([0, 0])) == 0

b = a**2
def make_X(multi_dimensional):
  ind = np.indices(multi_dimensional.shape, sparse=True)
  ind = [row.flatten() for row in ind]
  return cartprod(*ind)

def make_y(multi_dimensional):
  return multi_dimensional.flatten()

def make_X2(multi_dimensional):
  ind = np.indices(multi_dimensional.shape, sparse=True)
  ind = [row.flatten() for row in ind]
  return ind

def make_y2(multi_dimensional):
  return multi_dimensional.flatten()

assert scipy.interpolate.griddata(make_X(b), make_y(
  b), np.array([0, 0])) == 0

assert (scipy.interpolate.RegularGridInterpolator(make_X2(b), b)([[0, 0], [2.5, 0.5]]
                                                                 ) == [0, 31.5]).all()