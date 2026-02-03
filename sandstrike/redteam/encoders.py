"""
Encoding functions for adversarial prompts.

This module provides various encoding methods that can be applied to any prompt
as an additional layer of obfuscation or testing.
"""

import base64
import codecs
import hashlib
import re
from typing import Dict, List, Optional, Tuple


class PromptEncoder:
    """Handles various encoding methods for adversarial prompts."""
    
    # Available encoding methods
    ENCODING_METHODS = {
        'base64': 'Base64 encoding',
        'base32': 'Base32 encoding', 
        'base16': 'Base16 (hex) encoding',
        'rot13': 'ROT13 substitution cipher',
        'rot47': 'ROT47 substitution cipher',
        'url_encode': 'URL encoding',
        'html_encode': 'HTML entity encoding',
        'unicode_escape': 'Unicode escape sequences',
        'reverse': 'Reverse text',
        'caesar': 'Caesar cipher (shift by 3)',
        'binary': 'Binary representation',
        'md5_hash': 'MD5 hash (one-way)',
        'sha1_hash': 'SHA1 hash (one-way)',
        'double_encode': 'Double Base64 encoding',
        'mixed_case': 'Random case mixing',
        'whitespace_obfuscation': 'Add random whitespace',
        'zero_width': 'Insert zero-width characters',
        'leet_speak': 'Leet speak substitution',
        'pig_latin': 'Pig Latin transformation'
    }
    
    @staticmethod
    def encode_base64(text: str) -> str:
        """Encode text to Base64."""
        try:
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def decode_base64(text: str) -> str:
        """Decode text from Base64."""
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def encode_base32(text: str) -> str:
        """Encode text to Base32."""
        try:
            return base64.b32encode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def decode_base32(text: str) -> str:
        """Decode text from Base32."""
        try:
            return base64.b32decode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def encode_base16(text: str) -> str:
        """Encode text to Base16 (hex)."""
        try:
            return text.encode('utf-8').hex()
        except Exception:
            return text
    
    @staticmethod
    def decode_base16(text: str) -> str:
        """Decode text from Base16 (hex)."""
        try:
            return bytes.fromhex(text).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def encode_rot13(text: str) -> str:
        """Encode text using ROT13 substitution."""
        try:
            return codecs.encode(text, 'rot13')
        except Exception:
            return text
    
    @staticmethod
    def encode_rot47(text: str) -> str:
        """Encode text using ROT47 substitution."""
        try:
            result = ""
            for char in text:
                if 33 <= ord(char) <= 126:
                    result += chr(((ord(char) - 33 + 47) % 94) + 33)
                else:
                    result += char
            return result
        except Exception:
            return text
    
    @staticmethod
    def encode_url(text: str) -> str:
        """Encode text using URL encoding."""
        try:
            import urllib.parse
            return urllib.parse.quote(text)
        except Exception:
            return text
    
    @staticmethod
    def decode_url(text: str) -> str:
        """Decode text from URL encoding."""
        try:
            import urllib.parse
            return urllib.parse.unquote(text)
        except Exception:
            return text
    
    @staticmethod
    def encode_html(text: str) -> str:
        """Encode text using HTML entities."""
        try:
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
        except Exception:
            return text
    
    @staticmethod
    def encode_unicode_escape(text: str) -> str:
        """Encode text using Unicode escape sequences."""
        try:
            return text.encode('unicode_escape').decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def encode_reverse(text: str) -> str:
        """Reverse the text."""
        return text[::-1]
    
    @staticmethod
    def encode_caesar(text: str, shift: int = 3) -> str:
        """Encode text using Caesar cipher."""
        try:
            result = ""
            for char in text:
                if char.isalpha():
                    ascii_offset = ord('A') if char.isupper() else ord('a')
                    result += chr(((ord(char) - ascii_offset + shift) % 26) + ascii_offset)
                else:
                    result += char
            return result
        except Exception:
            return text
    
    @staticmethod
    def encode_binary(text: str) -> str:
        """Convert text to binary representation."""
        try:
            return ' '.join(format(ord(char), '08b') for char in text)
        except Exception:
            return text
    
    @staticmethod
    def encode_md5(text: str) -> str:
        """Generate MD5 hash of text (one-way encoding)."""
        try:
            return hashlib.md5(text.encode('utf-8')).hexdigest()
        except Exception:
            return text
    
    @staticmethod
    def encode_sha1(text: str) -> str:
        """Generate SHA1 hash of text (one-way encoding)."""
        try:
            return hashlib.sha1(text.encode('utf-8')).hexdigest()
        except Exception:
            return text
    
    @staticmethod
    def encode_double_base64(text: str) -> str:
        """Apply Base64 encoding twice."""
        try:
            first = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return base64.b64encode(first.encode('utf-8')).decode('utf-8')
        except Exception:
            return text
    
    @staticmethod
    def encode_mixed_case(text: str) -> str:
        """Randomly mix upper and lower case."""
        import random
        try:
            return ''.join(char.upper() if random.choice([True, False]) else char.lower() for char in text)
        except Exception:
            return text
    
    @staticmethod
    def encode_whitespace_obfuscation(text: str) -> str:
        """Add random whitespace characters."""
        import random
        try:
            result = ""
            for char in text:
                result += char
                if random.random() < 0.3:  # 30% chance to add whitespace
                    result += random.choice([' ', '\t', '\n', '\r'])
            return result
        except Exception:
            return text
    
    @staticmethod
    def encode_zero_width(text: str) -> str:
        """Insert zero-width characters."""
        try:
            zero_width_chars = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff']
            result = ""
            for char in text:
                result += char
                if char != ' ':  # Don't add after spaces
                    result += '\u200b'  # Zero-width space
            return result
        except Exception:
            return text
    
    @staticmethod
    def encode_leet_speak(text: str) -> str:
        """Convert text to leet speak."""
        leet_map = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7',
            'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '5', 'T': '7'
        }
        try:
            for char, replacement in leet_map.items():
                text = text.replace(char, replacement)
            return text
        except Exception:
            return text
    
    @staticmethod
    def encode_pig_latin(text: str) -> str:
        """Convert text to Pig Latin."""
        try:
            words = text.split()
            result = []
            for word in words:
                if word[0].lower() in 'aeiou':
                    result.append(word + 'way')
                else:
                    # Find first vowel
                    for i, char in enumerate(word):
                        if char.lower() in 'aeiou':
                            result.append(word[i:] + word[:i] + 'ay')
                            break
                    else:
                        result.append(word + 'ay')
            return ' '.join(result)
        except Exception:
            return text
    
    @classmethod
    def encode_prompt(cls, prompt: str, encoding_method: str) -> Tuple[str, str]:
        """
        Encode a prompt using the specified method.
        
        Returns:
            Tuple of (encoded_prompt, encoding_info)
        """
        if encoding_method not in cls.ENCODING_METHODS:
            return prompt, f"Unknown encoding method: {encoding_method}"
        
        try:
            # Get the encoding method function
            method_name = f"encode_{encoding_method}"
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                encoded = method(prompt)
                info = f"Applied {cls.ENCODING_METHODS[encoding_method]}"
                return encoded, info
            else:
                return prompt, f"Encoding method not implemented: {encoding_method}"
        except Exception as e:
            return prompt, f"Encoding failed: {str(e)}"
    
    @classmethod
    def get_available_encodings(cls) -> Dict[str, str]:
        """Get all available encoding methods."""
        return cls.ENCODING_METHODS.copy()
    
    @classmethod
    def apply_multiple_encodings(cls, prompt: str, encoding_methods: List[str]) -> Tuple[str, List[str]]:
        """
        Apply multiple encodings to a prompt in sequence.
        
        Returns:
            Tuple of (final_encoded_prompt, list_of_encoding_info)
        """
        current_prompt = prompt
        encoding_info = []
        
        for method in encoding_methods:
            if method in cls.ENCODING_METHODS:
                current_prompt, info = cls.encode_prompt(current_prompt, method)
                encoding_info.append(info)
            else:
                encoding_info.append(f"Unknown method: {method}")
        
        return current_prompt, encoding_info
