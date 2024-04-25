#!/usr/bin/env python3
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]="python"
from tokenization_llama_zh import LlamaZHTokenizer
from sentencepiece import sentencepiece_model_pb2 as sp_pb2_model
import sentencepiece as spm


old_sp_model_file = "./ice_text.model"
new_sp_model_file = "./new.model"

old_sp_model = spm.SentencePieceProcessor()
old_sp_model.Load(old_sp_model_file)
old_spm = sp_pb2_model.ModelProto()
old_spm.ParseFromString(old_sp_model.serialized_model_proto())
new_spm = sp_pb2_model.ModelProto()

def is_retain(index, piece):
    if index == 0 or index > 300:
        return True
    return False

for i, piece in enumerate(old_spm.pieces):
    if is_retain(i, piece):
        new_spm.pieces.append(piece)

with open(new_sp_model_file, 'wb') as f:
    f.write(new_spm.SerializeToString())

tokenizer = LlamaZHTokenizer(vocab_file=new_sp_model_file)
tokenizer.save_pretrained("./new_model/")

os.remove(new_sp_model_file)
