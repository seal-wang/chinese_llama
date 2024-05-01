#!/usr/bin/env bash

export PATH=$PATH:/home/yin/local_bin/miniconda3/envs/env_py310/bin
rm -rf output/* cache_dir/*


/home/yin/local_bin/miniconda3/envs/env_py310/bin/python3 sft_llama.py run_config.json
