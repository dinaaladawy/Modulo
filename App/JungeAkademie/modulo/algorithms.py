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

    def __init__(self, num_interests, num_categories, num_layers=3):
        super(LinearClassifier, self).__init__()
        self.net = None
        self.session = None
        self.num_interests = num_interests
        self.num_categories = num_categories

        self.create_network(num_interests=num_interests, num_categories=num_categories,
                            num_layers=num_layers, training=False)

    def __get_inputs(self, all_interests, selected_interests):
        assert (selected_interests is not [])
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
        return self.session.run([self.net.first_w, self.net.first_b, self.net.last_w, self.net.last_b])

    def update_weights(self, update_type, to_delete_index=None):
        first_w, first_b, last_w, last_b = self.get_weights()

        if update_type == UpdateType.DELETE_CATEGORY:
            value_w = np.delete(last_w, to_delete_index, axis=1)
            value_b = np.delete(last_b, to_delete_index, axis=0)
            op = [tf.assign(self.net.last_w, value_w, validate_shape=False),
                  tf.assign(self.net.last_b, value_b, validate_shape=False)]
        elif update_type == UpdateType.DELETE_INTEREST:
            value_w = np.delete(first_w, to_delete_index, axis=0)
            op = tf.assign(self.net.first_w, value_w, validate_shape=False)
        elif update_type == UpdateType.INSERT_CATEGORY:
            # add column to weight matrix
            value_w = np.append(last_w, np.random.normal(size=[last_w.shape[0], 1]), axis=1)
            # add row to bias
            value_b = np.append(last_b, np.random.normal(size=[1]), axis=0)
            op = [tf.assign(self.net.last_w, value_w, validate_shape=False),
                  tf.assign(self.net.last_b, value_b, validate_shape=False)]
        elif update_type == UpdateType.INSERT_INTEREST:
            # add row to weight matrix
            value_w = np.append(first_w, np.random.normal(size=[1, first_w.shape[1]]), axis=0)
            op = tf.assign(self.net.first_w, value_w, validate_shape=False)
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
    def get_model(num_interests, num_categories, num_layers=3,
                  learning_rate=1e-1, reg=1e-2, training=False, dropout_rate=0.5):
        class Model:
            def __init__(self):
                # placeholders
                self.inputs = None
                self.labels = None
                # variables
                self.train_variables = None
                self.first_w = None
                self.first_b = None
                self.last_w = None
                self.last_b = None
                # tensors
                self.outputs = None
                self.predictions = None
                self.accuracy = None
                self.loss = None
                self.train_op = None

        net = Model()
        net.inputs = tf.placeholder("float", shape=(None, num_interests), name="inputs")
        net.labels = tf.placeholder("float", shape=(None, num_categories), name="labels")

        first_layer_name = None
        fc_init = tf.contrib.layers.xavier_initializer()
        fc_reg = tf.contrib.layers.l2_regularizer(reg)

        x = net.inputs
        for l in range(1, num_layers):
            layer_name = "fc{}".format(l)
            if l == 1:
                first_layer_name = layer_name
            x = tf.layers.dense(x, 512, activation=tf.nn.relu, name=layer_name,
                                kernel_initializer=fc_init, kernel_regularizer=fc_reg)
            x = tf.layers.dropout(x, rate=dropout_rate, training=training, name="drop{}".format(l))
        last_layer_name = "fc{}".format(num_layers)
        x = tf.layers.dense(x, num_categories, activation=None, name=last_layer_name,
                            kernel_initializer=fc_init, kernel_regularizer=fc_reg)
        if first_layer_name is None:
            first_layer_name = last_layer_name
        net.train_variables = tf.trainable_variables()
        print(net.train_variables)
        with tf.variable_scope(tf.get_variable_scope(), reuse=True):
            net.first_w = tf.get_variable("{}/kernel".format(first_layer_name))
            net.first_b = tf.get_variable("{}/bias".format(first_layer_name))
            net.last_w = tf.get_variable("{}/kernel".format(last_layer_name))
            net.last_b = tf.get_variable("{}/bias".format(last_layer_name))
        print(net.first_w)
        print(net.first_b)
        print(net.last_w)
        print(net.last_b)

        net.outputs = x

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
