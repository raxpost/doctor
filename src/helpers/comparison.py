import numpy as np
import os
from fuzzywuzzy import fuzz
import re
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import jaccard_score
from sklearn.feature_extraction.text import CountVectorizer

embedding_model = None

# lazy load not to load the tool with no need
def model_singleton():
    model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    global embedding_model
    if embedding_model:
        return embedding_model
    #embedding_model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")
    embedding_model = SentenceTransformer(model_name) # best relevance
    return embedding_model

cache1 = None
cache2 = None

cache = {}

def fuzzy_score_lists(chunks1, chunks2):
    max_score = -1
    best_pair = (-1, -1)
    
    for i, a in enumerate(chunks1):
        for j, b in enumerate(chunks2):
            score = fuzz.token_set_ratio(a, b)
            if score > max_score:
                max_score = score
                best_pair = (i, j)
    
    return best_pair, max_score

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

def fuzzrat(str1, str2):
    return fuzz.token_sort_ratio(str1, str2)

def hybrid_score(str1, str2, cosine):
    """Core scoring logic with dynamic weights"""
    # Base scores
    str1 = normalize_string(str1)
    str2 = normalize_string(str2)
    
    fuzz_rat = fuzz.token_set_ratio(str1, str2) / 100
    lcs = longest_common_substring_score(str1, str2)
    
    # Dynamic weighting
    is_short = len(str1) < 20 or len(str2) < 20
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

def jaccard(text1, text2):
    vectorizer = CountVectorizer(binary=True).fit([text1, text2])
    vectors = vectorizer.transform([text1, text2])
    return jaccard_score(vectors[0].toarray()[0], vectors[1].toarray()[0])

def map_texts_fuzz(chunks1, chunks2):
    res = []
    for c1 in chunks1:
        c2res = []
        for c2 in chunks2:
            c2res.append(jaccard(c1, c2))
        res.append(c2res)
    return res

def map_texts_cosine_with_cache(chunks1, chunks2):
    model = model_singleton()
    h1 = str(hash("".join(chunks1)))
    h2 = str(hash("".join(chunks2)))
    
    emb2 = model.encode(chunks2)
    if h1 in cache:
        emb1 = cache[h1]
    else:
        emb1 = model.encode(chunks1)
        cache[h1] = emb1
    if h2 in cache:
        emb2 = cache[h2]
    else:
        emb2 = model.encode(chunks2)
        cache[h2] = emb2

    return cosine_similarity(emb1, emb2)


# compares two lists of strings. many to many.
# for each item on left calculates max hybrid score on the right
# keeps matched_rights dict with indices to restore matches
def hybrid_strings_lists_comparison(items1, items2, threshold=0.6):
    total_scores = []
    items1 = [str(item) for item in items1 if str(item).strip() != ""]
    items2 = [str(item) for item in items2 if str(item).strip() != ""]
    
    matrix = map_texts_cosine_with_cache(items1, items2)
    i2s_already_matched_with_i1s = []
    matched_rights = {}
    for i1, items in enumerate(matrix):
        scores = []
        mx = 0
        mx_right_i = -1
        for i2, cosine in enumerate(items):
            # avoid duplicates in the left column
            if i2 in i2s_already_matched_with_i1s:
                continue
            rat = hybrid_score(items1[i1], items2[i2], cosine)
            #print(rat, items1[i1], items2[i2])
            if rat > threshold and rat > mx:
                mx = rat
                mx_right_i = i2
                scores.append(rat)
                i2s_already_matched_with_i1s.append(i2)
        max_score = mx
        # avoid duplicates in the right column
        total_scores.append(max_score)
        if mx_right_i != -1:
            matched_rights[mx_right_i] = {"score": max_score, "with": i1}
    return total_scores, matched_rights