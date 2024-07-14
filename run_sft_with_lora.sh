#!/usr/bin/env bash

export PATH=$PATH:${HOME}/local_bin/miniconda3/envs/env_py310/bin
export PYTHONPATH=${PWD}

/home/yin/local_bin/miniconda3/envs/env_py310/bin/python3 script/sft_with_lora/sft_llama_with_lora.py script/sft_with_lora/sft_llama_with_lora_config.json
