# python merge_lora.py -b base_path -l lora_path -o output_path
from transformers import AutoModelForCausalLM
from peft import PeftModel
import shutil
import argparse

def merge_lora(base_path, adapter_path, save_path):
    base_model = AutoModelForCausalLM.from_pretrained(base_path, trust_remote_code = True)
    lora_model = PeftModel.from_pretrained(base_model, adapter_path)
    lora_model = lora_model.merge_and_unload()

    shutil.rmtree(save_path)
    lora_model.save_pretrained(save_path)

    shutil.copy(adapter_path+"/tokenization_llama_zh.py", save_path)
    shutil.copy(adapter_path+"/tokenizer_config.json", save_path)
    shutil.copy(adapter_path+"/special_tokens_map.json", save_path)
    shutil.copy(adapter_path+"/added_tokens.json", save_path)
    shutil.copy(adapter_path+"/ice_text.model", save_path)

def parse_args():
    parser = argparse.ArgumentParser(description = 'merge base and lora')
    parser.add_argument('-b', '--base_path', type = str, required = True, metavar = '', help = 'base path')
    parser.add_argument('-l', '--lora_path', type = str, required = True, metavar = '', help = 'lora path')
    parser.add_argument('-o', '--output_path', type = str, required = True, metavar = '', help = 'output path')
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = parse_args()
    merge_lora(args.base_path, args.lora_path, args.output_path)
