"""
Comprehensive encoding/decoding module for Avenlis SandStrike.

This module provides various encoding methods for adversarial prompts
to test evasion techniques and bypass security filters.
"""

import base64
import hashlib
import binascii
import urllib.parse
import re
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class EncodingMethod(Enum):
    """Available encoding methods."""
    BASE2 = "base2"
    BASE8 = "base8"
    BASE16 = "base16"
    BASE32 = "base32"
    BASE64 = "base64"
    BASE85 = "base85"
    HEXADECIMAL = "hexadecimal"
    MD5_HASH = "md5_hash"
    REVERSE = "reverse"
    ROT5 = "rot5"
    ROT13 = "rot13"
    ROT18 = "rot18"
    ROT25 = "rot25"
    ROT32 = "rot32"
    ROT47 = "rot47"
    URL_ENCODE = "url_encode"
    MORSE_CODE = "morse_code"
    NATO_PHONETIC = "nato_phonetic"
    DIACRITICS = "diacritics"
    BRAILLE = "braille"


class PromptEncoder:
    """Main encoder class for applying various encoding methods to prompts."""
    
    def __init__(self):
        self.morse_code_map = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
            '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
            '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
            ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
            '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
        }
        
        self.nato_phonetic_map = {
            'A': 'Alpha', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
            'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliet',
            'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
            'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
            'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee',
            'Z': 'Zulu', '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three',
            '4': 'Four', '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight',
            '9': 'Nine'
        }
        
        self.diacritics_map = {
            'A': ['À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ'],
            'E': ['È', 'É', 'Ê', 'Ë'],
            'I': ['Ì', 'Í', 'Î', 'Ï'],
            'O': ['Ò', 'Ó', 'Ô', 'Õ', 'Ö', 'Ø'],
            'U': ['Ù', 'Ú', 'Û', 'Ü'],
            'C': ['Ç'],
            'N': ['Ñ'],
            'S': ['Š'],
            'Z': ['Ž']
        }
        
        self.braille_map = {
            'A': '⠁', 'B': '⠃', 'C': '⠉', 'D': '⠙', 'E': '⠑', 'F': '⠋',
            'G': '⠛', 'H': '⠓', 'I': '⠊', 'J': '⠚', 'K': '⠅', 'L': '⠇',
            'M': '⠍', 'N': '⠝', 'O': '⠕', 'P': '⠏', 'Q': '⠟', 'R': '⠗',
            'S': '⠎', 'T': '⠞', 'U': '⠥', 'V': '⠧', 'W': '⠺', 'X': '⠭',
            'Y': '⠽', 'Z': '⠵', '0': '⠴', '1': '⠂', '2': '⠆', '3': '⠒',
            '4': '⠲', '5': '⠢', '6': '⠖', '7': '⠶', '8': '⠦', '9': '⠔'
        }

    def encode_text(self, text: str, method: EncodingMethod) -> str:
        """Encode text using the specified method."""
        try:
            if method == EncodingMethod.BASE2:
                return self._encode_base2(text)
            elif method == EncodingMethod.BASE8:
                return self._encode_base8(text)
            elif method == EncodingMethod.BASE16:
                return self._encode_base16(text)
            elif method == EncodingMethod.BASE32:
                return self._encode_base32(text)
            elif method == EncodingMethod.BASE64:
                return self._encode_base64(text)
            elif method == EncodingMethod.BASE85:
                return self._encode_base85(text)
            elif method == EncodingMethod.HEXADECIMAL:
                return self._encode_hexadecimal(text)
            elif method == EncodingMethod.MD5_HASH:
                return self._encode_md5(text)
            elif method == EncodingMethod.REVERSE:
                return self._encode_reverse(text)
            elif method == EncodingMethod.ROT5:
                return self._encode_rot5(text)
            elif method == EncodingMethod.ROT13:
                return self._encode_rot13(text)
            elif method == EncodingMethod.ROT18:
                return self._encode_rot18(text)
            elif method == EncodingMethod.ROT25:
                return self._encode_rot25(text)
            elif method == EncodingMethod.ROT32:
                return self._encode_rot32(text)
            elif method == EncodingMethod.ROT47:
                return self._encode_rot47(text)
            elif method == EncodingMethod.URL_ENCODE:
                return self._encode_url(text)
            elif method == EncodingMethod.MORSE_CODE:
                return self._encode_morse_code(text)
            elif method == EncodingMethod.NATO_PHONETIC:
                return self._encode_nato_phonetic(text)
            elif method == EncodingMethod.DIACRITICS:
                return self._encode_diacritics(text)
            elif method == EncodingMethod.BRAILLE:
                return self._encode_braille(text)
            else:
                raise ValueError(f"Unsupported encoding method: {method}")
        except Exception as e:
            raise ValueError(f"Error encoding with {method.value}: {str(e)}")

    def decode_text(self, encoded_text: str, method: EncodingMethod) -> str:
        """Decode text using the specified method."""
        try:
            if method == EncodingMethod.BASE2:
                return self._decode_base2(encoded_text)
            elif method == EncodingMethod.BASE8:
                return self._decode_base8(encoded_text)
            elif method == EncodingMethod.BASE16:
                return self._decode_base16(encoded_text)
            elif method == EncodingMethod.BASE32:
                return self._decode_base32(encoded_text)
            elif method == EncodingMethod.BASE64:
                return self._decode_base64(encoded_text)
            elif method == EncodingMethod.BASE85:
                return self._decode_base85(encoded_text)
            elif method == EncodingMethod.HEXADECIMAL:
                return self._decode_hexadecimal(encoded_text)
            elif method == EncodingMethod.REVERSE:
                return self._decode_reverse(encoded_text)
            elif method == EncodingMethod.ROT5:
                return self._decode_rot5(encoded_text)
            elif method == EncodingMethod.ROT13:
                return self._decode_rot13(encoded_text)
            elif method == EncodingMethod.ROT18:
                return self._decode_rot18(encoded_text)
            elif method == EncodingMethod.ROT25:
                return self._decode_rot25(encoded_text)
            elif method == EncodingMethod.ROT32:
                return self._decode_rot32(encoded_text)
            elif method == EncodingMethod.ROT47:
                return self._decode_rot47(encoded_text)
            elif method == EncodingMethod.URL_ENCODE:
                return self._decode_url(encoded_text)
            elif method == EncodingMethod.MORSE_CODE:
                return self._decode_morse_code(encoded_text)
            elif method == EncodingMethod.NATO_PHONETIC:
                return self._decode_nato_phonetic(encoded_text)
            elif method == EncodingMethod.DIACRITICS:
                return self._decode_diacritics(encoded_text)
            elif method == EncodingMethod.BRAILLE:
                return self._decode_braille(encoded_text)
            else:
                raise ValueError(f"Unsupported encoding method: {method}")
        except Exception as e:
            raise ValueError(f"Error decoding with {method.value}: {str(e)}")

    def apply_multiple_encodings(self, text: str, methods: List[EncodingMethod]) -> str:
        """Apply multiple encoding methods in sequence."""
        result = text
        for method in methods:
            result = self.encode_text(result, method)
        return result

    def apply_multiple_decodings(self, encoded_text: str, methods: List[EncodingMethod]) -> str:
        """Apply multiple decoding methods in reverse sequence."""
        result = encoded_text
        for method in reversed(methods):
            result = self.decode_text(result, method)
        return result

    # Base encoding methods
    def _encode_base2(self, text: str) -> str:
        """Encode text to base2 (binary)."""
        return ' '.join(format(ord(char), '08b') for char in text)

    def _decode_base2(self, encoded_text: str) -> str:
        """Decode text from base2 (binary)."""
        binary_chars = encoded_text.split()
        return ''.join(chr(int(binary, 2)) for binary in binary_chars)

    def _encode_base8(self, text: str) -> str:
        """Encode text to base8 (octal)."""
        return ' '.join(format(ord(char), '03o') for char in text)

    def _decode_base8(self, encoded_text: str) -> str:
        """Decode text from base8 (octal)."""
        octal_chars = encoded_text.split()
        return ''.join(chr(int(octal, 8)) for octal in octal_chars)

    def _encode_base16(self, text: str) -> str:
        """Encode text to base16 (hexadecimal)."""
        return text.encode('utf-8').hex()

    def _decode_base16(self, encoded_text: str) -> str:
        """Decode text from base16 (hexadecimal)."""
        return bytes.fromhex(encoded_text).decode('utf-8')

    def _encode_base32(self, text: str) -> str:
        """Encode text to base32."""
        return base64.b32encode(text.encode('utf-8')).decode('ascii')

    def _decode_base32(self, encoded_text: str) -> str:
        """Decode text from base32."""
        return base64.b32decode(encoded_text).decode('utf-8')

    def _encode_base64(self, text: str) -> str:
        """Encode text to base64."""
        return base64.b64encode(text.encode('utf-8')).decode('ascii')

    def _decode_base64(self, encoded_text: str) -> str:
        """Decode text from base64."""
        return base64.b64decode(encoded_text).decode('utf-8')

    def _encode_base85(self, text: str) -> str:
        """Encode text to base85."""
        return base64.b85encode(text.encode('utf-8')).decode('ascii')

    def _decode_base85(self, encoded_text: str) -> str:
        """Decode text from base85."""
        return base64.b85decode(encoded_text).decode('utf-8')

    def _encode_hexadecimal(self, text: str) -> str:
        """Encode text to hexadecimal (same as base16 but with different formatting)."""
        return ' '.join(format(ord(char), '02x') for char in text)

    def _decode_hexadecimal(self, encoded_text: str) -> str:
        """Decode text from hexadecimal."""
        hex_chars = encoded_text.split()
        return ''.join(chr(int(hex_char, 16)) for hex_char in hex_chars)

    def _encode_md5(self, text: str) -> str:
        """Generate MD5 hash of text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _encode_reverse(self, text: str) -> str:
        """Reverse the text."""
        return text[::-1]

    def _decode_reverse(self, encoded_text: str) -> str:
        """Reverse the text (same as encoding)."""
        return encoded_text[::-1]

    # ROT encoding methods
    def _encode_rot5(self, text: str) -> str:
        """Apply ROT5 encoding (rotate digits 0-9 by 5)."""
        result = []
        for char in text:
            if char.isdigit():
                result.append(str((int(char) + 5) % 10))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot5(self, encoded_text: str) -> str:
        """Decode ROT5 (rotate digits 0-9 by 5 in reverse)."""
        result = []
        for char in encoded_text:
            if char.isdigit():
                result.append(str((int(char) - 5) % 10))
            else:
                result.append(char)
        return ''.join(result)

    def _encode_rot13(self, text: str) -> str:
        """Apply ROT13 encoding."""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot13(self, encoded_text: str) -> str:
        """Decode ROT13 (same as encoding)."""
        return self._encode_rot13(encoded_text)

    def _encode_rot18(self, text: str) -> str:
        """Apply ROT18 encoding (ROT13 for letters + ROT5 for digits)."""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
            elif char.isdigit():
                result.append(str((int(char) + 5) % 10))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot18(self, encoded_text: str) -> str:
        """Decode ROT18 (reverse ROT13 + ROT5)."""
        result = []
        for char in encoded_text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') - 13) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') - 13) % 26 + ord('A')))
            elif char.isdigit():
                result.append(str((int(char) - 5) % 10))
            else:
                result.append(char)
        return ''.join(result)

    def _encode_rot25(self, text: str) -> str:
        """Apply ROT25 encoding (rotate letters by 25, equivalent to ROT-1)."""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 25) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 25) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot25(self, encoded_text: str) -> str:
        """Decode ROT25 (rotate letters by 1)."""
        result = []
        for char in encoded_text:
            if 'a' <= char <= 'z':
                result.append(chr((ord(char) - ord('a') + 1) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                result.append(chr((ord(char) - ord('A') + 1) % 26 + ord('A')))
            else:
                result.append(char)
        return ''.join(result)

    def _encode_rot32(self, text: str) -> str:
        """Apply ROT32 encoding (rotate printable ASCII by 32)."""
        result = []
        for char in text:
            if 32 <= ord(char) <= 126:
                result.append(chr((ord(char) - 32 + 32) % 95 + 32))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot32(self, encoded_text: str) -> str:
        """Decode ROT32 (rotate printable ASCII by -32)."""
        result = []
        for char in encoded_text:
            if 32 <= ord(char) <= 126:
                result.append(chr((ord(char) - 32 - 32) % 95 + 32))
            else:
                result.append(char)
        return ''.join(result)

    def _encode_rot47(self, text: str) -> str:
        """Apply ROT47 encoding (rotate printable ASCII by 47)."""
        result = []
        for char in text:
            if 33 <= ord(char) <= 126:
                result.append(chr((ord(char) - 33 + 47) % 94 + 33))
            else:
                result.append(char)
        return ''.join(result)

    def _decode_rot47(self, encoded_text: str) -> str:
        """Decode ROT47 (rotate printable ASCII by -47)."""
        result = []
        for char in encoded_text:
            if 33 <= ord(char) <= 126:
                result.append(chr((ord(char) - 33 - 47) % 94 + 33))
            else:
                result.append(char)
        return ''.join(result)

    def _encode_url(self, text: str) -> str:
        """URL encode text."""
        return urllib.parse.quote(text)

    def _decode_url(self, encoded_text: str) -> str:
        """URL decode text."""
        return urllib.parse.unquote(encoded_text)

    # Special encoding methods
    def _encode_morse_code(self, text: str) -> str:
        """Encode text to Morse code."""
        result = []
        for char in text.upper():
            if char in self.morse_code_map:
                result.append(self.morse_code_map[char])
            elif char == ' ':
                result.append('/')
            else:
                result.append(char)
        return ' '.join(result)

    def _decode_morse_code(self, encoded_text: str) -> str:
        """Decode text from Morse code."""
        morse_to_char = {v: k for k, v in self.morse_code_map.items()}
        morse_chars = encoded_text.split()
        result = []
        for morse_char in morse_chars:
            if morse_char == '/':
                result.append(' ')
            elif morse_char in morse_to_char:
                result.append(morse_to_char[morse_char])
            else:
                result.append(morse_char)
        return ''.join(result)

    def _encode_nato_phonetic(self, text: str) -> str:
        """Encode text to NATO phonetic alphabet."""
        result = []
        for char in text.upper():
            if char in self.nato_phonetic_map:
                result.append(self.nato_phonetic_map[char])
            else:
                result.append(char)
        return ' '.join(result)

    def _decode_nato_phonetic(self, encoded_text: str) -> str:
        """Decode text from NATO phonetic alphabet."""
        phonetic_to_char = {v: k for k, v in self.nato_phonetic_map.items()}
        phonetic_words = encoded_text.split()
        result = []
        for word in phonetic_words:
            if word in phonetic_to_char:
                result.append(phonetic_to_char[word])
            else:
                result.append(word)
        return ''.join(result)

    def _encode_diacritics(self, text: str) -> str:
        """Encode text using diacritics."""
        result = []
        for char in text.upper():
            if char in self.diacritics_map:
                # Use the first diacritic variant
                result.append(self.diacritics_map[char][0])
            else:
                result.append(char)
        return ''.join(result)

    def _decode_diacritics(self, encoded_text: str) -> str:
        """Decode text from diacritics."""
        char_to_diacritic = {}
        for base_char, diacritics in self.diacritics_map.items():
            for diacritic in diacritics:
                char_to_diacritic[diacritic] = base_char
        
        result = []
        for char in encoded_text:
            if char in char_to_diacritic:
                result.append(char_to_diacritic[char])
            else:
                result.append(char)
        return ''.join(result)

    def _encode_braille(self, text: str) -> str:
        """Encode text to Braille."""
        result = []
        for char in text.upper():
            if char in self.braille_map:
                result.append(self.braille_map[char])
            else:
                result.append(char)
        return ''.join(result)

    def _decode_braille(self, encoded_text: str) -> str:
        """Decode text from Braille."""
        braille_to_char = {v: k for k, v in self.braille_map.items()}
        result = []
        for char in encoded_text:
            if char in braille_to_char:
                result.append(braille_to_char[char])
            else:
                result.append(char)
        return ''.join(result)


def get_available_methods() -> List[str]:
    """Get list of all available encoding methods."""
    return [method.value for method in EncodingMethod]


def parse_encoding_methods(methods_str: str) -> List[EncodingMethod]:
    """Parse comma-separated encoding methods string."""
    methods = []
    for method_str in methods_str.split(','):
        method_str = method_str.strip().lower()
        try:
            methods.append(EncodingMethod(method_str))
        except ValueError:
            raise ValueError(f"Unknown encoding method: {method_str}")
    return methods
