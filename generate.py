#!/usr/bin/env python3
import sys
import torch
from transformers import GenerationConfig
from transformers import LlamaForCausalLM
from llama_zh.tokenizer.tokenization_llama_zh import LlamaZHTokenizer

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LlamaForCausalLM.from_pretrained(checkpoint_path).to(device)
    tokenizer = LlamaZHTokenizer.from_pretrained(checkpoint_path)

    config_dict = {
        "do_sample": False,
        "top_k": 20,
        "top_p": 0.5,
        "temperature": 1,
        "num_beams": 1,
        "repetition_penalty": 1.4,
        "max_new_tokens": 300
    }
    
    gen_config = GenerationConfig(
        do_sample=config_dict["do_sample"],
        top_k=config_dict["top_k"],
        top_p=config_dict["top_p"],
        temperature=config_dict["temperature"],
        num_beams=config_dict["num_beams"],
        repetition_penalty=config_dict["repetition_penalty"],
        max_new_tokens=config_dict["max_new_tokens"],
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    print("start chat")
    q_list = ["请介绍一下北京", "列举5种常见的水果", "世界上最大的动物是？", "请推荐一份健康的早餐", "高血压患者在饮食上有什么需要注意的点？", "你知道西安有什么特色美食吗？"]

    # while True:
        # print("用户：", end="")
        # text = input()
    for v in q_list:
        text = v
        tokens = tokenizer(text)
        input_ids = torch.LongTensor([tokens.input_ids]).to(device)
        outputs = model.generate(inputs=input_ids, generation_config=gen_config)
        outs = tokenizer.decode(outputs[0][input_ids.shape[-1]:])
        print("用户:", text)
        print("机器:", outs.rstrip(" <eop>"))

if __name__ == "__main__":
    checkpoint_path = sys.argv[1] if len(sys.argv) >= 2 else './'
    main()
