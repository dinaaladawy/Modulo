# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 05:02:51 2017

@author: Andrei
"""

import copy, numpy as np, tensorflow as tf
from abc import ABC, abstractstaticmethod, abstractmethod
from enum import Enum
from .models import Module


#matrix must be a numpy 2d array (matrix..)
#accepted is also a 1d array...
def normalizeProbabilitiesCol(matrix):
    compare = 1.0
    if len(matrix.shape) > 1:
        #dealing with matrix
        compare = np.ones((matrix.shape[1],))
        
    if (np.abs(np.sum(matrix, axis=0) - compare) >= 1e-9).any():
        #use softmax-type normalization
        matrix = np.divide(np.exp(matrix), np.sum(np.exp(matrix), axis=0))
    
    #assert that column sum is 1
    assert((np.abs(np.sum(matrix, axis=0) - compare) < 1e-9).all())
    return matrix

class UpdateType(Enum):
    DELETE_CATEGORY = 0
    DELETE_INTEREST = 1
    INSERT_CATEGORY = 2
    INSERT_INTEREST = 3

class LearningAlgorithm(ABC):
    @abstractstaticmethod
    def getWeights():
        pass
    
    @abstractstaticmethod
    def updateWeights(updateType, to_delete_index=None):
        pass
    
    @abstractmethod
    def run_algorithm(self, train=False, eval=False, loss=False):
        pass
    
    @abstractstaticmethod
    def initialize():
        pass

class LinearClassifier(LearningAlgorithm):
    #tensorflow session for training
    #FIXME: problem with multithreadding; just one global session???
    session = None
    #weights
    W = tf.Variable([], validate_shape=False)
    #biases
    b = tf.Variable([], validate_shape=False)
    #input vector
    x = tf.placeholder(tf.float32)
    #label vector
    y = tf.placeholder(tf.float32)
    
    def __init__(self, rec):
        self.rec = rec
    
    def __getInput(self, allInterests):
        nrInter = len(allInterests)
        
        # create boolean vector of positions of interests
        if not self.rec.interests: #if list is empty
            x = np.ones((1, nrInter))
        else:
            x = np.zeros((1, nrInter))
            for i in self.rec.interests:
                x[0, allInterests.index(i)] = 1
        return x
    
    def __getLabel(self, allCategories):
        try:
            #list of selected module (-> selected by the student)
            selected_modules = [Module.objects.get(title=self.rec.feedback['selected'])]
        except Module.DoesNotExist:
            #list of interesting modules (-> selected by the student)
            selected_modules = [Module.objects.get(title=t) for t in self.rec.feedback['interesting']]
        
        # get category names of the selected_modules and create "correct label" for this query
        #selected_categories = {c.name for m in selected_modules for c in m.categories.all()};
        selected_categories = [c.name for m in selected_modules for c in m.categories.all()];
        return normalizeProbabilitiesCol(np.array([selected_categories.count(name) for name in allCategories]))
        
    def run_algorithm(self, train=False, eval=False, loss=False):
        res = {}
        input = {}
        
        if eval or loss or train:
            input[LinearClassifier.x] = copy.deepcopy(self.__getInput(self.rec.interest_names))            
            if eval:
                res['eval'] = LinearClassifier.net_output                
            if loss or train:
                input[LinearClassifier.y] = copy.deepcopy(self.__getLabel(self.rec.category_names))                
                if loss:
                    res['loss'] = LinearClassifier.net_loss
                if train:
                    res['train'] = LinearClassifier.train

        return LinearClassifier.session.run(res, input)
    
    def getWeights():
        temp_W = tf.slice(LinearClassifier.W, begin=[0, 0], size=tf.shape(LinearClassifier.W))
        temp_b = tf.slice(LinearClassifier.b, begin=[0], size=tf.shape(LinearClassifier.b))
        value_W = LinearClassifier.session.run(temp_W)
        value_b = LinearClassifier.session.run(temp_b)
        return value_W, value_b
    
    def updateWeights(updateType, to_delete_index=None):
        value_W, value_b = LinearClassifier.getWeights()
        op = []
        
        if updateType == UpdateType.DELETE_CATEGORY:
            value_W = np.delete(value_W, to_delete_index, axis=1)
            value_b = np.delete(value_b, to_delete_index, axis=0)
            op = [tf.assign(LinearClassifier.W, value_W, validate_shape=False), tf.assign(LinearClassifier.b, value_b, validate_shape=False)]
        elif updateType == UpdateType.DELETE_INTEREST:
            value_W = np.delete(value_W, to_delete_index, axis=0)
            op = tf.assign(LinearClassifier.W, value_W, validate_shape=False)
        elif updateType == UpdateType.INSERT_CATEGORY:
            value_W = np.append(value_W, np.random.normal(size=[value_W.shape[0]]), axis=1) #add column to weight matrix
            value_b = np.append(value_b, np.random.normal(size=[1]), axis=0) #add row to bias
            op = [tf.assign(LinearClassifier.W, value_W, validate_shape=False), tf.assign(LinearClassifier.b, value_b, validate_shape=False)]
        elif updateType == UpdateType.INSERT_INTEREST:
            value_W = np.append(value_W, np.random.normal(size=[value_W.shape[1]]), axis=0) #add row to weight matrix
            op = tf.assign(LinearClassifier.W, value_W, validate_shape=False)
        else:
            pass
            
        LinearClassifier.session.run(op) #reassign variables
    
    def initialize(num_interests, num_categories):
        #normalize the data: column sum must be 1!!! why??? -> linear classifier...
        #W = np.random.normal(loc=0.0, scale=1.0, size=(nrCateg, nrInter))
        #W = normalizeProbabilitiesCol(W)
        
        LinearClassifier.W = tf.Variable(tf.random_normal([num_interests, num_categories], mean=0, stddev=1), validate_shape=False) #weights
        LinearClassifier.b = tf.Variable(tf.random_normal([num_categories], mean=0, stddev=1), validate_shape=False) #biases
        #print("Recommender.W = ", Recommender.W, sep='')
        #print("Recommender.b = ", Recommender.b, sep='')
        #FIXME: problem with multithreadding; just one global session???        
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        LinearClassifier.session = tf.Session(config=config)
        LinearClassifier.session.run(tf.global_variables_initializer())
        
        LinearClassifier.alpha = 0.5
        #print("Recommender.alpha = ", Recommender.alpha, sep='')
        LinearClassifier.beta = 0.01
        #print("Recommender.beta = ", Recommender.beta, sep='')
        
        LinearClassifier.net_output = tf.nn.softmax(tf.add(tf.matmul(LinearClassifier.x, LinearClassifier.W), LinearClassifier.b))
        LinearClassifier.net_loss = tf.reduce_sum(tf.square(LinearClassifier.net_output - LinearClassifier.y)) + LinearClassifier.beta * tf.nn.l2_loss(LinearClassifier.W) #add regularization
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=LinearClassifier.alpha)
        LinearClassifier.train = optimizer.minimize(LinearClassifier.net_loss)
        print("LinearClassifier initialized")
