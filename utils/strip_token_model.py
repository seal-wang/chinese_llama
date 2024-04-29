#!/usr/bin/env python3
# ./strip_token_model.py -i old_token.model -o new_token.model [-a add_file.txt]
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]="python"
from sentencepiece import sentencepiece_model_pb2 as sp_pb2_model
import sentencepiece as spm
import argparse
from opencc import OpenCC
import json
import re

opencc = OpenCC('t2s')
start_en_pattern = re.compile(r"[^a-zA-Z]")

strip_list = [
    [0x0080, 0x00FF],
    [0x0100, 0x017F],
    [0x0180, 0x024F],
    [0x0250, 0x02AF],
    [0x02B0, 0x02FF],
    [0x0300, 0x036F],
    [0x0370, 0x03FF],
    [0x0400, 0x04FF],
    [0x0530, 0x058F],
    [0x0590, 0x05FF],
    [0x0600, 0x06FF],
    [0x0700, 0x074F],
	[0x07C0, 0x07FF],
    [0x0900, 0x097F],
    [0x0980, 0x09FF],
    [0x0A00, 0x0A7F],
	[0x0A80, 0x0AFF],
    [0x0B80, 0x0BFF],
    [0x0C00, 0x0C7F],
	[0x0C80, 0x0CFF],
	[0x0D00, 0x0D7F],
	[0x0D80, 0x0DFF],
    [0x0E00, 0x0E7F],
	[0x0F00, 0x0FFF],
    [0x1000, 0x109F],
    [0x10A0, 0x10FF],
    [0x1100, 0x11FF],
    [0x1780, 0x17FF],
    [0x1D00, 0x1D7F],
    [0x1E00, 0x1EFF],
    [0x1F00, 0x1FFF],
    [0x2000, 0x2011], [0x2020, 0x2021], [0x2027, 0x202F], [0x203B, 0x206F],
    [0x2070, 0x209F],
    [0x20A0, 0x20CF],
    [0x20D0, 0x20FF],
    [0x2190, 0x21FF],
    [0x2300, 0x23FF],
    [0x2500, 0x257F],
    [0x2580, 0x259F],
    [0x25A0, 0x25FF],
    [0x2600, 0x26FF],
    [0x2700, 0x27BF],
    [0x27C0, 0x27EF],
	[0x27F0, 0x27FF],
	[0x2800, 0x28FF],
	[0x2900, 0x297F],
    [0x2B00, 0x2BFF],
    [0x2D30, 0x2D7F],
    [0x2E00, 0x2E7F],
    [0x2F00, 0x2FDF],
    [0x3004, 0x3007], [0x300E, 0x301B], [0x3020, 0x303F],
    [0x3040, 0x309F],
    [0x30A0, 0x30FF],
    [0x3100, 0x312F],
    [0x3130, 0x318F],
    [0x31F0, 0x31FF],
	[0xA490, 0xA4CF],
    [0xAC00, 0xD7AF],
    [0xE000, 0xF8FF],
    [0xF900, 0xFAFF],
    [0xFB00, 0xFB4F],
    [0xFE00, 0xFE0F],
    [0xFE30, 0xFE4F],
    [0xFE50, 0xFE6F],
    [0xFE70, 0xFEFF],
    [0xFFF0, 0xFFFF]    
]

en_pieces = []
added_en_pieces = []

def get_token_dict(index, p):
    piece_dict = {
        "id": f"{index:04X}",
        "piece": p.piece,
        "score": p.score,
        "type": p.type
    }

    return piece_dict

def init_en_pieces(file):
    global en_pieces
    if file:
        with open(file, mode="r", encoding="utf-8") as f:
            content = f.read()
            en_pieces = content.split("\n")

def is_including_tra(s):
    if s != opencc.convert(s):
        return True
    
    return False

def is_including_low_freq_en(piece):
    global en_pieces
    global added_en_pieces
    s = piece.piece
    s = s[1:] if s[0] == "\u2581" else s
    match = start_en_pattern.search(s)
    if not match and len(s) >= 1:
        s = s.lower()
        if s in en_pieces and s not in added_en_pieces:
            added_en_pieces.append(s.lower())
            piece.piece = piece.piece.lower()
            return False
        else:
            return True

    return False

def is_including_sp(s):
    for ch in s:
        index = ord(ch)
        if index == 0x2581:
            continue
        for t in strip_list:
            if t[0] <= index and index <= t[1]:
                return True
    
    return False

def is_retain(index, piece):
    p = piece.piece
    if is_including_sp(p) or is_including_tra(p)\
    or is_including_low_freq_en(piece):
        return False

    return True

def edit_tok_model(input_file, output_file, add_file):
    global en_pieces
    assert os.path.isfile(input_file)

    init_en_pieces(add_file)

    old_sp_model = spm.SentencePieceProcessor()
    old_sp_model.Load(input_file)
    old_spm = sp_pb2_model.ModelProto()
    old_spm.ParseFromString(old_sp_model.serialized_model_proto())
    new_spm = sp_pb2_model.ModelProto()

    for i, piece in enumerate(old_spm.pieces):
        if is_retain(i, piece):
            new_spm.pieces.append(piece)

    new_str = new_spm.SerializeToString() + old_spm.SerializeToString()[-242:]
    with open(output_file, mode='wb') as f:
        f.write(new_str)

def parse_args():
    parser = argparse.ArgumentParser(description = 'pack hot update res')
    parser.add_argument('-i', '--input_file', type = str, required = True, metavar = '', help = 'input file')
    parser.add_argument('-o', '--output_file', type = str, required = True, metavar = '', help = 'output file')
    parser.add_argument('-a', '--add_file', type = str, metavar = '', help = 'add file')
    args = parser.parse_args()

    return args

def dump_model(input_file, output_file):
    path = os.path.dirname(output_file)
    name_list = ["/old_vocabulary.json", "/new_vocabulary.json"]
    for i, file in enumerate([input_file, output_file]):
        sp_proc = spm.SentencePieceProcessor()
        sp_proc.Load(file)
        sp_model = sp_pb2_model.ModelProto()
        sp_model.ParseFromString(sp_proc.serialized_model_proto())

        piece_list = []
        for id, piece in enumerate(sp_model.pieces):
            piece_list.append(get_token_dict(id, piece))
        piece_num = len(piece_list)
        piece_list.insert(0, {"num": piece_num})
        with open(path + name_list[i], mode='w', encoding="utf-8") as f:
            json.dump(piece_list, f, sort_keys=True, indent=4, separators=(',', ':'), ensure_ascii=False)

if __name__ == "__main__":
    args = parse_args()
    edit_tok_model(args.input_file, args.output_file, args.add_file)
    dump_model(args.input_file, args.output_file)
