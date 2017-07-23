# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 13:17:32 2017

@author: Andrei
"""

from modulo.algorithms import LinearClassifier
import json
import numpy as np
import tensorflow as tf

'''
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "JungeAkademie.settings"
django.setup()
from modulo.models import Module, Category, Interest
'''

# '''
get_model = LinearClassifier.get_model
'''


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
    net.labels = tf.placeholder("float", shape=(None, num_categories), name="inputs")
    net.w = tf.get_variable("weights", shape=(num_interests, num_categories), validate_shape=True,
                            initializer=tf.contrib.layers.xavier_initializer(),
                            regularizer=tf.contrib.layers.l2_regularizer(reg))
    net.b = tf.get_variable("biases", shape=(num_categories,), validate_shape=True,
                            initializer=tf.zeros_initializer())
    net.outputs = tf.add(tf.matmul(net.inputs, net.w), net.b, name="logits")

    net.predictions = tf.sigmoid(net.outputs, name="predictions")
    net.accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.cast(net.predictions >= 0.5, "float"), net.labels), "float"),
                                  name="accuracy")
    reg_loss = tf.losses.get_regularization_loss()
    data_loss = tf.losses.sigmoid_cross_entropy(multi_class_labels=net.labels, logits=net.outputs)
    net.loss = tf.add(data_loss, reg_loss, name="loss")

    # TODO: add (exponentially) decaying learning rate
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    net.train_op = optimizer.minimize(net.loss, name="train_op")

    return net


# '''


def get_dataset(reduce_training=False):
    print("Getting dataset...")
    dataset = json.load(open("dataset/dataset.json", "r"))
    # format: ['train']['inputs']; ['train']['labels']
    print("Got dataset!")

    if reduce_training:
        dataset['train']['inputs'] = dataset['train']['inputs'][:1]
        dataset['train']['labels'] = dataset['train']['labels'][:1]

    for mode in dataset:
        for inp_type in dataset[mode]:
            dataset[mode][inp_type] = np.array(dataset[mode][inp_type])
            print("dataset[{}][{}].shape = {}".format(mode, inp_type, dataset[mode][inp_type].shape))

    return dataset


def main():
    dataset = get_dataset()

    train_data = dataset['train']
    training_samples = len(train_data['inputs'])
    epochs = 100
    batch_size = 10
    nr_batches_per_epoch = (training_samples + batch_size - 1) // batch_size
    print("training_samples = {}".format(training_samples))
    print("nr_batches_per_epoch = {}".format(nr_batches_per_epoch))

    num_interests = len(dataset['train']['inputs'][0])
    num_categories = len(dataset['train']['labels'][0])
    learning_rate = 1e-1
    reg = 1e-2
    print("num_interests = {}".format(num_interests))
    print("num_categories = {}".format(num_categories))
    print("learning_rate = {}".format(learning_rate))
    print("regularization = {}".format(reg))
    net = LinearClassifier.get_model(num_interests=num_interests, num_categories=num_categories,
                                     learning_rate=learning_rate, reg=reg)
    print("Got model")

    saver = tf.train.Saver(var_list=[net.w, net.b])

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    session = tf.Session(config=config)
    with session.as_default():
        session.run(tf.global_variables_initializer())

        for epoch in range(epochs):
            permutation = np.random.permutation(training_samples)
            print(permutation)
            for batch in range(nr_batches_per_epoch):
                inputs = train_data['inputs'][permutation[batch * batch_size:(batch + 1) * batch_size]]
                labels = train_data['labels'][permutation[batch * batch_size:(batch + 1) * batch_size]]
                _, loss, accuracy, preds = session.run([net.train_op, net.loss, net.accuracy, net.predictions],
                                                       feed_dict={net.inputs: inputs, net.labels: labels})
                update = epoch * nr_batches_per_epoch + batch + 1
                print("Update: {}; Loss: {}; Accuracy: {}".format(update, loss, accuracy))

        saver.save(sess=session, save_path="saved_models/model")

    return None


if __name__ == '__main__':
    main()
