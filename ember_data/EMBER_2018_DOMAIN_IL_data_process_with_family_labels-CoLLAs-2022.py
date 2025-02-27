#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import numpy as np
import tqdm
import json
import random
import time
import multiprocessing
from ember_features import PEFeatureExtractor

def vectorize(irow, raw_features_string, X_path, y_path, extractor, nrows):
    """
    Vectorize a single sample of raw features and write to a large numpy file
    """
    raw_features = json.loads(raw_features_string)
    
    feature_vector = extractor.process_raw_features(raw_features)

    y = np.memmap(y_path, dtype=np.float32, mode="r+", shape=nrows)
    y[irow] = raw_features["label"]
    

    X = np.memmap(X_path, dtype=np.float32, mode="r+", shape=(nrows, extractor.dim))
    X[irow] = feature_vector


def vectorize_unpack(args):
    """
    Pass through function for unpacking vectorize arguments
    """
    return vectorize(*args)



def create_parent_folder(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
        
def raw_feature_iterator(file_paths, task_months):
    """
    Yield raw feature strings from the inputed file paths
    """
    for path in file_paths:
        with open(path, "r") as fin:
            for line in fin:
                raw_features = json.loads(line)
                if raw_features['appeared'] in task_months:
                    yield line


def task_based_vectorize_subset(X_path, y_path, raw_feature_paths, task_months, extractor, nrows):
    """
    Vectorize a subset of data and write it to disk
    """
    # Create space on disk to write features to
    X = np.memmap(X_path, dtype=np.float32, mode="w+", shape=(nrows, extractor.dim))
    y = np.memmap(y_path, dtype=np.float32, mode="w+", shape=nrows)

    del X, y

    # Distribute the vectorization work
    pool = multiprocessing.Pool()
    argument_iterator = ((irow, raw_features_string, X_path, y_path, extractor, nrows)
                         for irow, raw_features_string in enumerate(raw_feature_iterator(raw_feature_paths, task_months)))
    #print(argument_iterator)
    
    
    for _ in tqdm.tqdm(pool.imap_unordered(vectorize_unpack, argument_iterator), total=nrows):
        pass
    
    #return argument_iterator

        
def task_num_rows(raw_feature_paths, task_months):
    cnt_rows = 0
    
    family_labels = []
    
    for fp in raw_feature_paths:
        #print(fp)
        with open(fp, "r") as fin:
            #print(fp)
            for line in fin:
                raw_features = json.loads(line)
                if raw_features['appeared'] in task_months:
                    family_labels.append(raw_features['avclass'])
                    cnt_rows += 1
    return cnt_rows, family_labels


def create_task_based_vectorized_features(data_dir, save_dir, current_task, task_months, feature_version=2):
    """
    Create feature vectors from raw features and write them to disk
    """
    extractor = PEFeatureExtractor(feature_version)
    
    print(f'Vectorizing {current_task} task data')
    X_path = os.path.join(save_dir, "X_train.dat")
    y_path = os.path.join(save_dir, "y_train.dat")
    
    #y_path_family_labels = os.path.join(save_dir, "y_family_train.dat")
    
    raw_feature_paths_base_tr = [os.path.join(data_dir, "train_features_{}.jsonl".format(i)) for i in range(6)]
    raw_feature_paths_base_te = [os.path.join(data_dir, "test_features.jsonl")]
    raw_feature_paths = raw_feature_paths_base_tr + raw_feature_paths_base_te
    
    nrows, family_labels = task_num_rows(raw_feature_paths, current_task)
    #print(nrows)
    
    save_test_file = save_dir + 'task_family_labels.npz'
    np.savez(save_test_file, family_labels=family_labels)
    
    
    task_based_vectorize_subset(X_path, y_path, raw_feature_paths, current_task, extractor, nrows)
    #argument_iterator = task_based_vectorize_subset(X_path, y_path, raw_feature_paths, task_months, extractor, nrows)
    
    #return argument_iterator

def read_task_based_vectorized_features(save_dir, feature_version=2):
    """
    Read vectorized features into memory mapped numpy arrays
    """

    extractor = PEFeatureExtractor(feature_version)
    ndim = extractor.dim
    X_ = None
    y_ = None


    X_path = os.path.join(save_dir, "X_train.dat")
    y_path = os.path.join(save_dir, "y_train.dat")
    
    y_ = np.memmap(y_path, dtype=np.float32, mode="r")
    N = y_.shape[0]
    
    X_ = np.memmap(X_path, dtype=np.float32, mode="r", shape=(N, ndim))
    
    print(np.unique(y_))
    
    goodware_indices = []
    malware_indices = []
    
    
    for ind, i in enumerate(y_):
        if i == 0:
            goodware_indices.append(ind)
        elif i == 1:
            malware_indices.append(ind)
        else:
            pass
    
    malware_goodware_indices = goodware_indices + malware_indices
    
    print(len(y_[malware_goodware_indices]), len(y_[goodware_indices]), len(y_[malware_indices]))
    
    
    Y_family_labels_file = save_dir + 'task_family_labels.npz'
    Y_fam_labels_ = np.load(Y_family_labels_file)
    Y_fam_labels = Y_fam_labels_['family_labels']
    
    
    X = X_[malware_goodware_indices]
    Y = y_[malware_goodware_indices]
    Y_families = Y_fam_labels[malware_goodware_indices]
    
    indx = [i for i in range(len(Y))]
    random.shuffle(indx)

    train_size = int(len(indx)*0.9)
    trainset = indx[:train_size]
    testset = indx[train_size:]

    # Separate the training set
    X_train = X[trainset]
    Y_train = Y[trainset]
    Y_family_train = Y_families[trainset]

    # Separate the test set
    X_test = X[testset]
    Y_test = Y[testset]
    Y_family_test = Y_families[testset]
    
    
    print(f'X_train {X_train.shape} Y_train {Y_train.shape} Y_family_train {Y_family_train.shape}\n X_test {X_test.shape} Y_test {Y_test.shape} \n Y_family_test {Y_family_test.shape}')
    
    print(f'saving files ...')
    save_training_file = save_dir + 'XY_train.npz'
    save_test_file = save_dir + 'XY_test.npz'
    
    np.savez(save_training_file, X_train=X_train, Y_train=Y_train, Y_family_train = Y_family_train)
    np.savez(save_test_file, X_test=X_test, Y_test=Y_test, Y_family_test = Y_family_test)

    
    
    
    
all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
                   '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']

# data_dir = "../../../ember/ember_data/2018_data/ember2018/"
data_dir = "/home/bae/continual-learning-malware/ember_data/ember2018/"

for task in range(0,len(all_task_months)):
    start_time = time.time()
    #task = 5 + task
    current_task = all_task_months[task]
    task_months = all_task_months[:task+1]
    
    
    # save_dir = '../../ember2018/month_based_processing_with_family_labels/' + str(current_task) + '/'
    save_dir = '/home/bae/continual-learning-malware/ember_data/ember2018/month_based_processing_with_family_labels/' + str(current_task) + '/'

    create_parent_folder(save_dir)
    
    print(f'Processing data for task {current_task}')
    #print(current_task, task_months)
    create_task_based_vectorized_features(data_dir, save_dir, current_task, task_months, feature_version=2)
    read_task_based_vectorized_features(save_dir, feature_version=2)
    
    
    end_time = time.time()
    
    print(f'Elapsed time {(end_time - start_time)/60} mins.')    

