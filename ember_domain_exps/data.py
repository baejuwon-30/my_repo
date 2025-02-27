import copy
import numpy as np
from sklearn.utils import shuffle
from torchvision import datasets, transforms
from torch.utils.data import ConcatDataset, Dataset
import torch
from sklearn.preprocessing import StandardScaler

def get_continual_month_data(data_dir, month, train=True):
    
    if train:
        data_dir = data_dir + str(month) + '/'
        XY_train = np.load(data_dir + 'XY_train.npz')
        X_tr, Y_tr = XY_train['X_train'], XY_train['Y_train']

        return X_tr, Y_tr
    else:
        data_dir = data_dir + str(month) + '/'
        XY_test = np.load(data_dir + 'XY_test.npz')
        X_test, Y_test = XY_test['X_test'], XY_test['Y_test']

        return X_test, Y_test 


def get_task_continual_training_data(data_dir, current_task):
    
    X_tr, Y_train = get_continual_month_data(data_dir, current_task)
    
    X_train = []
    for i in X_tr: #make 2381 to 2401 so that the sqrt is 49
        i = np.array(list(i) + [0] * 20)
        X_train.append(i)
        
    X_train = np.float32(np.array(X_train))
    X_train, Y_train = shuffle(X_train, Y_train)
    
    print(f'Current Task month training {current_task} data X {X_train.shape} Y {Y_train.shape}')
    return X_train, Y_train


def get_task_continual_test_data(data_dir, current_task):
    
    X_te, Y_test = get_continual_month_data(data_dir, current_task, train=False)
    
    X_test = []
    for i in X_te: #make 2381 to 2401 so that the sqrt is 49
        i = np.array(list(i) + [0] * 20)
        X_test.append(i)

    X_test = np.float32(np.array(X_test))
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
    
    X_train, y_train = shuffle(X_train, y_train)
    X_test, y_test = shuffle(X_test, y_test)
    
    return (X_train, y_train), (X_test, y_test)

class malwareSubDatasetExemplars(Dataset):
    '''To sub-sample a dataset, taking only those samples with label in [sub_labels].

    After this selection of samples has been made, it is possible to transform the target-labels,
    which can be useful when doing continual learning with fixed number of output units.'''
    
    
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
    
    
class TransformedDataset(Dataset):
    '''Modify existing dataset with transform; for creating multiple MNIST-permutations w/o loading data every time.'''

    def __init__(self, original_dataset, transform=None, target_transform=None):
        super().__init__()
        self.dataset, self.targets = original_dataset
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        input, target = self.dataset[index], self.targets[index]
        
        return (input, target)    
    
    
    
    
def get_malware_multitask_experiment(name, dataset_name, orig_feats_length, target_feats_length,\
                                     scenario, tasks, data_dir="./datasets", only_config=False, verbose=False,
                                     exception=False):
    '''Load, organize and return train- and test-dataset for requested experiment.

    [exception]:    <bool>; if True, for visualization no permutation is applied to first task (permMNIST) or digits
                            are not shuffled before being distributed over the tasks (splitMNIST)'''

    # depending on experiment, get and organize the datasets
    if name == 'permMNIST':
        # configurations
        config = DATASET_CONFIGS['ember_domain']
        classes_per_task = config['classes']
        if not only_config:
            
            # all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06',
            #      '2018-07', '2018-08', '2018-09', '2018-10', '2018-11', '2018-12']
            
            all_task_months = ['2018-01', '2018-02', '2018-03', '2018-04', '2018-05', '2018-06']
            

            #data_dir = '../../../../ember2018/month_based_processing/'
            data_dir = '/home/bae/continual-learning-malware/ember_data/ember2018/month_based_processing_with_family_labels/'
            
            standardization = StandardScaler()
            # prepare datasets per task
            train_datasets = []
            test_datasets = []
            for task_id, current_task in enumerate(all_task_months):
                taskid_X_train, taskid_Y_train = get_task_continual_training_data(data_dir, current_task)
                taskid_X_test, taskid_Y_test = get_task_continual_test_data(data_dir, current_task)
                
                standard_scaler = standardization.partial_fit(taskid_X_train)
                taskid_X_train = standard_scaler.transform(taskid_X_train)
                taskid_X_test = standard_scaler.transform(taskid_X_test)
                taskid_X_train, taskid_Y_train = np.array(taskid_X_train, np.float32), np.array(taskid_Y_train, np.float32)
                taskid_X_test, taskid_Y_test = np.array(taskid_X_test, np.float32), np.array(taskid_Y_test, np.float32)                  
                
                train_datasets.append(TransformedDataset((taskid_X_train, taskid_Y_train)))
                test_datasets.append(TransformedDataset((taskid_X_test, taskid_Y_test)))
    else:
        raise RuntimeError('Given undefined experiment: {}'.format(name))

    # If needed, update number of (total) classes in the config-dictionary
    config['classes'] = 2 #classes_per_task if scenario=='domain' else classes_per_task*tasks

    # Return tuple of train-, validation- and test-dataset, config-dictionary and number of classes per task
    return config if only_config else ((train_datasets, test_datasets), config, classes_per_task)
#----------------------------------------------------------------------------------------------------------#


class SubDataset(Dataset):
    '''To sub-sample a dataset, taking only those samples with label in [sub_labels].

    After this selection of samples has been made, it is possible to transform the target-labels,
    which can be useful when doing continual learning with fixed number of output units.'''

    def __init__(self, original_dataset, sub_labels, target_transform=None):
        super().__init__()
        self.dataset = original_dataset
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
        sample = self.dataset[self.sub_indeces[index]]
        if self.target_transform:
            target = self.target_transform(sample[1])
            sample = (sample[0], target)
            #print(sample)
        return sample


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


'''
class TransformedDataset(Dataset):
    #Modify existing dataset with transform; for creating multiple MNIST-permutations w/o loading data every time.

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

#----------------------------------------------------------------------------------------------------------#


# specify available data-sets.
AVAILABLE_DATASETS = {
    'mnist': datasets.MNIST,
}

# specify available transforms.
AVAILABLE_TRANSFORMS = {
    'mnist': [
        transforms.Pad(2),
        transforms.ToTensor(),
    ],
    'mnist28': [
        transforms.ToTensor(),
    ],
}


# drebin --> 2492

# specify configurations of available data-sets.
DATASET_CONFIGS = {
    'mnist': {'size': 32, 'channels': 1, 'classes': 10},
    'mnist28': {'size': 28, 'channels': 1, 'classes': 10},
    'drebin': {'size': 50, 'channels': 1, 'classes': 18},
    'ember_general': {'size': 49, 'channels': 1, 'classes': 25},
    'ember_domain': {'size': 49, 'channels': 1, 'classes': 2},
}


#----------------------------------------------------------------------------------------------------------#


def get_multitask_experiment(name, scenario, tasks, data_dir="./datasets", only_config=False, verbose=False,
                             exception=False):
    '''Load, organize and return train- and test-dataset for requested experiment.

    [exception]:    <bool>; if True, for visualization no permutation is applied to first task (permMNIST) or digits
                            are not shuffled before being distributed over the tasks (splitMNIST)'''

    # depending on experiment, get and organize the datasets
    if name == 'permMNIST':
        # configurations
        config = DATASET_CONFIGS['mnist']
        classes_per_task = 10
        if not only_config:
            # prepare dataset
            train_dataset = get_dataset('mnist', type="train", permutation=None, dir=data_dir,
                                        target_transform=None, verbose=verbose)
            print(train_dataset.shape)
            test_dataset = get_dataset('mnist', type="test", permutation=None, dir=data_dir,
                                       target_transform=None, verbose=verbose)
            # generate permutations
            if exception:
                permutations = [None] + [np.random.permutation(config['size']**2) for _ in range(tasks-1)]
            else:
                permutations = [np.random.permutation(config['size']**2) for _ in range(tasks)]
            # prepare datasets per task
            train_datasets = []
            test_datasets = []
            for task_id, perm in enumerate(permutations):
                target_transform = transforms.Lambda(
                    lambda y, x=task_id: y + x*classes_per_task
                ) if scenario in ('task', 'class') else None
                train_datasets.append(TransformedDataset(
                    train_dataset, transform=transforms.Lambda(lambda x, p=perm: _permutate_image_pixels(x, p)),
                    target_transform=target_transform
                ))
                test_datasets.append(TransformedDataset(
                    test_dataset, transform=transforms.Lambda(lambda x, p=perm: _permutate_image_pixels(x, p)),
                    target_transform=target_transform
                ))
    elif name == 'splitMNIST':
        # check for number of tasks
        if tasks>10:
            raise ValueError("Experiment 'splitMNIST' cannot have more than 10 tasks!")
        # configurations
        config = DATASET_CONFIGS['mnist28']
        classes_per_task = int(np.floor(10 / tasks))
        if not only_config:
            # prepare permutation to shuffle label-ids (to create different class batches for each random seed)
            permutation = np.array(list(range(10))) if exception else np.random.permutation(list(range(10)))
            target_transform = transforms.Lambda(lambda y, p=permutation: int(p[y]))
            # prepare train and test datasets with all classes
            mnist_train = get_dataset('mnist28', type="train", dir=data_dir, target_transform=target_transform,
                                      verbose=verbose)
            mnist_test = get_dataset('mnist28', type="test", dir=data_dir, target_transform=target_transform,
                                     verbose=verbose)
            # generate labels-per-task
            labels_per_task = [
                list(np.array(range(classes_per_task)) + classes_per_task * task_id) for task_id in range(tasks)
            ]
            
            print(labels_per_task)
            
            # split them up into sub-tasks
            train_datasets = []
            test_datasets = []
            for labels in labels_per_task:
                target_transform = transforms.Lambda(
                    lambda y, x=labels[0]: y - x
                ) if scenario=='domain' else None
                train_datasets.append(SubDataset(mnist_train, labels, target_transform=target_transform))
                test_datasets.append(SubDataset(mnist_test, labels, target_transform=target_transform))
            
            
            #print(f'here {test_datasets}')
                

    else:
        raise RuntimeError('Given undefined experiment: {}'.format(name))

    # If needed, update number of (total) classes in the config-dictionary
    config['classes'] = classes_per_task if scenario=='domain' else classes_per_task*tasks

    # Return tuple of train-, validation- and test-dataset, config-dictionary and number of classes per task
    return config if only_config else ((train_datasets, test_datasets), config, classes_per_task)

'''
print('running data.py')
(train_datasets, test_datasets), config, classes_per_task = get_malware_multitask_experiment(
    'splitMNIST', 'drebin', 2492, 2500, scenario='class', tasks=9,
    verbose=True, exception=True,
)
'''
#print(test_datasets)
