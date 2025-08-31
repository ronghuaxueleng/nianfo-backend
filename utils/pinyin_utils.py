"""
拼音生成工具类
用于自动为中文内容生成注音
"""
import re
from pypinyin import lazy_pinyin, Style

class PinyinGenerator:
    """拼音生成器"""
    
    @staticmethod
    def generate_pinyin(text, style=Style.TONE):
        """
        生成中文文本的拼音注音
        
        Args:
            text (str): 中文文本
            style: 拼音风格，默认为带声调
                - Style.TONE: 带声调符号的拼音 (mā mí tuó)
                - Style.TONE3: 数字声调的拼音 (ma1 mi2 tuo2)
                - Style.NORMAL: 不带声调的拼音 (ma mi tuo)
        
        Returns:
            str: 拼音注音文本
        """
        if not text or not text.strip():
            return ""
        
        # 按行处理，保持原文的换行格式
        lines = text.split('\n')
        pinyin_lines = []
        
        for line in lines:
            if not line.strip():
                # 空行直接添加
                pinyin_lines.append('')
                continue
                
            # 生成该行的拼音
            line_pinyin = PinyinGenerator._process_line(line, style)
            pinyin_lines.append(line_pinyin)
        
        return '\n'.join(pinyin_lines)
    
    @staticmethod
    def _process_line(line, style):
        """
        处理单行文本的拼音生成
        
        Args:
            line (str): 单行中文文本
            style: 拼音风格
        
        Returns:
            str: 该行的拼音注音
        """
        if not line.strip():
            return ""
        
        # 将文本分割为中文字符和非中文字符的片段
        segments = PinyinGenerator._split_text(line)
        result_segments = []
        
        for segment, is_chinese in segments:
            if is_chinese:
                # 对中文字符生成拼音
                pinyin_list = lazy_pinyin(segment, style=style)
                result_segments.append(' '.join(pinyin_list))
            else:
                # 非中文字符保持原样（标点符号、数字、英文等）
                result_segments.append(segment)
        
        return ''.join(result_segments)
    
    @staticmethod
    def _split_text(text):
        """
        将文本分割为中文和非中文的片段
        
        Args:
            text (str): 输入文本
        
        Returns:
            list: [(segment, is_chinese), ...] 的列表
        """
        segments = []
        current_segment = ""
        current_is_chinese = None
        
        for char in text:
            is_chinese = PinyinGenerator._is_chinese_char(char)
            
            if current_is_chinese is None:
                # 第一个字符
                current_segment = char
                current_is_chinese = is_chinese
            elif current_is_chinese == is_chinese:
                # 同类型字符，添加到当前片段
                current_segment += char
            else:
                # 类型变化，保存当前片段，开始新片段
                segments.append((current_segment, current_is_chinese))
                current_segment = char
                current_is_chinese = is_chinese
        
        # 添加最后一个片段
        if current_segment:
            segments.append((current_segment, current_is_chinese))
        
        return segments
    
    @staticmethod
    def _is_chinese_char(char):
        """
        判断字符是否为中文字符
        
        Args:
            char (str): 单个字符
        
        Returns:
            bool: True if 中文字符
        """
        # 使用Unicode码点范围判断中文字符
        # 包括基本汉字、扩展汉字等
        code = ord(char)
        return (
            (0x4e00 <= code <= 0x9fff) or      # CJK Unified Ideographs
            (0x3400 <= code <= 0x4dbf) or      # CJK Extension A
            (0x20000 <= code <= 0x2a6df) or    # CJK Extension B
            (0x2a700 <= code <= 0x2b73f) or    # CJK Extension C
            (0x2b740 <= code <= 0x2b81f) or    # CJK Extension D
            (0x2b820 <= code <= 0x2ceaf) or    # CJK Extension E
            (0x2ceb0 <= code <= 0x2ebef)       # CJK Extension F
        )
    
    @staticmethod
    def generate_simple_pinyin(text):
        """
        生成简单格式的拼音（带声调符号，适合显示）
        
        Args:
            text (str): 中文文本
        
        Returns:
            str: 带声调符号的拼音
        """
        return PinyinGenerator.generate_pinyin(text, Style.TONE)
    
    @staticmethod
    def generate_numbered_pinyin(text):
        """
        生成数字声调格式的拼音（适合输入）
        
        Args:
            text (str): 中文文本
        
        Returns:
            str: 数字声调的拼音
        """
        return PinyinGenerator.generate_pinyin(text, Style.TONE3)