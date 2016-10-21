#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "maxim"


from image_classification.tf.base_runner import BaseRunner
from image_classification.tf.util import *


class TensorflowRunner(BaseRunner):
  def __init__(self, model, log_level=1, **hyper_params):
    super(TensorflowRunner, self).__init__(log_level)
    self.model = model
    self.hyper_params = hyper_params
    self.session = None


  def prepare(self, **kwargs):
    self.session = kwargs['session']
    init, self.optimizer, self.cost, self.accuracy, self.misclassified_x, self.misclassified_y = self.model.build_graph(**self.hyper_params)
    self.info("Start training. Model size: %dk" % (self.model.params_num() / 1000))
    self.info("Hyper params: %s" % dict_to_str(self.hyper_params))
    self.session.run(init)


  def run_batch(self, batch_x, batch_y):
    self.session.run(self.optimizer, feed_dict=self.model.feed_dict(images=batch_x, labels=batch_y, mode='train'))


  def evaluate(self, batch_x, batch_y):
    cost, accuracy, x, y = self.session.run([self.cost, self.accuracy, self.misclassified_x, self.misclassified_y],
                                            feed_dict=self.model.feed_dict(images=batch_x, labels=batch_y, mode='test'))
    return {'cost': cost, 'accuracy': accuracy, 'misclassified_x': x, 'misclassified_y': y}