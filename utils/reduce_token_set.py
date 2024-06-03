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

unicode_list = [
    {
        "dsc":"0x0000-0x007F 基本拉丁文 Basic Latin",
        "s":"0x0000",
        "e":"0x007F"
    },
    {
        "dsc":"0x0080-0x00FF 拉丁字母补充-1 Latin-1 Supplement",
        "s":"0x0080",
        "e":"0x00FF"
    },
    {
        "dsc":"0x0100-0x017F 拉丁字母扩展-A Latin Extended-A",
        "s":"0x0100",
        "e":"0x017F"
    },
    {
        "dsc":"0x0180-0x024F 拉丁字母扩展-B Latin Extended-B",
        "s":"0x0180",
        "e":"0x024F"
    },
    {
        "dsc":"0x0250-0x02AF 国际音标扩展 IPA Extensions",
        "s":"0x0250",
        "e":"0x02AF"
    },
    {
        "dsc":"0x02B0-0x02FF 占位修饰符号 Spacing Modifier Letters",
        "s":"0x02B0",
        "e":"0x02FF"
    },
    {
        "dsc":"0x0300-0x036F 结合附加符号 Combining Diacritics Marks",
        "s":"0x0300",
        "e":"0x036F"
    },
    {
        "dsc":"0x0370-0x03FF 希腊字母及科普特字母 Greek and Coptic",
        "s":"0x0370",
        "e":"0x03FF"
    },
    {
        "dsc":"0x0400-0x04FF 西里尔字母 Cyrillic",
        "s":"0x0400",
        "e":"0x04FF"
    },
    {
        "dsc":"0x0500-0x052F 西里尔字母补充 Cyrillic Supplement",
        "s":"0x0500",
        "e":"0x052F"
    },
    {
        "dsc":"0x0530-0x058F 亚美尼亚字母 Armenian",
        "s":"0x0530",
        "e":"0x058F"
    },
    {
        "dsc":"0x0590-0x05FF 希伯来文 Hebrew",
        "s":"0x0590",
        "e":"0x05FF"
    },
    {
        "dsc":"0x0600-0x06FF 阿拉伯文 Arabic",
        "s":"0x0600",
        "e":"0x06FF"
    },
    {
        "dsc":"0x0700-0x074F 叙利亚文 Syriac",
        "s":"0x0700",
        "e":"0x074F"
    },
    {
        "dsc":"0x0750-0x077F 阿拉伯字母补充 Arabic Supplement",
        "s":"0x0750",
        "e":"0x077F"
    },
    {
        "dsc":"0x0780-0x07BF 它拿字母 Thaana",
        "s":"0x0780",
        "e":"0x07BF"
    },
    {
        "dsc":"0x07C0-0x07FF 西非书面文字 N'Ko",
        "s":"0x07C0",
        "e":"0x07FF"
    },
    {
        "dsc":"0x0800-0x083F 撒玛利亚字母 Samaritan",
        "s":"0x0800",
        "e":"0x083F"
    },
    {
        "dsc":"0x0840-0x085F 曼达文字 Mandaic",
        "s":"0x0840",
        "e":"0x085F"
    },
    {
        "dsc":"0x0860-0x086F 叙利亚文补充 Syriac Supplement",
        "s":"0x0860",
        "e":"0x086F"
    },
    {
        "dsc":"0x0870-0x089F 阿拉伯文扩展-B Arabic Extended-B",
        "s":"0x0870",
        "e":"0x089F"
    },
    {
        "dsc":"0x08A0-0x08FF 阿拉伯文扩展-A Arabic Extended-A",
        "s":"0x08A0",
        "e":"0x08FF"
    },
    {
        "dsc":"0x0900-0x097F 天城文 Devanagari",
        "s":"0x0900",
        "e":"0x097F"
    },
    {
        "dsc":"0x0980-0x09FF 孟加拉文 Bengali",
        "s":"0x0980",
        "e":"0x09FF"
    },
    {
        "dsc":"0x0A00-0x0A7F 古木基文 Gurmukhi",
        "s":"0x0A00",
        "e":"0x0A7F"
    },
    {
        "dsc":"0x0A80-0x0AFF 古吉拉特文 Gujarati",
        "s":"0x0A80",
        "e":"0x0AFF"
    },
    {
        "dsc":"0x0B00-0x0B7F 奥里亚文 Oriya",
        "s":"0x0B00",
        "e":"0x0B7F"
    },
    {
        "dsc":"0x0B80-0x0BFF 泰米尔文 Tamil",
        "s":"0x0B80",
        "e":"0x0BFF"
    },
    {
        "dsc":"0x0C00-0x0C7F 泰卢固文 Telugu",
        "s":"0x0C00",
        "e":"0x0C7F"
    },
    {
        "dsc":"0x0C80-0x0CFF 卡纳达文 Kannada",
        "s":"0x0C80",
        "e":"0x0CFF"
    },
    {
        "dsc":"0x0D00-0x0D7F 马拉雅拉姆文 Malayalam",
        "s":"0x0D00",
        "e":"0x0D7F"
    },
    {
        "dsc":"0x0D80-0x0DFF 僧伽罗文 Sinhala",
        "s":"0x0D80",
        "e":"0x0DFF"
    },
    {
        "dsc":"0x0E00-0x0E7F 泰文 Thai",
        "s":"0x0E00",
        "e":"0x0E7F"
    },
    {
        "dsc":"0x0E80-0x0EFF 老挝文 Lao",
        "s":"0x0E80",
        "e":"0x0EFF"
    },
    {
        "dsc":"0x0F00-0x0FFF 藏文 Tibetan",
        "s":"0x0F00",
        "e":"0x0FFF"
    },
    {
        "dsc":"0x1000-0x109F 缅甸文 Myanmar",
        "s":"0x1000",
        "e":"0x109F"
    },
    {
        "dsc":"0x10A0-0x10FF 格鲁吉亚字母 Georgian",
        "s":"0x10A0",
        "e":"0x10FF"
    },
    {
        "dsc":"0x1100-0x11FF 谚文字母 Hangul Jamo",
        "s":"0x1100",
        "e":"0x11FF"
    },
    {
        "dsc":"0x1200-0x137F 吉兹字母 Ethiopic",
        "s":"0x1200",
        "e":"0x137F"
    },
    {
        "dsc":"0x1380-0x139F 吉兹字母补充 Ethiopic Supplement",
        "s":"0x1380",
        "e":"0x139F"
    },
    {
        "dsc":"0x13A0-0x13FF 切罗基字母 Cherokee",
        "s":"0x13A0",
        "e":"0x13FF"
    },
    {
        "dsc":"0x1400-0x167F 统一加拿大原住民音节文字 Unified Canadian Aboriginal Syllabics",
        "s":"0x1400",
        "e":"0x167F"
    },
    {
        "dsc":"0x1680-0x169F 欧甘字母 Ogham",
        "s":"0x1680",
        "e":"0x169F"
    },
    {
        "dsc":"0x16A0-0x16FF 卢恩字母 Runic",
        "s":"0x16A0",
        "e":"0x16FF"
    },
    {
        "dsc":"0x1700-0x171F 他加禄字母 Tagalog",
        "s":"0x1700",
        "e":"0x171F"
    },
    {
        "dsc":"0x1720-0x173F 哈努诺文 Hanunóo",
        "s":"0x1720",
        "e":"0x173F"
    },
    {
        "dsc":"0x1740-0x175F 布希德文 Buhid",
        "s":"0x1740",
        "e":"0x175F"
    },
    {
        "dsc":"0x1760-0x177F 塔格班瓦文 Tagbanwa",
        "s":"0x1760",
        "e":"0x177F"
    },
    {
        "dsc":"0x1780-0x17FF 高棉文 Khmer",
        "s":"0x1780",
        "e":"0x17FF"
    },
    {
        "dsc":"0x1800-0x18AF 蒙古文 Mongolian",
        "s":"0x1800",
        "e":"0x18AF"
    },
    {
        "dsc":"0x18B0-0x18FF 加拿大原住民音节文字扩展 Unified Canadian Aboriginal Syllabics Extended",
        "s":"0x18B0",
        "e":"0x18FF"
    },
    {
        "dsc":"0x1900-0x194F 林布文 Limbu",
        "s":"0x1900",
        "e":"0x194F"
    },
    {
        "dsc":"0x1950-0x197F 德宏傣文 Tai Le",
        "s":"0x1950",
        "e":"0x197F"
    },
    {
        "dsc":"0x1980-0x19DF 新傣仂文 New Tai Lue",
        "s":"0x1980",
        "e":"0x19DF"
    },
    {
        "dsc":"0x19E0-0x19FF 高棉文符号 Khmer Symbols",
        "s":"0x19E0",
        "e":"0x19FF"
    },
    {
        "dsc":"0x1A00-0x1A1F 布吉文 Buginese",
        "s":"0x1A00",
        "e":"0x1A1F"
    },
    {
        "dsc":"0x1A20-0x1AAF 老傣文 Tai Tham",
        "s":"0x1A20",
        "e":"0x1AAF"
    },
    {
        "dsc":"0x1AB0-0x1AFF 组合变音标记扩展 Combining Diacritical Marks Extended",
        "s":"0x1AB0",
        "e":"0x1AFF"
    },
    {
        "dsc":"0x1B00-0x1B7F 巴厘字母 Balinese",
        "s":"0x1B00",
        "e":"0x1B7F"
    },
    {
        "dsc":"0x1B80-0x1BBF 巽他字母 Sundanese",
        "s":"0x1B80",
        "e":"0x1BBF"
    },
    {
        "dsc":"0x1BC0-0x1BFF 巴塔克文 Batak",
        "s":"0x1BC0",
        "e":"0x1BFF"
    },
    {
        "dsc":"0x1C00-0x1C4F 雷布查字母 Lepcha",
        "s":"0x1C00",
        "e":"0x1C4F"
    },
    {
        "dsc":"0x1C50-0x1C7F 桑塔利文 Ol Chiki",
        "s":"0x1C50",
        "e":"0x1C7F"
    },
    {
        "dsc":"0x1C80-0x1C8F 西里尔字母扩充-C Cyrillic Extended-C",
        "s":"0x1C80",
        "e":"0x1C8F"
    },
    {
        "dsc":"0x1C90-0x1CBF 格鲁吉亚字母扩展 Georgian Extended",
        "s":"0x1C90",
        "e":"0x1CBF"
    },
    {
        "dsc":"0x1CC0-0x1CCF 巽他字母补充 Sudanese Supplement",
        "s":"0x1CC0",
        "e":"0x1CCF"
    },
    {
        "dsc":"0x1CD0-0x1CFF 梵文吠陀扩展 Vedic Extensions",
        "s":"0x1CD0",
        "e":"0x1CFF"
    },
    {
        "dsc":"0x1D00-0x1D7F 音标扩展 Phonetic Extensions",
        "s":"0x1D00",
        "e":"0x1D7F"
    },
    {
        "dsc":"0x1D80-0x1DBF 音标扩展补充 Phonetic Extensions Supplement",
        "s":"0x1D80",
        "e":"0x1DBF"
    },
    {
        "dsc":"0x1DC0-0x1DFF 结合附加符号补充 Combining Diacritics Marks Supplement",
        "s":"0x1DC0",
        "e":"0x1DFF"
    },
    {
        "dsc":"0x1E00-0x1EFF 拉丁文扩展附加 Latin Extended Additional",
        "s":"0x1E00",
        "e":"0x1EFF"
    },
    {
        "dsc":"0x1F00-0x1FFF 希腊文扩展 Greek Extended",
        "s":"0x1F00",
        "e":"0x1FFF"
    },
    {
        "dsc":"0x2000-0x206F 常用标点 General Punctuation",
        "s":"0x2000",
        "e":"0x206F"
    },
    {
        "dsc":"0x2070-0x209F 上标及下标 Superscripts and Subscripts",
        "s":"0x2070",
        "e":"0x209F"
    },
    {
        "dsc":"0x20A0-0x20CF 货币符号 Currency Symbols",
        "s":"0x20A0",
        "e":"0x20CF"
    },
    {
        "dsc":"0x20D0-0x20FF 符号用组合附加符号 Combining Diacritical Marks for Symbols",
        "s":"0x20D0",
        "e":"0x20FF"
    },
    {
        "dsc":"0x2100-0x214F 字母式符号 Letterlike Symbols",
        "s":"0x2100",
        "e":"0x214F"
    },
    {
        "dsc":"0x2150-0x218F 数字形式 Number Forms",
        "s":"0x2150",
        "e":"0x218F"
    },
    {
        "dsc":"0x2190-0x21FF 箭头 Arrows",
        "s":"0x2190",
        "e":"0x21FF"
    },
    {
        "dsc":"0x2200-0x22FF 数学运算符 Mathematical Operators",
        "s":"0x2200",
        "e":"0x22FF"
    },
    {
        "dsc":"0x2300-0x23FF 杂项技术符号 Miscellaneous Technical",
        "s":"0x2300",
        "e":"0x23FF"
    },
    {
        "dsc":"0x2400-0x243F 控制图片 Control Pictures",
        "s":"0x2400",
        "e":"0x243F"
    },
    {
        "dsc":"0x2440-0x245F 光学识别符 Optical Character Recognition",
        "s":"0x2440",
        "e":"0x245F"
    },
    {
        "dsc":"0x2460-0x24FF 带圈字母和数字 Enclosed Alphanumerics",
        "s":"0x2460",
        "e":"0x24FF"
    },
    {
        "dsc":"0x2500-0x257F 制表符 Box Drawing",
        "s":"0x2500",
        "e":"0x257F"
    },
    {
        "dsc":"0x2580-0x259F 方块元素 Block Elements",
        "s":"0x2580",
        "e":"0x259F"
    },
    {
        "dsc":"0x25A0-0x25FF 几何图形 Geometric Shapes",
        "s":"0x25A0",
        "e":"0x25FF"
    },
    {
        "dsc":"0x2600-0x26FF 杂项符号 Miscellaneous Symbols",
        "s":"0x2600",
        "e":"0x26FF"
    },
    {
        "dsc":"0x2700-0x27BF 装饰符号 Dingbats",
        "s":"0x2700",
        "e":"0x27BF"
    },
    {
        "dsc":"0x27C0-0x27EF 杂项数学符号-A Miscellaneous Mathematical Symbols-A",
        "s":"0x27C0",
        "e":"0x27EF"
    },
    {
        "dsc":"0x27F0-0x27FF 追加箭头-A Supplemental Arrows-A",
        "s":"0x27F0",
        "e":"0x27FF"
    },
    {
        "dsc":"0x2800-0x28FF 盲文点字模型 Braille Patterns",
        "s":"0x2800",
        "e":"0x28FF"
    },
    {
        "dsc":"0x2900-0x297F 追加箭头-B Supplemental Arrows-B",
        "s":"0x2900",
        "e":"0x297F"
    },
    {
        "dsc":"0x2980-0x29FF 杂项数学符号-B Miscellaneous Mathematical Symbols-B",
        "s":"0x2980",
        "e":"0x29FF"
    },
    {
        "dsc":"0x2A00-0x2AFF 追加数学运算符 Supplemental Mathematical Operator",
        "s":"0x2A00",
        "e":"0x2AFF"
    },
    {
        "dsc":"0x2B00-0x2BFF 杂项符号和箭头 Miscellaneous Symbols and Arrows",
        "s":"0x2B00",
        "e":"0x2BFF"
    },
    {
        "dsc":"0x2C00-0x2C5F 格拉哥里字母 Glagolitic",
        "s":"0x2C00",
        "e":"0x2C5F"
    },
    {
        "dsc":"0x2C60-0x2C7F 拉丁文扩展-C Latin Extended-C",
        "s":"0x2C60",
        "e":"0x2C7F"
    },
    {
        "dsc":"0x2C80-0x2CFF 科普特字母 Coptic",
        "s":"0x2C80",
        "e":"0x2CFF"
    },
    {
        "dsc":"0x2D00-0x2D2F 格鲁吉亚字母补充 Georgian Supplement",
        "s":"0x2D00",
        "e":"0x2D2F"
    },
    {
        "dsc":"0x2D30-0x2D7F 提非纳文 Tifinagh",
        "s":"0x2D30",
        "e":"0x2D7F"
    },
    {
        "dsc":"0x2D80-0x2DDF 吉兹字母扩展 Ethiopic Extended",
        "s":"0x2D80",
        "e":"0x2DDF"
    },
    {
        "dsc":"0x2DE0-0x2DFF 西里尔字母扩展-A Cyrillic Extended-A",
        "s":"0x2DE0",
        "e":"0x2DFF"
    },
    {
        "dsc":"0x2E00-0x2E7F 追加标点 Supplemental Punctuation",
        "s":"0x2E00",
        "e":"0x2E7F"
    },
    {
        "dsc":"0x2E80-0x2EFF 中日韩汉字部首补充 CJK Radicals Supplement",
        "s":"0x2E80",
        "e":"0x2EFF"
    },
    {
        "dsc":"0x2F00-0x2FDF 康熙部首 Kangxi Radicals",
        "s":"0x2F00",
        "e":"0x2FDF"
    },
    {
        "dsc":"0x2FF0-0x2FFF 表意文字序列 Ideographic Description Characters",
        "s":"0x2FF0",
        "e":"0x2FFF"
    },
    {
        "dsc":"0x3000-0x303F 中日韩符号和标点 CJK Symbols and Punctuation",
        "s":"0x3000",
        "e":"0x303F"
    },
    {
        "dsc":"0x3040-0x309F 日文平假名 Hiragana",
        "s":"0x3040",
        "e":"0x309F"
    },
    {
        "dsc":"0x30A0-0x30FF 日文片假名 Katakana",
        "s":"0x30A0",
        "e":"0x30FF"
    },
    {
        "dsc":"0x3100-0x312F 注音符号 Bopomofo",
        "s":"0x3100",
        "e":"0x312F"
    },
    {
        "dsc":"0x3130-0x318F 谚文兼容字母 Hangul Compatibility Jamo",
        "s":"0x3130",
        "e":"0x318F"
    },
    {
        "dsc":"0x3190-0x319F 汉文注释标志 Kanbun",
        "s":"0x3190",
        "e":"0x319F"
    },
    {
        "dsc":"0x31A0-0x31BF 注音字母扩展 Bopomofo Extended",
        "s":"0x31A0",
        "e":"0x31BF"
    },
    {
        "dsc":"0x31C0-0x31EF 中日韩笔画 CJK Strokes",
        "s":"0x31C0",
        "e":"0x31EF"
    },
    {
        "dsc":"0x31F0-0x31FF 日文片假名拼音扩展 Katakana Phonetic Extensions",
        "s":"0x31F0",
        "e":"0x31FF"
    },
    {
        "dsc":"0x3200-0x32FF 带圈的CJK字符及月份 Enclosed CJK Letters and Months",
        "s":"0x3200",
        "e":"0x32FF"
    },
    {
        "dsc":"0x3300-0x33FF 中日韩兼容字符 CJK Compatibility",
        "s":"0x3300",
        "e":"0x33FF"
    },
    {
        "dsc":"0x3400-0x4DBF 中日韩统一表意文字扩展区A CJK Unified Ideographs Extension A",
        "s":"0x3400",
        "e":"0x4DBF"
    },
    {
        "dsc":"0x4DC0-0x4DFF 易经六十四卦符号 Yijing Hexagrams Symbols",
        "s":"0x4DC0",
        "e":"0x4DFF"
    },
    {
        "dsc":"0x4E00-0x9FFF 中日韩统一表意文字 CJK Unified Ideographs",
        "s":"0x4E00",
        "e":"0x9FFF"
    },
    {
        "dsc":"0xA000-0xA48F 彝文音节 Yi Syllables",
        "s":"0xA000",
        "e":"0xA48F"
    },
    {
        "dsc":"0xA490-0xA4CF 彝文字根 Yi Radicals",
        "s":"0xA490",
        "e":"0xA4CF"
    },
    {
        "dsc":"0xA4D0-0xA4FF 老傈僳文 Lisu",
        "s":"0xA4D0",
        "e":"0xA4FF"
    },
    {
        "dsc":"0xA500-0xA63F 瓦伊语 Vai",
        "s":"0xA500",
        "e":"0xA63F"
    },
    {
        "dsc":"0xA640-0xA69F 西里尔字母扩展-B Cyrillic Extended-B",
        "s":"0xA640",
        "e":"0xA69F"
    },
    {
        "dsc":"0xA6A0-0xA6FF 巴姆穆文字 Bamum",
        "s":"0xA6A0",
        "e":"0xA6FF"
    },
    {
        "dsc":"0xA700-0xA71F 声调修饰符号 Modifier Tone Letters",
        "s":"0xA700",
        "e":"0xA71F"
    },
    {
        "dsc":"0xA720-0xA7FF 拉丁文扩展-D Latin Extended-D",
        "s":"0xA720",
        "e":"0xA7FF"
    },
    {
        "dsc":"0xA800-0xA82F 锡尔赫特文 Syloti Nagri",
        "s":"0xA800",
        "e":"0xA82F"
    },
    {
        "dsc":"0xA830-0xA83F 通用印度数字格式 Common Indic Number Forms",
        "s":"0xA830",
        "e":"0xA83F"
    },
    {
        "dsc":"0xA840-0xA87F 八思巴字 Phags-pa",
        "s":"0xA840",
        "e":"0xA87F"
    },
    {
        "dsc":"0xA880-0xA8DF 索拉什特拉文 Saurashtra",
        "s":"0xA880",
        "e":"0xA8DF"
    },
    {
        "dsc":"0xA8E0-0xA8FF 天城文扩展 Devanagari Extended",
        "s":"0xA8E0",
        "e":"0xA8FF"
    },
    {
        "dsc":"0xA900-0xA92F 克耶里字母 Kayah Li",
        "s":"0xA900",
        "e":"0xA92F"
    },
    {
        "dsc":"0xA930-0xA95F 勒姜字母 Rejang",
        "s":"0xA930",
        "e":"0xA95F"
    },
    {
        "dsc":"0xA960-0xA97F 谚文扩展-A Hangul Jamo Extended-A",
        "s":"0xA960",
        "e":"0xA97F"
    },
    {
        "dsc":"0xA980-0xA9DF 爪哇字母 Javanese",
        "s":"0xA980",
        "e":"0xA9DF"
    },
    {
        "dsc":"0xA9E0-0xA9FF 缅甸文扩展-B Myanmar Extended-B",
        "s":"0xA9E0",
        "e":"0xA9FF"
    },
    {
        "dsc":"0xAA00-0xAA5F 占语字母 Cham",
        "s":"0xAA00",
        "e":"0xAA5F"
    },
    {
        "dsc":"0xAA60-0xAA7F 缅甸文扩展-A Myanmar Extended-A",
        "s":"0xAA60",
        "e":"0xAA7F"
    },
    {
        "dsc":"0xAA80-0xAADF 越南傣文 Tai Viet",
        "s":"0xAA80",
        "e":"0xAADF"
    },
    {
        "dsc":"0xAAE0-0xAAFF 曼尼普尔文扩展 Meetei Mayek Extensions",
        "s":"0xAAE0",
        "e":"0xAAFF"
    },
    {
        "dsc":"0xAB00-0xAB2F 吉兹字母扩展-A Ethiopic Extended-A",
        "s":"0xAB00",
        "e":"0xAB2F"
    },
    {
        "dsc":"0xAB30-0xAB6F 拉丁文扩展-E Latin Extended-E",
        "s":"0xAB30",
        "e":"0xAB6F"
    },
    {
        "dsc":"0xAB70-0xABBF 切罗基语补充 Cherokee Supplement",
        "s":"0xAB70",
        "e":"0xABBF"
    },
    {
        "dsc":"0xABC0-0xABFF 曼尼普尔文 Meetei Mayek",
        "s":"0xABC0",
        "e":"0xABFF"
    },
    {
        "dsc":"0xAC00-0xD7AF 谚文音节 Hangul Syllables",
        "s":"0xAC00",
        "e":"0xD7AF"
    },
    {
        "dsc":"0xD7B0-0xD7FF 谚文字母扩展-B Hangul Jamo Extended-B",
        "s":"0xD7B0",
        "e":"0xD7FF"
    },
    {
        "dsc":"0xD800-0xDBFF UTF-16的高半区 High-half zone of UTF-16",
        "s":"0xD800",
        "e":"0xDBFF"
    },
    {
        "dsc":"0xDC00-0xDFFF UTF-16的低半区 Low-half zone of UTF-16",
        "s":"0xDC00",
        "e":"0xDFFF"
    },
    {
        "dsc":"0xE000-0xF8FF 私用区 Private Use Area",
        "s":"0xE000",
        "e":"0xF8FF"
    },
    {
        "dsc":"0xF900-0xFAFF 中日韩兼容表意文字 CJK Compatibility Ideographs",
        "s":"0xF900",
        "e":"0xFAFF"
    },
    {
        "dsc":"0xFB00-0xFB4F 字母表达形式（拉丁字母连字、亚美尼亚字母连字、希伯来文表现形式） Alphabetic Presentation Forms",
        "s":"0xFB00",
        "e":"0xFB4F"
    },
    {
        "dsc":"0xFB50-0xFDFF 阿拉伯字母表达形式-A Arabic Presentation Forms A",
        "s":"0xFB50",
        "e":"0xFDFF"
    },
    {
        "dsc":"0xFE00-0xFE0F 异体字选择器 Variation Selector",
        "s":"0xFE00",
        "e":"0xFE0F"
    },
    {
        "dsc":"0xFE10-0xFE1F 竖排形式 Vertical Forms",
        "s":"0xFE10",
        "e":"0xFE1F"
    },
    {
        "dsc":"0xFE20-0xFE2F 组合用半符号 Combining Half Marks",
        "s":"0xFE20",
        "e":"0xFE2F"
    },
    {
        "dsc":"0xFE30-0xFE4F 中日韩兼容形式 CJK Compatibility Forms",
        "s":"0xFE30",
        "e":"0xFE4F"
    },
    {
        "dsc":"0xFE50-0xFE6F 小写变体形式 Small Form Variants",
        "s":"0xFE50",
        "e":"0xFE6F"
    },
    {
        "dsc":"0xFE70-0xFEFF 阿拉伯文表达形式-B Arabic Presentation Forms B",
        "s":"0xFE70",
        "e":"0xFEFF"
    },
    {
        "dsc":"0xFF00-0xFFEF 半角及全角字符 Halfwidth and Fullwidth Forms",
        "s":"0xFF00",
        "e":"0xFFEF"
    },
    {
        "dsc":"0xFFF0-0xFFFF 特殊字符区 Specials",
        "s":"0xFFF0",
        "e":"0xFFFF"
    }
]


if __name__ == "__main__":
    args = parse_args()
    edit_tok_model(args.input_file, args.output_file, args.add_file)
    dump_model(args.input_file, args.output_file)
