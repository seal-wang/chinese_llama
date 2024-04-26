#!/usr/bin/env python3
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]="python"
from sentencepiece import sentencepiece_model_pb2 as sp_pb2_model
import sentencepiece as spm
import argparse

def is_retain(index, piece):
        if index <= 0xFCFC:
            return True
        return False

def edit_tok_model(input_file, output_file):
    assert os.path.isfile(input_file)

    old_sp_model = spm.SentencePieceProcessor()
    old_sp_model.Load(input_file)
    old_spm = sp_pb2_model.ModelProto()
    old_spm.ParseFromString(old_sp_model.serialized_model_proto())
    new_spm = sp_pb2_model.ModelProto()

    for i, piece in enumerate(old_spm.pieces):
        if is_retain(i, piece):
            new_spm.pieces.append(piece)

    new_str = new_spm.SerializeToString() + old_spm.SerializeToString()[-242:]
    with open(output_file, 'wb') as f:
        f.write(new_str)

def parse_args():
    parser = argparse.ArgumentParser(description = 'pack hot update res')
    parser.add_argument('-i', '--input_file', type = str, required = True, metavar = '', help = 'input file')
    parser.add_argument('-o', '--output_file', type = str, required = True, metavar = '', help = 'output file')
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = parse_args()
    edit_tok_model(args.input_file, args.output_file)
