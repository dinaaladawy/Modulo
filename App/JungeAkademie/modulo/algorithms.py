# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 05:02:51 2017

@author: Andrei
"""

import copy, numpy as np, tensorflow as tf
from abc import ABC, abstractstaticmethod, abstractmethod
from enum import Enum
from .models import Module


# matrix must be a numpy 2d array (matrix..)
# accepted is also a 1d array...
def normalize_probs_col(matrix):
    compare = 1.0
    if len(matrix.shape) > 1:
        # dealing with matrix
        compare = np.ones((matrix.shape[1],))

    if (np.abs(np.sum(matrix, axis=0) - compare) >= 1e-9).any():
        # use softmax-type normalization
        matrix = np.divide(np.exp(matrix), np.sum(np.exp(matrix), axis=0))

    # assert that column sum is 1
    assert ((np.abs(np.sum(matrix, axis=0) - compare) < 1e-9).all())
    return matrix


class UpdateType(Enum):
    DELETE_CATEGORY = 0
    DELETE_INTEREST = 1
    INSERT_CATEGORY = 2
    INSERT_INTEREST = 3


class LearningAlgorithm(ABC):
    @staticmethod
    @abstractstaticmethod
    def get_weights():
        pass

    @staticmethod
    @abstractstaticmethod
    def update_weights(updateType, to_delete_index=None):
        pass

    @abstractmethod
    def run_algorithm(self, train=False, eval=False, loss=False):
        pass

    @staticmethod
    @abstractstaticmethod
    def initialize():
        pass


class LinearClassifier(LearningAlgorithm):
    # FIXME: problem with multi-threading; just one global session???
    session = None  # tensorflow session
    net_output = None  # category predictions
    net_loss = None  # loss
    train = None  # train operation
    w = tf.Variable([], validate_shape=False)  # weights
    b = tf.Variable([], validate_shape=False)  # biases
    x = tf.placeholder(tf.float32)  # input vector
    y = tf.placeholder(tf.float32)  # label vector

    def __init__(self, rec):
        self.rec = rec

    def __get_input(self, all_interests):
        nr_interests = len(all_interests)

        # create boolean vector of positions of interests
        if not self.rec.interests:  # if list is empty
            x = np.ones((1, nr_interests))
        else:
            x = np.zeros((1, nr_interests))
            for i in self.rec.interests:
                x[0, all_interests.index(i)] = 1
        return x

    def __get_label(self, all_categories):
        '''
        try:
            # list of selected module (-> selected by the student)
            selected_modules = [Module.objects.get(title=self.rec.feedback['selected_module'])]
        except Module.DoesNotExist:
            # list of interesting modules (-> selected by the student)
            selected_modules = [Module.objects.get(title=t) for t in self.rec.feedback['interesting_modules']]
        '''
        selected_modules = [Module.objects.get(title=t) for t in self.rec.feedback['interesting_modules']]
        not_interesting_modules = [Module.objects.get(title=t) for t in self.rec.feedback['not_for_me_modules']]

        # get category names (with repetitions) of the selected modules
        selected_categories = [c.name for m in selected_modules for c in m.categories.all()]
        # return label for this query -> shape = (nr_categories, )
        return normalize_probs_col(np.array([selected_categories.count(name) for name in all_categories]))

    def run_algorithm(self, train=False, evaluate=False, loss=False):
        res = {}
        inp = {}

        if evaluate or loss or train:
            inp[LinearClassifier.x] = copy.deepcopy(self.__get_input(self.rec.interest_names))
            if evaluate:
                res['eval'] = LinearClassifier.net_output
            if loss or train:
                inp[LinearClassifier.y] = copy.deepcopy(self.__get_label(self.rec.category_names))
                if loss:
                    res['loss'] = LinearClassifier.net_loss
                if train:
                    res['train'] = LinearClassifier.train

        return LinearClassifier.session.run(res, inp)

    @staticmethod
    def get_weights():
        temp_W = tf.slice(LinearClassifier.w, begin=[0, 0], size=tf.shape(LinearClassifier.w))
        temp_b = tf.slice(LinearClassifier.b, begin=[0], size=tf.shape(LinearClassifier.b))
        value_W = LinearClassifier.session.run(temp_W)
        value_b = LinearClassifier.session.run(temp_b)
        return value_W, value_b

    @staticmethod
    def update_weights(updateType, to_delete_index=None):
        value_w, value_b = LinearClassifier.get_weights()
        op = []

        if updateType == UpdateType.DELETE_CATEGORY:
            value_w = np.delete(value_w, to_delete_index, axis=1)
            value_b = np.delete(value_b, to_delete_index, axis=0)
            op = [tf.assign(LinearClassifier.w, value_w, validate_shape=False),
                  tf.assign(LinearClassifier.b, value_b, validate_shape=False)]
        elif updateType == UpdateType.DELETE_INTEREST:
            value_w = np.delete(value_w, to_delete_index, axis=0)
            op = tf.assign(LinearClassifier.w, value_w, validate_shape=False)
        elif updateType == UpdateType.INSERT_CATEGORY:
            value_w = np.append(value_w, np.random.normal(size=[value_w.shape[0], 1]),
                                axis=1)  # add column to weight matrix
            value_b = np.append(value_b, np.random.normal(size=[1]), axis=0)  # add row to bias
            op = [tf.assign(LinearClassifier.w, value_w, validate_shape=False),
                  tf.assign(LinearClassifier.b, value_b, validate_shape=False)]
        elif updateType == UpdateType.INSERT_INTEREST:
            value_w = np.append(value_w, np.random.normal(size=[1, value_w.shape[1]]),
                                axis=0)  # add row to weight matrix
            op = tf.assign(LinearClassifier.w, value_w, validate_shape=False)
        else:
            pass

        LinearClassifier.session.run(op)  # reassign variables

    @staticmethod
    def initialize(num_interests, num_categories):
        # normalize the data: column sum must be 1!!! why??? -> linear classifier...
        # w = np.random.normal(loc=0.0, scale=1.0, size=(nrCateg, nrInter))
        # w = normalize_probs_col(w)

        LinearClassifier.w = tf.Variable(tf.random_normal([num_interests, num_categories], mean=0, stddev=1),
                                         validate_shape=False)  # weights
        LinearClassifier.b = tf.Variable(tf.random_normal([num_categories], mean=0, stddev=1),
                                         validate_shape=False)  # biases
        # print("Recommender.w = ", Recommender.w, sep='')
        # print("Recommender.b = ", Recommender.b, sep='')
        # FIXME: problem with multithreadding; just one global session???
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        LinearClassifier.session = tf.Session(config=config)
        LinearClassifier.session.run(tf.global_variables_initializer())

        LinearClassifier.alpha = 0.1
        # print("Recommender.alpha = ", Recommender.alpha, sep='')
        LinearClassifier.beta = 0.01
        # print("Recommender.beta = ", Recommender.beta, sep='')

        # TODO: add (exponentially) decaying learning rate
        LinearClassifier.net_output = tf.nn.softmax(
            tf.add(tf.matmul(LinearClassifier.x, LinearClassifier.w), LinearClassifier.b))
        reg_loss = LinearClassifier.beta * tf.nn.l2_loss(LinearClassifier.w)  # add regularization
        LinearClassifier.net_loss = tf.reduce_sum(
            tf.square(LinearClassifier.net_output - LinearClassifier.y)) + reg_loss
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=LinearClassifier.alpha)
        LinearClassifier.train = optimizer.minimize(LinearClassifier.net_loss)
        print("LinearClassifier initialized")
