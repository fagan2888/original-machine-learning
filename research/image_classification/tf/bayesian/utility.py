#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "maxim"


import math
import numpy as np
from scipy import stats


class BaseUtility(object):
  def __init__(self, points, values, **params):
    super(BaseUtility, self).__init__()
    self.points = np.array(points)
    self.values = np.array(values)

    if len(self.points.shape) == 1:
      self.points = self.points.reshape(-1, 1)
    assert len(self.points.shape) == 2
    assert len(self.values.shape) == 1
    assert self.points.shape[0] == self.values.shape[0]

    self.dimension = self.points.shape[1]
    self.iteration = params.get('iteration', self.points.shape[0])

  def compute_values(self, batch):
    pass


class BaseGaussianUtility(BaseUtility):
  def __init__(self, points, values, kernel, mu_prior=0, **params):
    super(BaseGaussianUtility, self).__init__(points, values, **params)
    self.kernel = kernel
    self.mu_prior = mu_prior

    kernel_matrix = self.kernel.compute(self.points)
    self.k_inv = np.linalg.pinv(kernel_matrix)
    self.k_inv_f = np.dot(self.k_inv, (self.values-self.mu_prior))

  def mean_and_std(self, batch):
    assert len(batch.shape) == 2

    batch = np.array(batch)
    k_star = np.swapaxes(self.kernel.compute(self.points, batch), 0, 1)
    k_star_star = self.kernel.id(batch)

    mu_star = self.mu_prior + np.dot(k_star, self.k_inv_f)

    t_star = np.dot(self.k_inv, k_star.T)
    t_star = np.einsum('ij,ji->i', k_star, t_star)
    sigma_star = k_star_star - t_star

    return mu_star, sigma_star


class ProbabilityOfImprovement(BaseGaussianUtility):
  def __init__(self, points, values, kernel, mu_prior=0, **params):
    super(ProbabilityOfImprovement, self).__init__(points, values, kernel, mu_prior, **params)
    self.epsilon = params.get('epsilon', 1e-8)
    self.max_value = np.max(self.values)

  def compute_values(self, batch):
    mu, sigma = self.mean_and_std(batch)
    z = (mu - self.max_value - self.epsilon) / sigma
    cdf = stats.norm.cdf(z)
    cdf[np.abs(mu - self.max_value) < self.epsilon] = 0.0
    return cdf


class UpperConfidenceBound(BaseGaussianUtility):
  def __init__(self, points, values, kernel, mu_prior=0, **params):
    super(UpperConfidenceBound, self).__init__(points, values, kernel, mu_prior, **params)
    delta = params.get('delta', 0.5)
    self.beta = np.sqrt(2 * np.log(self.dimension * self.iteration**2 * math.pi**2 / (6 * delta)))

  def compute_values(self, batch):
    mu, sigma = self.mean_and_std(batch)
    return mu + self.beta * sigma
