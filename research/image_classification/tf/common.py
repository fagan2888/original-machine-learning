#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "maxim"


import tensorflow as tf


def log(*msg):
  import datetime
  print '[%s]' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ' '.join([str(it) for it in msg])


def dict_to_str(d):
  def smart_str(val):
    if type(val) == float:
      return "%.5f" % val
    return repr(val)

  return '{%s}' % ', '.join(['%s: %s' % (repr(k), smart_str(d[k])) for k in sorted(d.keys())])


def zip_longest(list1, list2):
  len1 = len(list1)
  len2 = len(list2)
  for i in xrange(max(len1, len2)):
    yield (list1[i % len1], list2[i % len2])


def is_gpu():
  from tensorflow.python.client import device_lib
  local_devices = device_lib.list_local_devices()
  return len([x for x in local_devices if x.device_type == 'GPU']) > 0

is_gpu_available = is_gpu()


def total_params():
  total_parameters = 0
  for variable in tf.trainable_variables():
      shape = variable.get_shape()
      variable_parameters = 1
      for dim in shape:
          variable_parameters *= dim.value
      total_parameters += variable_parameters
  return total_parameters


def reset_data_set(data_set):
  data_set._epochs_completed = 0
  data_set._index_in_epoch = 0
  return data_set


def train(data_sets, model, **hyper_params):
  train_set = reset_data_set(data_sets.train)
  val_set = data_sets.validation
  test_set = data_sets.test

  epochs = hyper_params['epochs']
  batch_size = hyper_params['batch_size']

  optimizer, cost, accuracy, init = model.build_graph(**hyper_params)
  log("Total parameters: %dk" % (total_params() / 1000))
  log("Hyper params: %s" % dict_to_str(hyper_params))

  with tf.Session() as session:
    log("Start training")
    session.run(init)

    step = 0
    max_val_acc = 0
    while True:
      batch_x, batch_y = train_set.next_batch(batch_size)
      session.run(optimizer, feed_dict=model.feed_dict(images=batch_x, labels=batch_y, **hyper_params))
      step += 1
      iteration = step * batch_size

      loss, acc, name = None, None, None
      if is_gpu_available:
        if iteration % train_set.num_examples < batch_size:
          loss, acc = session.run([cost, accuracy], feed_dict=model.feed_dict(data_set=val_set))
          name = "validation_accuracy"
          max_val_acc = max(max_val_acc, acc)
      elif step % 100 == 0:
        loss, acc = session.run([cost, accuracy], feed_dict=model.feed_dict(data_set=val_set))
        name = "validation_accuracy"
      elif step % 10 == 0:
        loss, acc = session.run([cost, accuracy], feed_dict=model.feed_dict(images=batch_x, labels=batch_y))
        name = "train_accuracy"
      if loss is not None and acc is not None and name is not None:
        log("epoch %d, iteration %6d: loss=%.6f, %s=%.4f" % (train_set.epochs_completed, iteration, loss, name, acc))

      if iteration >= train_set.num_examples * epochs:
        break

    if hyper_params.get('evaluate_test', False):
      test_acc = session.run(accuracy, feed_dict=model.feed_dict(data_set=test_set))
      log("Final test_accuracy=%.4f" % test_acc)

    return max_val_acc
