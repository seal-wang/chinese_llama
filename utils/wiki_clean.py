#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主要用于解析wiki
"""

from gensim.corpora.wikicorpus import extract_pages,filter_wiki
import bz2file
import re
from opencc import OpenCC 
from tqdm import tqdm
import codecs
import argparse

size_per_file = 5*(2**20)
openCC = OpenCC('t2s')

def match_chinese_variants(text):
    text = text.replace('-{}-', "")
    pattern = re.compile(r'-{.*?}-')
    matches = pattern.findall(text)
    for substr in matches:
        if "zh-" in substr and ":" in substr:
            if "zh-hans:" in substr:
                zh_prefix = "zh-hans:"
            elif "zh-cn:" in substr:
                zh_prefix = "zh-cn:"
            else:
                zh_prefix = "zh-"

            substr_index = substr.find(zh_prefix)
            start_index = substr.find(":", substr_index) + 1
            end_index = substr.find(";", substr_index)
            if end_index < 0:
                end_index = len(substr) - 2
            new_substr = substr[start_index:end_index]
        else:
            new_substr = substr[2:-2]
        text = text.replace(substr, new_substr)
    return text

def match_string(s):
    pattern1 = re.compile(r'[a-zA-Z0-9,;.?!:&()|–\-—æ/\'"= •\xa0]+')
    pattern2 = re.compile(r' p{1,2}(?:,|\.)')
    pattern4 = re.compile(r'[0-9]+。')
    pattern5 = re.compile(r'p=\d+')
    pattern6 = re.compile(r'\d+')
    
    s = match_chinese_variants(s)
    return s
    matches = pattern1.findall(s)
    for substr in matches:
        if 'date=' in substr or len(pattern2.findall(substr)) > 0 or len(pattern4.findall(substr)) > 0 or len(pattern5.findall(substr)) > 0:
            if len(pattern5.findall(substr)) > 0:
                substr_index = s.find(substr)
                if substr_index >= 0:
                    s_len = len(s)
                    start_index = substr_index + len(substr)
                    substr_match_list = pattern6.findall(substr)
                    if (start_index < line_len and s[start_index] == "年") and len(substr_match_list[-1]) > 4:
                        substr = substr[:-4]
                    elif (start_index+1 < line_len and s[start_index:start_index+2] == "世纪") and len(substr_match_list[-1]) > 2:
                        substr = substr[:-2]
            s = s.replace(substr, '')
    return s

def strip_note(s):
    match = re.search(r'\n={2,}.*?(?:注解|脚注|参[见考]|注释|参考文献|外部[链连]接|参考资料|(延伸|扩展)阅读).*?={2}', s)
    if match:
        s = s[:match.start()+1]
    return s

def get_title(d):
    s = d[1]
    key_word = '数学'
    if (key_word == d[0] or key_word == openCC.convert(d[0])) and len(d[1]) > 100:
        with open("/home/yin/work/other/test/pp_data/wiki_data/compare/old.txt", mode='w') as f:
            f.write(d[1])
            quit()
    return ''
    with open("/home/yin/work/other/test/pp_data/wiki_data/compare/new.txt", mode='w') as f:
        s = filter_wiki(d[1])
        f.write(s)

def strip_last_pair_symbol(s, left_sym, right_sym):
    while True:
        s_index = s.rfind(left_sym)
        e_index = s.find(right_sym, s_index)
        if s_index < 0 or e_index < s_index:
            break
        else:
            s = s[:s_index] + s[e_index+len(right_sym):]

    return s

def find_match_symbol(s, left_sym, right_sym):
    s_index = s.find(left_sym)
    if s_index < 0:
        return -1, -1

    e_index = s_index
    right_sym_len = len(right_sym)
    while True:
        e_index = s.find(right_sym, e_index)
        if e_index < s_index:
            s = ''
            break
        else:
            e_index += right_sym_len
            left_sym_num = s[s_index:e_index].count(left_sym)
            right_sym_num = s[s_index:e_index].count(right_sym)
            if left_sym_num == right_sym_num:
                return s_index, e_index

    return -1, -1

def clean_file(s):
    match_list = re.findall(r'\[\[(?:File|file|Image|文件|档案):', s)
    for match in match_list:
        index = s.find(match)
        if index < 0:
            continue
        s_index, e_index = find_match_symbol(s[index:], '[[', ']]')
        if 0 <= s_index and s_index < e_index:
            s = s[:index] + s[index:][:s_index] + s[index:][e_index:]

    return s

def clean_table(s):
    # match_list = re.findall(r'\{\|.*?[cC]lass.*?wikitable', s)
    match_list = re.findall(r'\{\|', s)
    for match in match_list:
        index = s.find(match)
        if index < 0:
            continue
        s_index, e_index = find_match_symbol(s[index:], '{|', '|}')
        if 0 <= s_index and s_index < e_index:
            s = s[:index] + s[index:][:s_index] + s[index:][e_index:]

    match_list = re.findall(r'<table\s', s)
    for match in match_list:
        index = s.find(match)
        if index < 0:
            continue
        s_index, e_index = find_match_symbol(s[index:], '<table', '</table>')
        if 0 <= s_index and s_index < e_index:
            s = s[:index] + s[index:][:s_index] + s[index:][e_index:]

    return s

def clean_audio(s):
    match_list = re.findall(r'（\{\{(?:Audio|IPAc)', s)
    for match in match_list:
        index = s.find(match)
        if index < 0:
            continue
        s_index, e_index = find_match_symbol(s[index:], '（', '）')
        if 0 <= s_index and s_index < e_index:
            s = s[:index] + s[index:][:s_index] + s[index:][e_index:]
    
    return s

def clean_lang(s):
    match_list = re.findall(r"（\{\{.*?\}\}）", s, re.S)
    for match in match_list:
        index = s.find(match)
        if index < 0:
            continue
        sub_str = s[index:]
        s_index, e_index = find_match_symbol(sub_str, "{{", "}}")
        if 0 <= s_index and s_index < e_index:
            if any(v in sub_str[s_index:e_index] for v in ["lang-", "Lang-"]):
                s = s.replace(sub_str[s_index:e_index], sub_str[s_index:e_index].split("|")[-1][:-2])
            elif any(v in sub_str[s_index:e_index] for v in ["link-", "le|", "Le|"]):
                s = s.replace(sub_str[s_index:e_index], sub_str[s_index:e_index].split("|")[1].strip())
            else:
                s = s.replace(sub_str[s_index:e_index], '')
    return s

def parse_date(s):
    start_index = 0
    year_pattern = re.compile(r'\d+[?:年|世纪]')
    month_pattern = re.compile(r'\d+[?:月|日]')
    while True:
        start_index = re.search(r"\{\{[bB]d\|", s)
        if not start_index:
            break
        start_index = start_index.start()
        end_index = start_index
        while True:
            end_index = s.find("}}", end_index+2)
            if end_index < start_index:
                break
            if s[start_index:end_index+2].count("{{") == s[start_index:end_index+2].count("}}"):
                break

        if end_index > start_index:
            strip_str = s[start_index+2:end_index]
            strip_str = strip_last_pair_symbol(strip_str, "{{", "}}")
            strip_str = strip_last_pair_symbol(strip_str, "<ref>", "</ref>")
            data_list = strip_str[3:].split("|")
            new_str = ''
            for v in data_list[:5 if len(data_list) > 5 else len(data_list)]:
                if (year_pattern.findall(v) or (len(v) > 0 and v in "?？")) and len(new_str) > 0 and '-' not in new_str:
                    new_str += '-'
                if len(year_pattern.findall(v)) > 0 or len(month_pattern.findall(v)) > 0 or (len(v) > 0 and v in "?？"):
                    new_str += v
            s = s.replace(s[start_index:end_index+2], new_str)
        else:
            s = re.sub(r"\{\{[bB]d\|", '', s, count=1)

    return s

def wiki_replace(d):
    s = d[1]
    s = openCC.convert(s)
    s = strip_note(s)
    s = re.sub('\{\|[ ]{0,2}class="wikitable".*?\n\|\}|(?:<br />|<br/>|<nowiki/>)', '', s, flags=re.S)
    s = re.sub('<ref([> ].*?)(</ref>|/>)', '', s, flags=re.S)
    s = clean_file(s)
    s = clean_table(s)
    s = parse_date(s)
    s = clean_lang(s)
    s = clean_audio(s)    
    s = re.sub('(?:<gallery[> ][\s\S]*?</gallery>|（）)', '', s, flags=re.S)
    s = filter_wiki(s)
    s = '\n'.join(line.strip() for line in s.split('\n') if (not re.match("File:", line) and len(line.strip()) > 0))
    s = re.sub('(?:\n{2,}|\n:(?!:)|\n[：;])', '\n', s)
    s = re.sub('\'{2,}|={2,5}[^=\n]{1,}?={2,5}\n', '', s)
    s = match_string(s)
    return s

def test_fun():
    with open("/home/yin/work/other/test/pp_data/wiki_data/tmp_file.txt", mode='r') as f:
        s = f.read()
    
    s, ret_str = parse_date(s)

    with open("/home/yin/work/other/test/pp_data/wiki_data/tmp_file.txt", mode='a') as f:
        f.write("\n\n\n" + s)
    quit()

def wiki_process(input_file,save_path):
    # wikicorpus解析
    wiki = extract_pages(bz2file.open(input_file))
    # 处理并导出
    article_num = 0
    file_len = 0
    file_cache = ''
    file_index = 0
    f = codecs.open(save_path + f"parse_00000.txt", 'w', encoding='utf-8')
    w = tqdm(wiki, desc=u'')
    for d in w:
        # wiki_replace(d)
        # get_title(d)
        # continue 
        if not re.findall('^[a-zA-Z]+:', d[0]) and d[0] and not re.findall(u'^#', d[1]) and '年表' not in d[0]:
            s = '=====' + openCC.convert(d[0]) + '=====\n'+ wiki_replace(d) +'\n\n\n\n'
            file_len += len(s.encode('utf-8'))
            file_cache = file_cache + s
            if file_len >= size_per_file:
                f.write(file_cache)
                f.close()
                file_len = 0
                file_cache = ''
                file_index += 1
                f = codecs.open(save_path + f"parse_{file_index:05}.txt", 'w', encoding='utf-8')
                w.set_description(u'已获取%s篇文章'%article_num)
            article_num += 1
    if len(file_cache) > 0:
        f.write(file_cache)
        f.close()
  
def parse_args():
    parser = argparse.ArgumentParser(description = 'clean wiki corpus')
    parser.add_argument('-i', '--input_file', type = str, required = True, nargs = '+', metavar = '', default = [], help = 'input file')
    parser.add_argument('-o', '--output_file', type = str, required = True, metavar = '', help = 'output file')
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = parse_args()
    for input_file in args.input_file:
        wiki_process(input_file, args.output_file)
