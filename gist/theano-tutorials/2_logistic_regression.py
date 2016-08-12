#! /usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "maxim"

import theano
from theano import tensor as T
import numpy as np

import load

def floatX(X):
    return np.asarray(X, dtype=theano.config.floatX)

def init_weights(shape):
    return theano.shared(floatX(np.random.randn(*shape) * 0.01))

def model(X, w):
    return T.nnet.softmax(T.dot(X, w))

trainX, testX, trainY, testY = load.mnist(onehot=True)

X = T.fmatrix()
Y = T.fmatrix()

w = init_weights(shape=(trainX.shape[1], trainY.shape[1]))
print w.shape.eval()

# Probability p(y|x)
py_x = model(X, w)
y_prediction = T.argmax(py_x, axis=1)

cost = T.mean(T.nnet.categorical_crossentropy(py_x, Y))
gradient = T.grad(cost=cost, wrt=w)
update = [[w, w - gradient * 0.05]]

train = theano.function(inputs=[X, Y], outputs=cost, updates=update, allow_input_downcast=True)
predict = theano.function(inputs=[X], outputs=y_prediction, allow_input_downcast=True)

def mini_batch(total, size):
    return zip(range(0, total, size),
               range(size, total, size))

for i in range(100):
    for start, end in mini_batch(len(trainX), 128):
        cost = train(trainX[start:end], trainY[start:end])
    print i, np.mean(np.argmax(testY, axis=1) == predict(testX))
