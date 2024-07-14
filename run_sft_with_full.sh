#!/usr/bin/env bash

export PATH=$PATH:${HOME}/local_bin/miniconda3/envs/env_py310/bin
export PYTHONPATH=${PWD}

/home/yin/local_bin/miniconda3/envs/env_py310/bin/python3 ./script/sft_with_full/sft_llama_with_full.py ./script/sft_with_full/sft_llama_with_full_config.json
