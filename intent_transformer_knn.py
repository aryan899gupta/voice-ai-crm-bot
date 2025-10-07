# intent_verbs_knn.py

from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np
import json
import argparse

from syntheticData.verb_intent_data import INTENT_VERBS
from syntheticData.keyword_intent_data import INTENT_KEYWORDS
from syntheticData.regex_parser import regex_score

from logger_config import logger

import logging
import os

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

# Disable tqdm progress bars globally
import tqdm
tqdm.tqdm = lambda *args, **kwargs: iter(args[0])

# Model config
EMBED_MODEL_NAME = "all-mpnet-base-v2"
K = 4  # neighbors for each index

logger.info("[info] Loading embedding model {EMBED_MODEL_NAME}")
model = SentenceTransformer(EMBED_MODEL_NAME)

# Building verb indices
verbs = []
verb_labels = []
for intent, vlist in INTENT_VERBS.items():
    for v in vlist:
        verbs.append(v)
        verb_labels.append(intent)

verb_embs = model.encode(verbs, normalize_embeddings=True)
nn_verbs = NearestNeighbors(n_neighbors=min(K, len(verbs)), metric="cosine")
nn_verbs.fit(verb_embs)

# Building keyword indices
keywords = []
kw_labels = []
for intent, klist in INTENT_KEYWORDS.items():
    for k in klist:
        keywords.append(k)
        kw_labels.append(intent)

kw_embs = model.encode(keywords, normalize_embeddings=True)
nn_keywords = NearestNeighbors(n_neighbors=min(K, len(keywords)), metric="cosine")
nn_keywords.fit(kw_embs)


INTENTS = list(INTENT_VERBS.keys())

# KNN SCORING
def _knn_score_from_index(text: str, nn: NearestNeighbors, ref_list, ref_labels, k: int = K, debug=False, debug_prefix=""):
    emb = model.encode([text], normalize_embeddings=True)
    emb = np.array(emb)
    k_use = min(k, len(ref_list))
    dists, idxs = nn.kneighbors(emb, n_neighbors=k_use, return_distance=True)
    dists = dists[0]
    idxs = idxs[0]
    sims = 1.0 - dists
    sims = np.clip(sims, 0.0, None) 

    if debug:
        logger.info(f"\n[debug {debug_prefix}] nearest neighbors (rank, token, intent, sim):")
        for rank, (idx, sim) in enumerate(zip(idxs, sims), start=1):
            token = ref_list[idx]
            label = ref_labels[idx]
            logger.info(f"  {rank:>2}. {token!r:<25} ({label})   sim={sim:.4f}")
        logger.info()

    agg = {intent: 0.0 for intent in INTENTS}
    for sim, idx in zip(sims, idxs):
        label = ref_labels[idx]
        agg[label] += float(sim)

    total = sum(agg.values())
    if total <= 0:
        uniform = 1.0 / len(agg)
        return {intent: uniform for intent in agg}

    # normalize
    return {intent: float(score / total) for intent, score in agg.items()}

# Combined scoring algorithm: average of verb, keyword and regex scores
def score_intents_avg(text: str, k: int = K, verbose: bool = False):
    verb_scores = _knn_score_from_index(text, nn_verbs, verbs, verb_labels, k=k, debug=verbose, debug_prefix="VERB")
    kw_scores = _knn_score_from_index(text, nn_keywords, keywords, kw_labels, k=k, debug=verbose, debug_prefix="KW")
    regex_scores, regex_matches = regex_score(text, per_match_score=0.5, max_per_intent=2.0)
    if verbose:
        logger.info("[debug] regex_scores: %s", {k: round(v, 3) for k, v in regex_scores.items()})
        if regex_matches:
            logger.info("[debug] regex_matches: %s", regex_matches)
        else:
            logger.info("[debug] regex_matches: None")


    combined_raw = {intent: 0.0 for intent in INTENTS}
    for intent in INTENTS:
        v = verb_scores.get(intent, 0.0)
        w = kw_scores.get(intent, 0.0)
        r = regex_scores.get(intent, 0.0)
        combined_raw[intent] = (v + w + r) / 3.0

    # normalize
    total = sum(combined_raw.values())
    if total <= 0:
        uniform = 1.0 / len(INTENTS)
        combined = {intent: uniform for intent in INTENTS}
    else:
        combined = {intent: float(combined_raw[intent] / total) for intent in INTENTS}

    return verb_scores, kw_scores, regex_scores, combined



# CLI (FOR TESTING)
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="kNN intent scorer: verb + keyword average")
    p.add_argument("--text", type=str, required=True, help="Input sentence to score")
    p.add_argument("--k", type=int, default=K, help="Number of neighbors")
    p.add_argument("--verbose", action="store_true", help="Show debug neighbor lists")
    args = p.parse_args()

    v_s, k_s, r_s, combined = score_intents_avg(args.text, k=args.k, verbose=args.verbose)

    out = {
        "verb_scores": {k: round(v, 3) for k, v in v_s.items()},
        "keyword_scores": {k: round(v, 3) for k, v in k_s.items()},
        "regex_scores": {k: round(v, 3) for k, v in r_s.items()},
        "combined_final": {k: round(v, 3) for k, v in combined.items()}
    }

    print(json.dumps(out, indent=2))