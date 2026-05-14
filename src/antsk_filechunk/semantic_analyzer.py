"""
Semantic analysis helpers for the chunking service.
"""

import logging
import os
import re
import threading
from collections import Counter, OrderedDict
from typing import Dict, List, Optional, Tuple

import jieba
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Compute embeddings and lightweight semantic metrics."""

    _MODEL_CACHE: Dict[str, SentenceTransformer] = {}
    _MODEL_CACHE_LOCK = threading.Lock()
    _EMBEDDING_CACHE: "OrderedDict[str, np.ndarray]" = OrderedDict()
    _EMBEDDING_CACHE_LOCK = threading.Lock()
    _EMBEDDING_CACHE_MAX_SIZE = 4096

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", language: str = "zh"):
        self.model_name = model_name
        self.language = language
        self.model: Optional[SentenceTransformer] = None
        self.stopwords_set = set()

        self._initialize_model()
        self._initialize_language_resources()

    def _initialize_model(self) -> None:
        """Load the embedding model once and reuse it across instances."""
        try:
            logger.info("Loading semantic model: %s", self.model_name)
            self.model = self._get_or_load_model(self.model_name)
            logger.info("Semantic model ready")
        except Exception as exc:
            logger.error("Failed to load semantic model %s: %s", self.model_name, exc)
            fallback_models = [
                "paraphrase-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "distilbert-base-nli-stsb-mean-tokens",
            ]

            for fallback_model in fallback_models:
                try:
                    logger.info("Trying fallback model: %s", fallback_model)
                    self.model = self._get_or_load_model(fallback_model)
                    self.model_name = fallback_model
                    logger.info("Fallback model ready: %s", fallback_model)
                    break
                except Exception as fallback_exc:
                    logger.warning(
                        "Fallback model %s also failed: %s",
                        fallback_model,
                        fallback_exc,
                    )

            if self.model is None:
                raise RuntimeError("Unable to load any semantic embedding model")

    @classmethod
    def _get_or_load_model(cls, model_name: str) -> SentenceTransformer:
        with cls._MODEL_CACHE_LOCK:
            cached_model = cls._MODEL_CACHE.get(model_name)
            if cached_model is not None:
                logger.info("Reusing cached semantic model: %s", model_name)
                return cached_model

            model = SentenceTransformer(model_name)
            cls._MODEL_CACHE[model_name] = model
            return model

    def _initialize_language_resources(self) -> None:
        """Prepare tokenization helpers for the configured language."""
        try:
            if self.language == "en":
                try:
                    nltk.data.find("tokenizers/punkt")
                except LookupError:
                    nltk.download("punkt", quiet=True)

                try:
                    nltk.data.find("corpora/stopwords")
                except LookupError:
                    nltk.download("stopwords", quiet=True)

                self.stopwords_set = set(stopwords.words("english"))
            else:
                self.stopwords_set = {
                    "的",
                    "了",
                    "在",
                    "是",
                    "我",
                    "有",
                    "和",
                    "就",
                    "不",
                    "人",
                    "都",
                    "一",
                    "一个",
                    "上",
                    "也",
                    "很",
                    "到",
                    "说",
                    "要",
                    "去",
                    "你",
                    "会",
                    "着",
                    "没有",
                    "看",
                    "好",
                    "自己",
                    "这",
                    "那",
                    "里",
                    "就是",
                    "还",
                }

            logger.info("Language resources ready for %s", self.language)
        except Exception as exc:
            logger.warning("Language resources were only partially initialized: %s", exc)

    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """Compute sentence embeddings with shared LRU caching."""
        if not texts:
            return np.array([])

        try:
            logger.info("Computing embeddings for %s texts", len(texts))
            processed_texts = [self._preprocess_text(text) for text in texts]
            embeddings = self._compute_embeddings_with_cache(processed_texts)
            logger.info("Embedding computation complete with shape %s", embeddings.shape)
            return embeddings
        except Exception as exc:
            logger.error("Embedding computation failed: %s", exc)
            raise

    def _compute_embeddings_with_cache(self, processed_texts: List[str]) -> np.ndarray:
        if not processed_texts:
            return np.array([])

        ordered_results: List[Optional[np.ndarray]] = [None] * len(processed_texts)
        missing_indexes: List[int] = []
        missing_texts: List[str] = []

        for index, text in enumerate(processed_texts):
            cache_key = self._get_embedding_cache_key(text)
            cached_embedding = self._get_cached_embedding(cache_key)
            if cached_embedding is None:
                missing_indexes.append(index)
                missing_texts.append(text)
            else:
                ordered_results[index] = cached_embedding

        if missing_texts:
            unique_missing_texts = list(dict.fromkeys(missing_texts))
            encoded_embeddings = self.model.encode(
                unique_missing_texts,
                show_progress_bar=self._should_show_progress_bar(),
                batch_size=self._resolve_batch_size(len(unique_missing_texts)),
                normalize_embeddings=True,
            )

            encoded_lookup = {
                text: np.asarray(embedding)
                for text, embedding in zip(unique_missing_texts, encoded_embeddings)
            }

            for text, embedding in encoded_lookup.items():
                self._store_cached_embedding(self._get_embedding_cache_key(text), embedding)

            for index in missing_indexes:
                ordered_results[index] = encoded_lookup[processed_texts[index]]

        return np.asarray(ordered_results)

    def _get_embedding_cache_key(self, text: str) -> str:
        return f"{self.model_name}:{self.language}:{text}"

    @classmethod
    def _get_cached_embedding(cls, cache_key: str) -> Optional[np.ndarray]:
        with cls._EMBEDDING_CACHE_LOCK:
            embedding = cls._EMBEDDING_CACHE.get(cache_key)
            if embedding is None:
                return None

            cls._EMBEDDING_CACHE.move_to_end(cache_key)
            return embedding.copy()

    @classmethod
    def _store_cached_embedding(cls, cache_key: str, embedding: np.ndarray) -> None:
        with cls._EMBEDDING_CACHE_LOCK:
            cls._EMBEDDING_CACHE[cache_key] = np.asarray(embedding).copy()
            cls._EMBEDDING_CACHE.move_to_end(cache_key)

            while len(cls._EMBEDDING_CACHE) > cls._EMBEDDING_CACHE_MAX_SIZE:
                cls._EMBEDDING_CACHE.popitem(last=False)

    def _resolve_batch_size(self, text_count: int) -> int:
        batch_size = os.getenv("ANTSK_EMBEDDING_BATCH_SIZE")
        if batch_size:
            try:
                return max(1, int(batch_size))
            except ValueError:
                logger.warning(
                    "Invalid ANTSK_EMBEDDING_BATCH_SIZE=%s, using defaults",
                    batch_size,
                )

        if text_count >= 128:
            return 64
        if text_count >= 32:
            return 32
        return max(8, text_count)

    def _should_show_progress_bar(self) -> bool:
        env_value = os.getenv("ANTSK_SHOW_EMBEDDING_PROGRESS", "").strip().lower()
        return env_value in {"1", "true", "yes", "on"}

    def _preprocess_text(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        if text.startswith("[IMAGE_PLACEHOLDER_"):
            return "图片内容"

        text = re.sub(r"\s+", " ", text.strip())

        max_length = 512 if self.language == "zh" else 256
        if len(text) > max_length:
            text = text[:max_length]

        return text

    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        if embeddings.size == 0:
            return np.array([])

        try:
            return cosine_similarity(embeddings)
        except Exception as exc:
            logger.error("Failed to compute similarity matrix: %s", exc)
            raise

    def find_semantic_boundaries(
        self,
        embeddings: np.ndarray,
        threshold: float = 0.6,
        window_size: int = 5,
    ) -> List[int]:
        if len(embeddings) < 2:
            return []

        boundaries = [0]

        try:
            similarities = []
            for index in range(len(embeddings) - 1):
                similarity = cosine_similarity(
                    embeddings[index : index + 1],
                    embeddings[index + 1 : index + 2],
                )[0][0]
                similarities.append(similarity)

            if len(similarities) > window_size:
                smoothed = []
                for index in range(len(similarities)):
                    start_index = max(0, index - window_size // 2)
                    end_index = min(len(similarities), index + window_size // 2 + 1)
                    smoothed.append(float(np.mean(similarities[start_index:end_index])))
                similarities = smoothed

            for index, similarity in enumerate(similarities):
                if similarity < threshold:
                    boundaries.append(index + 1)

            if boundaries[-1] != len(embeddings):
                boundaries.append(len(embeddings))

            return boundaries
        except Exception as exc:
            logger.error("Failed to detect semantic boundaries: %s", exc)
            return [0, len(embeddings)]

    def analyze_topic_coherence(
        self,
        texts: List[str],
        embeddings: Optional[np.ndarray] = None,
    ) -> Dict:
        if not texts:
            return {"coherence_score": 0.0, "topic_distribution": []}

        try:
            if embeddings is None:
                embeddings = self.compute_embeddings(texts)

            if len(embeddings) > 1:
                similarity_matrix = self.compute_similarity_matrix(embeddings)
                upper_triangle = np.triu(similarity_matrix, k=1)
                non_zero_count = np.count_nonzero(upper_triangle)
                coherence_score = (
                    np.sum(upper_triangle) / non_zero_count if non_zero_count > 0 else 0.0
                )
            else:
                coherence_score = 1.0

            return {
                "coherence_score": float(coherence_score),
                "topic_distribution": self._analyze_topic_distribution(texts, embeddings),
                "text_count": len(texts),
                "avg_similarity": float(coherence_score),
            }
        except Exception as exc:
            logger.error("Failed to analyze topic coherence: %s", exc)
            return {"coherence_score": 0.0, "topic_distribution": []}

    def _analyze_topic_distribution(
        self,
        texts: List[str],
        embeddings: np.ndarray,
    ) -> List[Dict]:
        try:
            from sklearn.cluster import KMeans

            if len(embeddings) < 2:
                centroid = embeddings[0].tolist() if len(embeddings) > 0 else []
                return [{"topic_id": 0, "texts": list(range(len(texts))), "centroid": centroid}]

            n_clusters = min(max(2, len(texts) // 3), 5)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)

            topic_distribution = []
            for cluster_id in range(n_clusters):
                cluster_indexes = np.where(cluster_labels == cluster_id)[0]
                if len(cluster_indexes) > 0:
                    topic_distribution.append(
                        {
                            "topic_id": cluster_id,
                            "texts": cluster_indexes.tolist(),
                            "centroid": kmeans.cluster_centers_[cluster_id].tolist(),
                            "size": len(cluster_indexes),
                        }
                    )

            return topic_distribution
        except Exception as exc:
            logger.warning("Failed to analyze topic distribution: %s", exc)
            return []

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        try:
            embeddings = self.compute_embeddings([text1, text2])
            if len(embeddings) != 2:
                return 0.0

            similarity = cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0]
            return float(similarity)
        except Exception as exc:
            logger.error("Failed to calculate text similarity: %s", exc)
            return 0.0

    def extract_key_phrases(self, text: str, top_k: int = 10) -> List[str]:
        try:
            if self.language == "zh":
                words = [word for word in jieba.cut(text) if len(word) > 1 and word not in self.stopwords_set]
            else:
                words = [
                    word
                    for word in word_tokenize(text.lower())
                    if word.isalpha() and word not in self.stopwords_set
                ]

            return [word for word, _ in Counter(words).most_common(top_k)]
        except Exception as exc:
            logger.warning("Failed to extract key phrases: %s", exc)
            return []

    def detect_semantic_shifts(
        self,
        embeddings: np.ndarray,
        sensitivity: float = 0.3,
    ) -> List[Tuple[int, float]]:
        if len(embeddings) < 3:
            return []

        try:
            shifts = []
            for index in range(1, len(embeddings) - 1):
                prev_similarity = cosine_similarity(
                    embeddings[index - 1 : index],
                    embeddings[index : index + 1],
                )[0][0]
                next_similarity = cosine_similarity(
                    embeddings[index : index + 1],
                    embeddings[index + 1 : index + 2],
                )[0][0]

                shift_intensity = abs(prev_similarity - next_similarity)
                if shift_intensity > sensitivity:
                    shifts.append((index, float(shift_intensity)))

            shifts.sort(key=lambda item: item[1], reverse=True)
            return shifts
        except Exception as exc:
            logger.error("Failed to detect semantic shifts: %s", exc)
            return []

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        with cls._EMBEDDING_CACHE_LOCK:
            embedding_cache_size = len(cls._EMBEDDING_CACHE)
        with cls._MODEL_CACHE_LOCK:
            model_cache_size = len(cls._MODEL_CACHE)

        return {
            "model_cache_size": model_cache_size,
            "embedding_cache_size": embedding_cache_size,
            "embedding_cache_capacity": cls._EMBEDDING_CACHE_MAX_SIZE,
        }

    @classmethod
    def clear_caches(cls) -> None:
        with cls._MODEL_CACHE_LOCK:
            cls._MODEL_CACHE.clear()
        with cls._EMBEDDING_CACHE_LOCK:
            cls._EMBEDDING_CACHE.clear()
