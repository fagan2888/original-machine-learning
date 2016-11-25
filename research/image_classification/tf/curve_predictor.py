#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
from image_classification.tf.base_io import BaseIO
from image_classification.tf.log import log
from image_classification.tf.util import dict_to_str

__author__ = "maxim"


class CurvePredictorIO(BaseIO):
  def __init__(self, predictor, log_level=1, **params):
    super(CurvePredictorIO, self).__init__(log_level, **params)
    self.predictor = predictor

  def load(self):
    directory = self.load_dir
    if not directory is None:
      destination = os.path.join(directory, 'curve-data.xjson')
      if os.path.exists(destination):
        data = CurvePredictorIO._load_dict(destination)
        self.debug('Loaded curve data: %s from %s' % (dict_to_str(data), destination))
        self.predictor.import_from(data)
        return

    self.predictor.import_from({})

  def save(self):
    directory = self.save_dir
    if not CurvePredictorIO._prepare(directory):
      return

    destination = os.path.join(directory, 'curve-data.xjson')
    with open(destination, 'w') as file_:
      file_.write(dict_to_str(self.predictor.export_to()))
      self.debug('Curve data saved to %s' % destination)


class BaseCurvePredictor(object):
  def __init__(self, **params):
    self._x = np.array([])
    self._y = np.array([])
    self._burn_in = params.get('burn_in', 10)
    self._min_input_size = params.get('min_input_size', 3)

    self._curve_io = CurvePredictorIO(**params)
    self._curve_io.load()

  @property
  def curves_number(self):
    return self._x.shape[0]

  @property
  def curve_length(self):
    if self.curves_number == 0:
      return 0
    return self._x.shape[1]

  def add_curve(self, curve, value):
    assert len(curve.shape) == 1

    curve = curve.reshape(1, -1)
    value = value.reshape(1)

    if self.curves_number == 0:
      self._x = curve
      self._y = value
    else:
      self._x = np.concatenate([self._x, curve], axis=0)
      self._y = np.concatenate([self._y, value], axis=0)

    log('Adding curve. Current data shape: ', self._x.shape)
    self._curve_io.save()

  def predict(self, curve):
    raise NotImplementedError()

  def stop_condition(self):
    raise NotImplementedError()

  def result_metric(self):
    raise NotImplementedError()

  def import_from(self, data):
    self._x = np.array(data.get('x', []))
    self._y = np.array(data.get('y', []))

  def export_to(self):
    return {
      'x': self._x.tolist(),
      'y': self._y.tolist(),
    }


class LinearCurvePredictor(BaseCurvePredictor):
  def __init__(self, value_limit, **params):
    super(LinearCurvePredictor, self).__init__(**params)
    self._value_limit = value_limit
    self._model = {}

  def add_curve(self, curve, value):
    super(LinearCurvePredictor, self).add_curve(curve, value)
    self._model = {}

  def predict(self, curve):
    curve = np.array(curve)
    size = curve.shape[0]
    if self.curves_number < self._burn_in or size < self._min_input_size or size >= self.curve_length:
      return None

    w, error = self._build_model(size)
    value_prediction = curve[:size].dot(w)
    log('Prediction for curve %s: %.4f (error=%.4f)' % (str(curve), value_prediction, error))
    return value_prediction-error, value_prediction, value_prediction+error

  def stop_condition(self):
    def condition(curve):
      interval = self.predict(curve)
      if interval:
        _, _, right = interval
        if right < self._value_limit:
          return True
      return False
    return condition

  def result_metric(self):
    def metric(curve):
      if len(curve) < self.curve_length:
        _, expected, _ = self.predict(curve)
        return expected
      return max(curve)
    return metric

  def _build_model(self, size):
    result = self._model.get(size)
    if result is None:
      w = self._compute_matrix(size)
      error = self._std_error(w)
      result = (w, error)
      self._model[size] = result
    return result

  def _compute_matrix(self, size):
    x = self._x[:,:size]
    y = self._y
    return np.linalg.pinv(x.T.dot(x)).dot(x.T).dot(y)

  def _std_error(self, w):
    size = w.shape[0]
    x = self._x[:,:size]
    y = self._y
    predictions = x.dot(w)
    return np.sqrt(np.mean((predictions - y)**2))
