#!/usr/bin/env bash

export PATH=$PATH:${HOME}/local_bin/miniconda3/envs/env_py310/bin
export PYTHONPATH=${PWD}

/home/yin/local_bin/miniconda3/envs/env_py310/bin/python3 ./script/pt_clm/pt_llama.py ./script/pt_clm/pt_llama_config.json
