import numpy as np
from fuzzywuzzy import fuzz
import re

def longest_common_substring_score(a, b):
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0.0

    dp = [[0]*(n+1) for _ in range(m+1)]
    max_len = 0
    i_of_max = 0
    j_of_max = 0

    # Fill DP table
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                dp[i+1][j+1] = dp[i][j] + 1
                if dp[i+1][j+1] > max_len:
                    max_len = dp[i+1][j+1]
                    i_of_max = i
                    j_of_max = j

    length_score = max_len / min(m, n)

    # Earliest start index of the matched substring in both strings
    start_i = i_of_max + 1 - max_len
    start_j = j_of_max + 1 - max_len

    # Position factor: the closer to the front, the higher the score
    # This simple formula penalizes matches that start further along in the string
    position_factor = 1.0 - ((start_i/m + start_j/n) / 2)
    # Stronger penalty for being far from the start
    # The substring can't start any later than n - max_len
    denom = (n - max_len + 1) if (n - max_len + 1) else 1
    position_factor = 1.0 - (start_j / denom)
    position_factor = max(0, min(position_factor, 1))

    return length_score * position_factor

def normalize_string(txt):
    txt = txt.replace("_", " ")
    # If not upper case ENV_VAR style, split by camel case
    if not re.match(r"^[A-Z ]+$", txt):
        # setting space before capital letter
        txt = re.sub(r'(?<!^)(?<=[^A-Z])([A-Z])', r' \1', txt)
    return txt

def hybrid_score(str1, str2, cosine):
    """Core scoring logic with dynamic weights"""
    # Base scores
    str1 = normalize_string(str1)
    str2 = normalize_string(str2)
    
    fuzz_rat = fuzz.token_set_ratio(str1, str2) / 100
    lcs = longest_common_substring_score(str1, str2)
    
    # Dynamic weighting
    is_short = len(str1) < 20 and len(str2) < 20
    if is_short:
        weights = [0.4, 0.1, 0.5]  # Focus on lexical
    else:
        # Here embeddings work better because of the context
        weights = [0.2, 0.6, 0.2]  # Focus on semantic
        
    # Combine scores
    base_score = np.clip(
        (fuzz_rat * weights[0]) +
        (cosine * weights[1]) +
        (lcs * weights[2]),
        0, 1
    )
    return base_score