#!/usr/bin/env python3
import sys
import torch
from transformers import GenerationConfig
from transformers import LlamaForCausalLM
from llama_zh.tokenizer.tokenization_llama_zh import LlamaZHTokenizer

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(checkpoint_path)
    model = LlamaForCausalLM.from_pretrained(checkpoint_path).to(device)
    tokenizer = LlamaZHTokenizer.from_pretrained(checkpoint_path)

    config_dict = {
        "temperature": 0.5,
        "do_sample": False,
        "top_k": 20,
        "top_p": 0.5,
        "num_beams": 1,
        "repetition_penalty": 1.4,
        "max_new_tokens": 300
    }
    
    gen_config = GenerationConfig(
        max_length=10,
        temperature=0.3,
        top_k=20,
        top_p=0.5,
        do_sample=True,
        num_beams=1,
        repetition_penalty=1.1,
        max_new_tokens=300,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )

    print("start chat")

    while True:
        print("用户：", end="")
        text = input()

        tokens = tokenizer(text)
        input_ids = torch.LongTensor([tokens.input_ids]).to(device)
        outputs = model.generate(inputs=input_ids, generation_config=gen_config)
        outs = tokenizer.decode(outputs[0])
        print("机器:", outs)

if __name__ == "__main__":
    checkpoint_path = sys.argv[1] if len(sys.argv) >= 2 else './'
    main()
