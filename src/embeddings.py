from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("BAAI/bge-m3") # best relevance. threshold 0.65

cache1 = None
cache2 = None

cache = {}

def map_texts_cosine_with_cache(chunks1, chunks2):
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