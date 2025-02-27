import copy
import numpy as np
from sklearn.utils import shuffle
from torchvision import datasets, transforms
from torch.utils.data import ConcatDataset, Dataset
import torch
from sklearn.preprocessing import StandardScaler


class ExemplarDataset(Dataset):
    '''Create dataset from list of <np.arrays> with shape (N, C, H, W) (i.e., with N images each).

    The images at the i-th entry of [exemplar_sets] belong to class [i], unless a [target_transform] is specified'''

    def __init__(self, exemplar_sets, target_transform=None):
        super().__init__()
        self.exemplar_sets = exemplar_sets
        self.target_transform = target_transform

    def __len__(self):
        total = 0
        for class_id in range(len(self.exemplar_sets)):
            total += len(self.exemplar_sets[class_id])
        return total

    def __getitem__(self, index):
        total = 0
        for class_id in range(len(self.exemplar_sets)):
            exemplars_in_this_class = len(self.exemplar_sets[class_id])
            if index < (total + exemplars_in_this_class):
                class_id_to_return = class_id if self.target_transform is None else self.target_transform(class_id)
                exemplar_id = index - total
                break
            else:
                total += exemplars_in_this_class
        image = torch.from_numpy(self.exemplar_sets[class_id][exemplar_id])
        return (image, class_id_to_return)




def V2_get_continual_ember_class_data(data_dir, train=True):
    
    if train:
        data_dir = data_dir + '/'
        XY_train = np.load(data_dir + 'XY_train.npz')
        X_tr, Y_tr = XY_train['X_train'], XY_train['Y_train']

        return X_tr, Y_tr
    else:
        data_dir = data_dir + '/'
        XY_test = np.load(data_dir + 'XY_test.npz')
        X_test, Y_test = XY_test['X_test'], XY_test['Y_test']

        return X_test, Y_test 



def get_selected_classes(target_classes):
    classes_Y = [i for i in range(100)]
    #print(classes_Y)
    selected_classes = np.random.choice(classes_Y, target_classes,replace=False)
    #print(selected_classes)
    
    return selected_classes


def get_ember_selected_class_data(data_dir, selected_classes, train=True):
    
    
    if train:
        all_X, all_Y = V2_get_continual_ember_class_data(data_dir, train=True)
    else:
        all_X, all_Y = V2_get_continual_ember_class_data(data_dir, train=False)
    
    X_ = []
    Y_ = []

    for ind, cls in enumerate(selected_classes):
        get_ind_cls = np.where(all_Y == cls)
        cls_X = all_X[get_ind_cls]
        
        #cls_Y = all_Y[get_ind_cls]

        #assert len(cls_Y) == len(cls_X)

        for j in range(len(cls_X)):
            print("length:",len(cls_X[j]))
            X_.append(cls_X[j])
            Y_.append(ind)

    

    #from sklearn.utils import shuffle
    X_ = np.float32(np.array(X_))
    #X_ = np.array(X_)
    Y_ = np.array(Y_, dtype=np.int64)
    X_, Y_ = shuffle(X_, Y_)

    
    if train:
        print(f' Training data X {X_.shape} Y {Y_.shape}')
    else:
        print(f' Test data X {X_.shape} Y {Y_.shape}')
    
    return X_, Y_


def get_continual_ember_class_data(data_dir, num_classes, train=True):
    
    if train:
        data_dir = data_dir + str(num_classes) + '/'
        XY_train = np.load(data_dir + 'XY_train.npz')
        X_tr, Y_tr = XY_train['X_train'], XY_train['Y_train']

        return X_tr, Y_tr
    else:
        data_dir = data_dir + str(num_classes) + '/'
        XY_test = np.load(data_dir + 'XY_test.npz')
        X_test, Y_test = XY_test['X_test'], XY_test['Y_test']

        return X_test, Y_test 


def get_task_continual_training_data(data_dir, num_classes):
    
    X_train, Y_train = get_continual_ember_class_data(data_dir, num_classes)
    
    #X_train = []
    #for i in X_tr: #make 2381 to 2401 so that the sqrt is 49
    #    i = np.array(list(i) + [0] * 20)
    #    X_train.append(i)
        
    X_train = np.float32(np.array(X_train))
    Y_train = np.array(Y_train, dtype=np.int64)
    X_train, Y_train = shuffle(X_train, Y_train)
    
    print(f'Current Task month training data X {X_train.shape} Y {Y_train.shape}')
    return X_train, Y_train


def get_task_continual_test_data(data_dir, num_classes):
    
    X_test, Y_test = get_continual_ember_class_data(data_dir, num_classes, train=False)
    
    #X_test = []
    #for i in X_te: #make 2381 to 2401 so that the sqrt is 49
    #    i = np.array(list(i) + [0] * 20)
    #    X_test.append(i)
    
    X_test = np.float32(np.array(X_test))
    Y_test = np.array(Y_test,dtype=np.int64)
    X_test, Y_test = shuffle(X_test, Y_test)
    
    print(f'Testing X_test {X_test.shape} Y_test {Y_test.shape}')
    
    return X_test, Y_test




def _permutate_image_pixels(image, permutation):
    '''Permutate the pixels of an image according to [permutation].

    [image]         3D-tensor containing the image
    [permutation]   <ndarray> of pixel-indeces in their new order'''

    if permutation is None:
        return image
    else:
        c, h, w = image.size()
        image = image.view(c, -1)
        image = image[:, permutation]  #--> same permutation for each channel
        image = image.view(c, h, w)
        return image


def get_dataset(name, type='train', download=True, capacity=None, permutation=None, dir='./datasets',
                verbose=False, target_transform=None):
    '''Create [train|valid|test]-dataset.'''

    data_name = 'mnist' if name=='mnist28' else name
    dataset_class = AVAILABLE_DATASETS[data_name]

    # specify image-transformations to be applied
    dataset_transform = transforms.Compose([
        *AVAILABLE_TRANSFORMS[name],
        transforms.Lambda(lambda x, p=permutation: _permutate_image_pixels(x, p)),
    ])

    # load data-set
    dataset = dataset_class('{dir}/{name}'.format(dir=dir, name=data_name), train=False if type=='test' else True,
                            download=download, transform=dataset_transform, target_transform=target_transform)

    # print information about dataset on the screen
    if verbose:
        print(" --> {}: '{}'-dataset consisting of {} samples".format(name, type, len(dataset)))
        #print(dataset)
    # if dataset is (possibly) not large enough, create copies until it is.
    if capacity is not None and len(dataset) < capacity:
        dataset_copy = copy.deepcopy(dataset)
        dataset = ConcatDataset([dataset_copy for _ in range(int(np.ceil(capacity / len(dataset))))])

    return dataset




def get_malware_dataset(name, dir='../../', verbose=True):
    '''Create [train|valid|test]-dataset.'''
    
    train_file = dir + 'NEW_drebin_train_all.npz'
    test_file = dir + 'NEW_drebin_test_all.npz'
    train_data = np.load(train_file)
    test_data = np.load(test_file)

    X_train, y_train = train_data['X_train'], train_data['y_train']
    X_test, y_test = test_data['X_test'], test_data['y_test']    
    
    # print information about dataset on the screen
    if verbose:
        print(" --> {}: {} training and {} testing samples".format(name, len(y_train), len(y_test)))
    
    X_train = np.float32(X_train)
    X_test = np.float32(X_test)
    
    print(f'data type x_train {(y_train.dtype)} x_test {(y_test.dtype)}')
    X_train, y_train = shuffle(X_train, y_train)
    X_test, y_test = shuffle(X_test, y_test)
    
    return (X_train, y_train), (X_test, y_test)

class malwareSubDatasetExemplars(Dataset):
    '''To sub-sample a dataset, taking only those samples with label in [sub_labels].

    After this selection of samples has been made, it is possible to transform the target-labels,
    which can be useful when doing continual learning with fixed number of output units.'''
    
    # drebin dataset feature length --> 2492
    
    
    def __init__(self, original_dataset, orig_length_features, target_length_features, sub_labels, target_transform=None):
        super().__init__()
        #print(target_transform)
        self.dataset = original_dataset
        self.orig_length_features = orig_length_features
        self.target_length_features = target_length_features
        self.sub_indeces = []
        for index in range(len(self.dataset)):
            if hasattr(original_dataset, "targets"):
                if self.dataset.target_transform is None:
                    label = self.dataset.targets[index]
                else:
                    label = self.dataset.target_transform(self.dataset.targets[index])
            else:
                label = self.dataset[index][1]
            if label in sub_labels:
                self.sub_indeces.append(index)
        self.target_transform = target_transform
        

    def __len__(self):
        return len(self.sub_indeces)

    def __getitem__(self, index):
        
        #self.padded_features = np.zeros(self.target_length_features - self.orig_length_features, dtype=np.float32)
        #sample = np.concatenate((self.dataset[self.sub_indeces[index]],self.padded_features))
        #target = self.origlabels[self.sub_indeces[index]]
        
        sample = self.dataset[self.sub_indeces[index]]
        if self.target_transform:
            target = self.target_transform(sample[1])
            sample = (sample[0], target)
            #print(sample)        
        
        #if self.target_transform:
        #    #print(f'target transforming here ..')
        #    target = self.target_transform(target)
        
        return sample 


class malwareSubDataset(Dataset):
    '''To sub-sample a dataset, taking only those samples with label in [sub_labels].

    After this selection of samples has been made, it is possible to transform the target-labels,
    which can be useful when doing continual learning with fixed number of output units.'''
    
    # drebin dataset feature length --> 2492
    
    
    def __init__(self, original_dataset, orig_length_features, target_length_features, sub_labels, target_transform=None):
        super().__init__()
        #print(target_transform)
        self.dataset, self.origlabels = original_dataset
        self.orig_length_features = orig_length_features
        self.target_length_features = target_length_features
        
        self.sub_indeces = []
        for index in range(len(self.dataset)):
            label = self.origlabels[index]
            
            if label in sub_labels:
                self.sub_indeces.append(index)
        self.target_transform = target_transform
        #self.transform = [transforms.Pad(2),
        #                  transforms.ToTensor(),
        #                 ]

    def __len__(self):
        return len(self.sub_indeces)

    def __getitem__(self, index):
        
        self.padded_features = np.zeros(self.target_length_features - self.orig_length_features, dtype=np.float32)
        sample = np.concatenate((self.dataset[self.sub_indeces[index]],self.padded_features))
        target = self.origlabels[self.sub_indeces[index]]
        
        #sample = self.transform(sample)
        if self.target_transform:
            #print(f'target transforming here ..')
            target = self.target_transform(target)
            
            #print(target)
        #else:
        #    target = self.origlabels[self.sub_indeces[index]]
        #print((sample, target))
        return (sample, target)    
    
    
def get_malware_multitask_experiment(dataset_name, target_classes, init_classes,\
                                     orig_feats_length, target_feats_length,\
                                     scenario, tasks, data_dir, verbose=False):


    if dataset_name == 'EMBER':
        
        num_class = target_classes
        selected_classes = get_selected_classes(target_classes)
        
        # check for number of tasks
        if tasks > num_class:
            raise ValueError(f"EMBER experiments cannot have more than {num_class} tasks!")
            
        # configurations
        config = DATASET_CONFIGS[dataset_name]
        
        
        if scenario == 'class':
            initial_task_num_classes = init_classes
            if initial_task_num_classes > target_classes:
                raise ValueError(f"Initial Number of Classes cannot be more than {target_classes} classes!")


            left_tasks = tasks - 1 
            classes_per_task_except_first_task = int((num_class - initial_task_num_classes) / left_tasks)

            

            #print(selected_classes)
            first_task = list(range(initial_task_num_classes))

            labels_per_task = [first_task] + [list(initial_task_num_classes +\
                                               np.array(range(classes_per_task_except_first_task)) +\
                                               classes_per_task_except_first_task * task_id)\
                                              for task_id in range(left_tasks)]
            
            classes_per_task = classes_per_task_except_first_task
                               
        else:
            classes_per_task = int(np.floor(num_class / tasks))
            
            labels_per_task = [list(np.array(range(classes_per_task)) +\
                                classes_per_task * task_id) for task_id in range(tasks)]
        
        
        print(labels_per_task) 
        
        
        #data_dir = '../../../../ember2018/top_class_bases/top_classes_100' 
        data_dir = '/home/bae/continual-learning-malware/top_classes_100'
        x_train, y_train = get_ember_selected_class_data(data_dir, selected_classes, train=True)
        x_test, y_test = get_ember_selected_class_data(data_dir, selected_classes, train=False)
        

        standardization = StandardScaler()
        standard_scaler = standardization.fit(x_train)
        x_train = standard_scaler.transform(x_train)
        x_test = standard_scaler.transform(x_test)  

        ember_train, ember_test = (x_train, y_train), (x_test, y_test)



        # split them up into sub-tasks
        train_datasets = []
        test_datasets = []
        for labels in labels_per_task:
            #print(scenario)
            train_datasets.append(malwareSubDataset(ember_train, orig_feats_length,\
                                                    target_feats_length,\
                                                    labels))
            test_datasets.append(malwareSubDataset(ember_test, orig_feats_length,\
                                                   target_feats_length,\
                                                   labels))


    # If needed, update number of (total) classes in the config-dictionary
    config['classes'] = 100

    # Return tuple of train-, validation- and test-dataset, config-dictionary and number of classes per task
    return (int(y_train.shape[0]), (train_datasets, test_datasets), config, classes_per_task)


    
# specify available transforms.
AVAILABLE_TRANSFORMS = {
    'EMBER': [
        transforms.ToTensor(),
    ],
}



# specify configurations of available data-sets.
DATASET_CONFIGS = {
    'EMBER': {'size': 49, 'channels': 1, 'classes': 100},
}





class TransformedDataset(Dataset):
    '''Modify existing dataset with transform; for creating multiple MNIST-permutations w/o loading data every time.'''

    def __init__(self, original_dataset, transform=None, target_transform=None):
        super().__init__()
        self.dataset = original_dataset
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        (input, target) = self.dataset[index]
        if self.transform:
            input = self.transform(input)
        if self.target_transform:
            target = self.target_transform(target)
        return (input, target)





'''
print('running data.py')
(train_datasets, test_datasets), config, classes_per_task = get_malware_multitask_experiment(
    'splitMNIST', 'drebin', 2492, 2500, scenario='class', tasks=9,
    verbose=True, exception=True,
)
'''
#print(test_datasets)
