#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "maxim"


import numbers
import random

import numpy as np
import skimage.transform
import skimage.util
from tflearn import ImageAugmentation


class ImageAugmentationPlus(ImageAugmentation):
  def apply(self, batch):
    return super(ImageAugmentationPlus, self).apply(np.copy(batch))

  def add_random_scale(self, downscale_limit=1.0, upscale_limit=1.0, fix_aspect_ratio=False):
    if isinstance(downscale_limit, numbers.Number):
      downscale_limit = (downscale_limit, downscale_limit)
    downscale_limit = t_min(t_max(downscale_limit, (0, 0)), (1, 1))

    if isinstance(upscale_limit, numbers.Number):
      upscale_limit = (upscale_limit, upscale_limit)
    upscale_limit = t_max(upscale_limit, (1, 1))

    if downscale_limit != (1, 1) or upscale_limit != (1, 1):
      self.methods.append(self._random_scale)
      self.args.append([downscale_limit, upscale_limit, fix_aspect_ratio])

  def add_random_swirl(self, strength_limit=1.0, radius_limit=100.0):
    self.methods.append(self._random_swirl)
    self.args.append([strength_limit, radius_limit])

  def _random_scale(self, batch, downscale_limit, upscale_limit, fix_aspect_ratio):
    for i in range(len(batch)):
      if bool(random.getrandbits(1)):
        image = batch[i]
        scale = np.random.uniform(downscale_limit, upscale_limit)
        if fix_aspect_ratio:
          scale[1] = scale[0]
        if scale[0] < 1 or scale[1] < 1:
          image = skimage.transform.rescale(image, scale=t_min(scale, (1, 1)), preserve_range=True)
          image = pad_to_shape(image, batch[i].shape)
        if scale[0] > 1 or scale[1] > 1:
          image = skimage.transform.rescale(image, scale=t_max(scale, (1, 1)), preserve_range=True)
          image = crop_to_shape(image, batch[i].shape)
        batch[i] = image
    return batch

  def _random_swirl(self, batch, strength_limit, radius_limit):
    for i in range(len(batch)):
      if bool(random.getrandbits(1)):
        image = batch[i]
        strength = np.random.uniform(0, strength_limit)
        radius = np.random.uniform(0, radius_limit)
        if strength > 0 and radius > 0:
          image = skimage.transform.swirl(image, strength=strength, radius=radius, rotation=0, preserve_range=True)
        batch[i] = image
    return batch


def t_min(lhs, rhs):
  return min(lhs[0], rhs[0]), min(lhs[1], rhs[1])


def t_max(lhs, rhs):
  return max(lhs[0], rhs[0]), max(lhs[1], rhs[1])


def pad_to_shape(image, target_shape):
  current_shape = image.shape
  diff = (target_shape[0] - current_shape[0], target_shape[1] - current_shape[1])
  side = (diff[0] / 2, diff[1] / 2)
  pad_width = ((side[0], diff[0]-side[0]), (side[1], diff[1]-side[1]), (0, 0))
  return skimage.util.pad(image, pad_width=pad_width, mode='constant')


def crop_to_shape(image, target_shape):
  current_shape = image.shape
  diff = (current_shape[0] - target_shape[0], current_shape[1] - target_shape[1])
  side = (diff[0] / 2, diff[1] / 2)
  crop_width = ((side[0], diff[0]-side[0]), (side[1], diff[1]-side[1]), (0, 0))
  return skimage.util.crop(image, crop_width=crop_width)
