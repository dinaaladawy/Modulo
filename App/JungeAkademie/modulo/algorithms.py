# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 05:02:51 2017

@author: Andrei
"""

from abc import ABC, abstractmethod  # , abstractstaticmethod
from enum import Enum
# from .models import Module
import copy
import numpy as np
import tensorflow as tf


# matrix must be a numpy 2d array (matrix..)
# accepted is also a 1d array...
def normalize_column_probabilities(matrix):
    compare = 1.0
    if len(matrix.shape) > 1:
        # dealing with matrix
        compare = np.ones((matrix.shape[1],))

    if np.any(np.abs(np.sum(matrix, axis=0) - compare) >= 1e-9):
        # use softmax-type normalization
        matrix = np.divide(np.exp(matrix), np.sum(np.exp(matrix), axis=0))

    # assert that column sum is 1
    assert (np.all(np.abs(np.sum(matrix, axis=0) - compare) < 1e-9))
    return matrix


class UpdateType(Enum):
    DELETE_CATEGORY = 0
    DELETE_INTEREST = 1
    INSERT_CATEGORY = 2
    INSERT_INTEREST = 3


class LearningAlgorithm(ABC):
    @abstractmethod
    def get_weights(self):
        pass

    @abstractmethod
    def update_weights(self, update_type, to_delete_index=None):
        pass

    @abstractmethod
    def run_algorithm(self, train=False, evaluate=False, loss=False, **kwargs):
        pass

    @abstractmethod
    def create_network(self, **kwargs):
        pass


class LinearClassifier(LearningAlgorithm):
    """
    session = None  # tensorflow session
    net_output = None  # category predictions
    net_loss = None  # loss
    train = None  # train operation
    w = tf.Variable([], validate_shape=False)  # weights
    b = tf.Variable([], validate_shape=False)  # biases
    x = tf.placeholder(tf.float32)  # input vector
    y = tf.placeholder(tf.float32)  # label vector
    """

    def __init__(self, num_interests, num_categories):
        super(LinearClassifier, self).__init__()
        self.net = None
        self.session = None
        self.num_interests = num_interests
        self.num_categories = num_categories

        self.create_network(num_interests=num_interests, num_categories=num_categories)

    def __get_inputs(self, all_interests, selected_interests):
        assert(selected_interests is not [])
        # create boolean vector of positions of interests
        if not selected_interests:  # if list is empty
            inputs = np.ones((1, self.num_interests))
        else:
            inputs = np.zeros((1, self.num_interests))
            for i in selected_interests:
                inputs[0, all_interests.index(i)] = 1
        # shape (1, num_interests)
        assert (inputs.shape == (1, self.num_interests))
        return inputs

    def __get_labels(self, all_categories, feedback):
        """
        try:
            # list of selected module (-> selected by the student)
            selected_modules = [Module.objects.get(title=feedback['selected_module'])]
        except Module.DoesNotExist:
            # list of interesting modules (-> selected by the student)
            selected_modules = [Module.objects.get(title=t) for t in feedback['interesting_modules']]
        
        selected_modules = [Module.objects.get(title=t) for t in feedback['interesting_modules']]
        not_interesting_modules = [Module.objects.get(title=t) for t in feedback['not_for_me_modules']]
        """
        selected_modules = feedback['interesting_modules']
        # not_interesting_modules = feedback['not_for_me_modules']

        # get category names (with repetitions) of the selected modules
        selected_categories = [c.name for m in selected_modules for c in m.categories.all()]

        # return label for this query;
        # don't need to normalize probabilities anymore because we don't use the softmax anymore...
        # return normalize_column_probabilities(np.array([selected_categories.count(name) for name in all_categories]))
        labels = np.array([[int(c in selected_categories) for c in all_categories]])

        assert (labels.shape == (1, self.num_categories))
        return labels

    def run_algorithm(self, train=False, evaluate=False, loss=False,
                      all_interests=None, all_categories=None, selected_interests=None, feedback=None):
        tensors = {}
        feed_dict = {}

        if evaluate or loss or train:
            feed_dict[self.net.inputs] = copy.deepcopy(self.__get_inputs(all_interests, selected_interests))
            if evaluate:
                # tensors['eval'] = self.net.outputs
                tensors['eval'] = self.net.predictions
            if loss or train:
                feed_dict[self.net.labels] = copy.deepcopy(self.__get_labels(all_categories, feedback))
                if loss:
                    tensors['loss'] = self.net.loss
                if train:
                    tensors['train'] = self.net.train_op

        return self.session.run(tensors, feed_dict)

    def get_weights(self):
        """
        temp_w = tf.slice(self.net.w, begin=[0, 0], size=tf.shape(self.net.w))
        temp_b = tf.slice(self.net.b, begin=[0], size=tf.shape(self.net.b))
        value_w, value_b = self.session.run([temp_w, temp_b])
        return value_w, value_b
        """
        return self.session.run([self.net.w, self.net.b])

    def update_weights(self, update_type, to_delete_index=None):
        value_w, value_b = self.get_weights()

        if update_type == UpdateType.DELETE_CATEGORY:
            value_w = np.delete(value_w, to_delete_index, axis=1)
            value_b = np.delete(value_b, to_delete_index, axis=0)
            op = [tf.assign(self.net.w, value_w, validate_shape=False),
                  tf.assign(self.net.b, value_b, validate_shape=False)]
        elif update_type == UpdateType.DELETE_INTEREST:
            value_w = np.delete(value_w, to_delete_index, axis=0)
            op = tf.assign(self.net.w, value_w, validate_shape=False)
        elif update_type == UpdateType.INSERT_CATEGORY:
            # add column to weight matrix
            value_w = np.append(value_w, np.random.normal(size=[value_w.shape[0], 1]), axis=1)
            # add row to bias
            value_b = np.append(value_b, np.random.normal(size=[1]), axis=0)
            op = [tf.assign(self.net.w, value_w, validate_shape=False),
                  tf.assign(self.net.b, value_b, validate_shape=False)]
        elif update_type == UpdateType.INSERT_INTEREST:
            # add row to weight matrix
            value_w = np.append(value_w, np.random.normal(size=[1, value_w.shape[1]]), axis=0)
            op = tf.assign(self.net.w, value_w, validate_shape=False)
        else:
            raise ValueError("Unknown (weights) update type")

        self.session.run(op)  # reassign variables

    def create_network(self, **kwargs):
        num_interests = kwargs.get('num_interests', None)
        num_categories = kwargs.get('num_categories', None)
        assert (num_interests is not None)
        assert (num_categories is not None)

        learning_rate = 0.1
        reg = 0.01
        self.net = LinearClassifier.get_model(num_interests=num_interests, num_categories=num_categories,
                                              learning_rate=learning_rate, reg=reg)

        saver = tf.train.Saver(var_list=tf.trainable_variables())
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.session = tf.Session(config=config)
        self.session.run(tf.global_variables_initializer())

        ckpt_dir = "training/saved_models/"
        ckpt = tf.train.get_checkpoint_state(ckpt_dir)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(self.session, ckpt.model_checkpoint_path)  # restore trainable variables
            print("Restored model variables from {}!".format(ckpt.model_checkpoint_path))
        else:
            print("Using untrained model!")

        print("LinearClassifier initialized")

    @staticmethod
    def get_model(num_interests, num_categories, learning_rate=1e-1, reg=1e-2):
        class Model:
            def __init__(self):
                # placeholders
                self.inputs = None
                self.labels = None
                # variables
                self.w = None
                self.b = None
                # tensors
                self.outputs = None
                self.predictions = None
                self.accuracy = None
                self.loss = None
                self.train_op = None

        net = Model()
        net.inputs = tf.placeholder("float", shape=(None, num_interests), name="inputs")
        net.labels = tf.placeholder("float", shape=(None, num_categories), name="labels")
        net.w = tf.get_variable("weights", shape=(num_interests, num_categories), validate_shape=True,
                                initializer=tf.contrib.layers.xavier_initializer(),
                                regularizer=tf.contrib.layers.l2_regularizer(reg))
        net.b = tf.get_variable("biases", shape=(num_categories,), validate_shape=True,
                                initializer=tf.zeros_initializer())
        net.outputs = tf.add(tf.matmul(net.inputs, net.w), net.b, name="logits")

        net.distribution = tf.nn.softmax(net.outputs)
        net.predictions = tf.cast(tf.sigmoid(net.outputs) >= 0.5, "float", name="predictions")
        net.accuracy = tf.reduce_mean(tf.cast(tf.equal(net.predictions, net.labels), "float"), name="accuracy")
        reg_loss = tf.losses.get_regularization_loss()
        data_loss = tf.losses.sigmoid_cross_entropy(multi_class_labels=net.labels, logits=net.outputs)
        net.loss = tf.add(data_loss, reg_loss, name="loss")

        # TODO: add (exponentially) decaying learning rate
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
        net.train_op = optimizer.minimize(net.loss, name="train_op")

        '''
        # TODO: add (exponentially) decaying learning rate
        LinearClassifier.net_output = tf.nn.softmax(
            tf.add(tf.matmul(LinearClassifier.x, LinearClassifier.w), LinearClassifier.b))
        reg_loss = LinearClassifier.beta * tf.nn.l2_loss(LinearClassifier.w)  # add regularization
        LinearClassifier.net_loss = tf.reduce_sum(
            tf.square(LinearClassifier.net_output - LinearClassifier.y)) + reg_loss
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=LinearClassifier.alpha)
        LinearClassifier.train = optimizer.minimize(LinearClassifier.net_loss)
        '''

        return net
