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

from datetime import datetime
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
import operator
import copy


# In[ ]:


def get_emberdata_family_stat(data_dir):
    #data_dir = "../../ember/ember_data/2018_data/ember2018/"
    
    raw_feature_paths_base_tr = [os.path.join(data_dir, "train_features_{}.jsonl".format(i)) for i in range(6)]
    raw_feature_paths_base_te = [os.path.join(data_dir, "test_features.jsonl")]
    raw_feature_paths = raw_feature_paths_base_tr + raw_feature_paths_base_te
    #print(raw_feature_paths)

    all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
                       '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']
    task_months = all_task_months

    av_class_stats = {}
    cnt_rows = 0
    cnt_good_rows = 0
    cnt_missing_rows = 0

    for fp in raw_feature_paths:
        #print(fp)
        with open(fp, "r") as fin:
            #print(fp)
            for line in fin:
                raw_features = json.loads(line)
                #print(raw_features.keys())

                if raw_features['appeared'] in task_months:
                    if raw_features['label'] == 1: # and raw_features['avclass']
                        #print(raw_features['label'], raw_features['avclass'])
                        if raw_features['avclass'] not in av_class_stats.keys():
                            av_class_stats[raw_features['avclass']] = 1
                        else:
                            av_class_stats[raw_features['avclass']] += 1
                        cnt_rows += 1

                    elif raw_features['label'] == 0:
                        cnt_good_rows += 1
                    elif raw_features['label'] == -1:
                        #print(raw_features['label'], raw_features['avclass'])
                        cnt_missing_rows += 1

            #if cnt_rows == 2:
            #    break
    min_samples = 0

    families_more_than_400_samples = {}

    for k, v in av_class_stats.items():
        if v >= min_samples and k != '':
            families_more_than_400_samples[k] = v
            
    return families_more_than_400_samples, av_class_stats


# In[ ]:


def vectorize(irow, raw_features_string, X_path, y_path, extractor, nrows):
    """
    Vectorize a single sample of raw features and write to a large numpy file
    """
    raw_features = json.loads(raw_features_string)
    
    feature_vector = extractor.process_raw_features(raw_features)

    y = np.memmap(y_path, dtype=np.float32, mode="r+", shape=nrows)
    y[irow] = top_families_100_labels[raw_features["avclass"]]

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
        
def raw_feature_iterator(file_paths, top_families):
    """
    Yield raw feature strings from the inputed file paths
    """
    all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
                   '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']
    
    for path in file_paths:
        with open(path, "r") as fin:
            for line in fin:
                raw_features = json.loads(line)
                if raw_features['appeared'] in all_task_months:
                    if raw_features['avclass'] != '':
                        if raw_features['avclass'] in top_families and raw_features['label'] == 1:
                            yield line


def task_based_vectorize_subset(X_path, y_path, raw_feature_paths, top_families, extractor, nrows):
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
                         for irow, raw_features_string in enumerate(raw_feature_iterator(raw_feature_paths, top_families)))
    #print(argument_iterator)
    
    
    for _ in tqdm.tqdm(pool.imap_unordered(vectorize_unpack, argument_iterator), total=nrows):
        pass
    
    #return argument_iterator

        
def task_num_rows(raw_feature_paths, top_families):
    print(top_families)
    all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
                   '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']
    cnt_rows = 0
    for fp in raw_feature_paths:
        #print(fp)
        with open(fp, "r") as fin:
            #print(fp)
            for line in fin:
                raw_features = json.loads(line)
                if raw_features['appeared'] in all_task_months:
                    if raw_features['avclass'] != '':
                        if raw_features['avclass'] in top_families and raw_features['label'] == 1:
                            cnt_rows += 1
    return cnt_rows


def create_task_based_vectorized_features(data_dir, save_dir, top_families, feature_version=2):
    """
    Create feature vectors from raw features and write them to disk
    """
    extractor = PEFeatureExtractor(feature_version)
    
    #print(f'Vectorizing {current_task} task data')
    X_path = os.path.join(save_dir, "X_train.dat")
    y_path = os.path.join(save_dir, "y_train.dat")
    raw_feature_paths_base_tr = [os.path.join(data_dir, "train_features_{}.jsonl".format(i)) for i in range(6)]
    raw_feature_paths_base_te = [os.path.join(data_dir, "test_features.jsonl")]
    raw_feature_paths = raw_feature_paths_base_tr + raw_feature_paths_base_te
    
    
    
    nrows = task_num_rows(raw_feature_paths, top_families)
    #print(nrows)
    task_based_vectorize_subset(X_path, y_path, raw_feature_paths, top_families, extractor, nrows)
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
    
    X, Y = X_, y_
    
    indx = [i for i in range(len(Y))]
    random.shuffle(indx)

    train_size = int(len(indx)*0.9)
    trainset = indx[:train_size]
    testset = indx[train_size:]

    # Separate the training set
    X_train = X[trainset]
    Y_train = Y[trainset]

    # Separate the test set
    X_test = X[testset]
    Y_test = Y[testset]
    
    
    print(f'X_train {X_train.shape} Y_train {Y_train.shape} X_test {X_test.shape} Y_test {Y_test.shape}')
    
    print(f'saving files ...')
    save_training_file = save_dir + 'XY_train.npz'
    save_test_file = save_dir + 'XY_test.npz'
    
    np.savez(save_training_file, X_train=X_train, Y_train=Y_train)
    np.savez(save_test_file, X_test=X_test, Y_test=Y_test)
    


# In[ ]:





# In[ ]:


#data_dir = "../../ember/ember_data/2018_data/ember2018/"
data_dir = "/home/bae/continual-learning-malware/ember_data/ember2018/"

families_more_than_400_samples, av_class_stats = get_emberdata_family_stat(data_dir)
ordered_106_families = sorted(families_more_than_400_samples.items(),key=operator.itemgetter(1),reverse=True)


ordered_100_families_keys_100 = []
num_classes = 100

cnt = 0
for j in ordered_106_families:
    #print(j[0], j[1])
    cnt += 1
    ordered_100_families_keys_100.append(j[0])
    if cnt == num_classes:
        break
print(len(ordered_100_families_keys_100))

    
top_families_100_labels = {}

for ind, fam in enumerate(ordered_100_families_keys_100):
    top_families_100_labels[fam] = int(ind)
    
    
all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
                   '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']



start_time = time.time()

#top_families = ordered_100_families_keys_100

# save_dir = '/home/mr6564/continual_research/top_classes_' + str(num_classes) + '/'
save_dir = '/home/bae/continual-learning-malware/top_classes_'+ str(num_classes) + '/'

create_parent_folder(save_dir)


create_task_based_vectorized_features(data_dir, save_dir, ordered_100_families_keys_100, feature_version=2)
read_task_based_vectorized_features(save_dir, feature_version=2)
    
    
end_time = time.time()

print(f'Elapsed time {(end_time - start_time)/60} mins.')

