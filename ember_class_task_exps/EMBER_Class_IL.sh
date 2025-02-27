#!/bin/sh

NUM_TASK=2
SCENARIO=class
DATASET=EMBER
GPU_NUMBER=0



# # None
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=none --metrics --logger_file none --scenario=${SCENARIO}

# # Offline/Joint
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=offline --metrics --logger_file offline --scenario=${SCENARIO}

# # EWC
CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --ewc --lambda=5000 --metrics --logger_file ewc --scenario=${SCENARIO} 

# # EWC-O
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --ewc --online --lambda=5000 --gamma=1 --metrics --logger_file ewc_online --scenario=${SCENARIO}


# # SI
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --si --c=0.1 --metrics --logger_file si --scenario=${SCENARIO} 




# # LwF
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET}  --tasks=${NUM_TASK} --replay=current --distill --metrics --logger_file lwf --scenario=${SCENARIO} 

# # GR
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=generative --metrics --logger_file gr --scenario=${SCENARIO}

# # GR-D
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=generative --distill --metrics --logger_file gr_distill --scenario=${SCENARIO} 

# # RtF
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=generative --distill --feedback --metrics --logger_file rtf --scenario=${SCENARIO}




# # ER
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=exemplars --budget=2000 --metrics --logger_file experience_replay --scenario=${SCENARIO}

# # A-GEM
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --replay=exemplars --agem --budget=2000 --metrics --logger_file agem --scenario=${SCENARIO}


# # i-CaRL
# CUDA_VISIBLE_DEVICES=${GPU_NUMBER} python main.py --data_set=${DATASET} --tasks=${NUM_TASK} --icarl --budget=2000 --metrics --logger_file icarl --scenario=${SCENARIO} 













