# -*- coding: utf-8 -*-
"""
编码处理模块

使用 codecs 增量解码器优雅地处理 GBK/UTF-8 的断包/粘包问题，
防止多字节字符被截断导致乱码。
"""

import codecs
import re
from typing import Tuple


class EncodingHandler:
    """
    编码处理器
    
    使用增量解码器处理字节流到文本的转换，
    自动处理多字节字符的断包问题。
    """
    
    def __init__(self, encoding: str = 'gbk'):
        """
        初始化编码处理器
        
        Args:
            encoding: 编码方式 ('gbk' 或 'utf-8')
        """
        self._encoding = encoding.lower()
        self._decoder = codecs.getincrementaldecoder(self._encoding)('ignore')
    
    @property
    def encoding(self) -> str:
        """获取当前编码"""
        return self._encoding
    
    @encoding.setter
    def encoding(self, value: str):
        """
        设置编码并重置解码器
        
        Args:
            value: 新的编码方式
        """
        new_encoding = value.lower()
        if new_encoding != self._encoding:
            self._encoding = new_encoding
            self.reset()
    
    def reset(self):
        """重置解码器状态（清空缓冲区）"""
        self._decoder = codecs.getincrementaldecoder(self._encoding)('ignore')
    
    def decode(self, data: bytes, final: bool = False) -> str:
        """
        将字节数据解码为文本
        
        使用增量解码器，自动处理不完整的多字节字符。
        不完整的字符会被缓存，等待后续数据补全。
        
        Args:
            data: 输入字节数据
            final: 是否为最后一块数据
            
        Returns:
            解码后的文本
        """
        try:
            return self._decoder.decode(data, final)
        except Exception:
            # 解码失败时尝试替换错误字符
            self.reset()
            return data.decode(self._encoding, errors='replace')


def bytes_to_hex(data: bytes) -> str:
    """
    将字节数据转换为 HEX 字符串
    
    Args:
        data: 输入字节数据
        
    Returns:
        格式化的 HEX 字符串 (如 "AA BB CC ")
    """
    return ' '.join(f'{b:02X}' for b in data) + ' ' if data else ''


def hex_to_bytes(hex_str: str) -> bytes:
    """
    将 HEX 字符串转换为字节数据
    
    移植自 C# 的 HexToBytes 方法，
    自动清除非法字符并解析十六进制数据。
    
    Args:
        hex_str: HEX 字符串 (如 "AA BB CC" 或 "AABBCC")
        
    Returns:
        解析后的字节数据
    """
    # 清除非法字符，只保留 0-9 A-F a-f
    clean_str = re.sub(r'[^A-Fa-f0-9]', '', hex_str)
    
    if not clean_str:
        return bytes()
    
    # 确保偶数长度
    if len(clean_str) % 2 != 0:
        clean_str = clean_str + '0'
    
    # 将字符两两分组并转换为字节
    result = []
    for i in range(0, len(clean_str), 2):
        byte_str = clean_str[i:i+2]
        try:
            result.append(int(byte_str, 16))
        except ValueError:
            pass
    
    return bytes(result)


def text_to_bytes(text: str, encoding: str = 'gbk') -> bytes:
    """
    将文本转换为字节数据
    
    Args:
        text: 输入文本
        encoding: 编码方式
        
    Returns:
        编码后的字节数据
    """
    try:
        return text.encode(encoding.lower())
    except Exception:
        return text.encode(encoding.lower(), errors='replace')
