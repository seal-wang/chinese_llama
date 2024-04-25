#!/usr/bin/env python3
from tokenization_llama_zh import LlamaZHTokenizer
from transformers import AutoTokenizer
import re
from opencc import OpenCC

opencc = OpenCC('t2s')

#A-Z: 0041-005A
#a-z: 0061-007A
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

normal_pattern = re.compile(r'[^[\u4E00-\u9FFF]&&[a-zA-Z0-9]]')
normal_pattern = re.compile(r'[^\u4e00-\u9fffA-Za-z0-9]')

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

def is_including_sp(s):
    for v in s:
        if normal_pattern.search(v):
            return True
    
    return False

def classify_tok(path='./'):
    tok = LlamaZHTokenizer.from_pretrained(path, trust_remote_code=True, num_image_tokens=0)
    print(len(tok))

    content = ''
    zh_num = 0
    en_num = 0
    full_list = []
    conten_list = []
    ko_list = []
    ja_list = []
    latin_list = []
    cyrillic_list = []
    tra_list = []
    sp_list = []
    for i in range(len(tok)):
        zh_flag = False
        token = tok.decode(i)
        full_list.append(token)

        for v in token:
            if 0x4E00 <= ord(v) and 0x9FFF >= ord(v):
                zh_num += 1
                zh_flag = True
                break
        
        if False == zh_flag:
            match_item = re.search(r'[a-zA-Z]', tok.decode(i))
            if match_item:
                en_num += 1

        if is_including_ko(token):
            ko_list.append((i,token))
            continue

        if is_including_ja(token):
            ja_list.append((i,token))
            continue

        if is_including_latin(token):
            latin_list.append((i,token))
            continue

        if is_including_cl(token):
            cyrillic_list.append((i,token))
            continue

        if is_including_tra(token):
            tra_list.append((i,token))
            continue

        if is_including_sp(token):
            sp_list.append((i,token))
            continue
        
        conten_list.append(token)
        special_str = f'\t{ord(token):04X}' if len(token) == 1 else ''
        content += f'{i:05}' + '\t' + token + special_str + '\n'
    
    no_repeate_full_list = []
    repeate_full_list = []
    repeate_num = 0
    for v in full_list:
        if v not in no_repeate_full_list:
            no_repeate_full_list.append(v)
        elif v not in repeate_full_list:
            repeate_full_list.append(v)
    
    with open('./content.txt', mode='w', encoding='utf-8') as f:
        f.write(content)

    with open('./ko.txt', mode='w', encoding='utf-8') as f:
        for v in ko_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')
    
    with open('./ja.txt', mode='w', encoding='utf-8') as f:
        for v in ja_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')
        
    with open('./latin.txt', mode='w', encoding='utf-8') as f:
        for v in latin_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')
    
    with open('./latin.txt', mode='w', encoding='utf-8') as f:
        for v in cyrillic_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')

    with open('./tra.txt', mode='w', encoding='utf-8') as f:
        for v in tra_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')

    with open('./sp.txt', mode='w', encoding='utf-8') as f:
        for v in sp_list:
            f.write(f'{v[0]:05}\t' + v[1] + '\n')

def dump_model(path='./'):
    tok = LlamaZHTokenizer.from_pretrained(path, trust_remote_code=True, num_image_tokens=0)
    tok_len = len(tok)
    print(tok_len)

    for i in range(tok_len):
        print(f"{i:04X}\t\t{tok.decode(i)}")

if __name__ == "__main__":
    # classify_tok()
    dump_model("./ll_new/")
