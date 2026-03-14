# services/chat/alpha_ai_model/stock_resolver/korean_utils.py
"""
Korean Language Utilities for Stock Resolver

Provides Korean text processing functions:
- decompose_korean: Decompose Hangul into jamo (consonants and vowels)
- extract_chosung: Extract initial consonants only
- is_korean: Check if text contains Korean characters
- normalize_korean: Normalize Korean text for comparison
"""

# Hangul jamo lists
CHOSUNG = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]

JUNGSUNG = [
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ',
    'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
]

JONGSUNG = [
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ',
    'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]


def decompose_korean(text: str) -> str:
    """
    Decompose Korean Hangul syllables into jamo (consonants and vowels)

    Args:
        text: Korean text string

    Returns:
        Jamo-decomposed string

    Example:
        >>> decompose_korean("삼성")
        'ㅅㅏㅁㅅㅓㅇ'
        >>> decompose_korean("삼전")
        'ㅅㅏㅁㅈㅓㄴ'
    """
    result = []

    for char in text:
        code = ord(char)

        # Hangul syllable range (가 ~ 힣: 0xAC00 ~ 0xD7A3)
        if 0xAC00 <= code <= 0xD7A3:
            # Decompose syllable
            code -= 0xAC00
            cho = code // (21 * 28)
            jung = (code % (21 * 28)) // 28
            jong = code % 28

            result.append(CHOSUNG[cho])
            result.append(JUNGSUNG[jung])
            if jong > 0:
                result.append(JONGSUNG[jong])
        else:
            # Non-Korean characters pass through
            result.append(char)

    return ''.join(result)


def extract_chosung(text: str) -> str:
    """
    Extract only initial consonants (chosung) from Korean text

    Args:
        text: Korean text string

    Returns:
        String of initial consonants only

    Example:
        >>> extract_chosung("삼성전자")
        'ㅅㅅㅈㅈ'
        >>> extract_chosung("SK하이닉스")
        'SKㅎㅇㄴㅅ'
    """
    result = []

    for char in text:
        code = ord(char)

        # Hangul syllable range
        if 0xAC00 <= code <= 0xD7A3:
            cho = (code - 0xAC00) // (21 * 28)
            result.append(CHOSUNG[cho])
        else:
            result.append(char)

    return ''.join(result)


def is_korean(text: str) -> bool:
    """
    Check if text contains any Korean characters

    Args:
        text: Input text string

    Returns:
        True if text contains Korean characters, False otherwise

    Example:
        >>> is_korean("삼성전자")
        True
        >>> is_korean("Apple")
        False
        >>> is_korean("SK하이닉스")
        True
    """
    for char in text:
        code = ord(char)
        # Hangul syllable range (가 ~ 힣)
        if 0xAC00 <= code <= 0xD7A3:
            return True
        # Hangul jamo range (ㄱ ~ ㅣ)
        if 0x3131 <= code <= 0x3163:
            return True
    return False


def normalize_korean(text: str) -> str:
    """
    Normalize Korean text for comparison

    - Removes whitespace
    - Converts to lowercase
    - Strips leading/trailing whitespace

    Args:
        text: Input text string

    Returns:
        Normalized text string

    Example:
        >>> normalize_korean("SK 하이닉스")
        'sk하이닉스'
        >>> normalize_korean("  삼성전자  ")
        '삼성전자'
    """
    return text.replace(' ', '').lower().strip()


def get_korean_similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two Korean texts using jamo decomposition

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score (0.0 ~ 1.0)
    """
    # Decompose both texts
    decomposed1 = decompose_korean(text1)
    decomposed2 = decompose_korean(text2)

    # Simple character-based similarity
    if not decomposed1 or not decomposed2:
        return 0.0

    # Check if one is substring of the other
    if decomposed1 in decomposed2 or decomposed2 in decomposed1:
        shorter = min(len(decomposed1), len(decomposed2))
        longer = max(len(decomposed1), len(decomposed2))
        return shorter / longer

    # Character overlap
    set1 = set(decomposed1)
    set2 = set(decomposed2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union
