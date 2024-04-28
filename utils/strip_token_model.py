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

#C0 Controls and Basic Latin: 0000–007F
#C1 Controls and Latin-1 Supplement：0080–00FF
#Latin Extended-A:0100–017F
#Latin Extended-B:0180–024F
#Latin Extended-C:2C60–2C7F
#Latin Extended-D:A720–A7FF
#Latin Extended Additional: 1E00–1EFF
#韩文拼音(Hangul Syllables)：AC00-D7AF
#韩文字母：1100-11FF
#韩文兼容字母:3130-318F
#日文平假名:3040-309F
#日文片假名:30A0-30FF
#日文片假名拼音扩展:31F0-31FF
#Cyrillic:0400–04FF

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

def is_including_ko(s):
    for v in s:
        unicode_id = ord(v)
        if (0x1100 <= unicode_id and 0x11FF >= unicode_id) \
            or (0x3130 <= unicode_id and 0x318F >= unicode_id) \
            or (0xAC00 <= unicode_id and 0xD7AF >= unicode_id):
            return True
    
    return False

def is_including_ja(s):
    for v in s:
        unicode_id = ord(v)
        if (0x3040 <= unicode_id and 0x309F >= unicode_id) \
            or (0x30A0 <= unicode_id and 0x30FF >= unicode_id) \
            or (0x31F0 <= unicode_id and 0x31FF >= unicode_id):
            return True
    
    return False

def is_including_latin(s):
    for v in s:
        unicode_id = ord(v)
        if (0x000 <= unicode_id and 0x0020 >= unicode_id) \
            or (0x0080 <= unicode_id and 0x000F >= unicode_id) \
            or (0x0100 <= unicode_id and 0x017F >= unicode_id) \
            or (0x0180 <= unicode_id and 0x024F >= unicode_id) \
            or (0x2C60 <= unicode_id and 0x2C7F >= unicode_id) \
            or (0xA720 <= unicode_id and 0xA7FF >= unicode_id) \
            or (0x1E00 <= unicode_id and 0x1EFF >= unicode_id):
            return True
    
    return False

def is_including_cl(s):
    for v in s:
        unicode_id = ord(v)
        if (0x0400 <= unicode_id and 0x04FF >= unicode_id):
            return True
    
    return False

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

def is_retain(index, piece):
    p = piece.piece
    if is_including_ko(p) or is_including_ja(p)\
    or is_including_cl(p)\
    or is_including_tra(p) or is_including_low_freq_en(piece):
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
