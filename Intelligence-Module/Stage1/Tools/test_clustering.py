"""
Test Clustering Module for Stage-1.

Clusters executed tests using agglomerative hierarchical clustering
to select diverse representative tests for LLM prompts.

Algorithm:
    Agglomerative hierarchical clustering
    Cosine distance, average linkage
    Dendrogram cut at k = ceil(sqrt(n)) where n = total tests generated

Per iteration:
    Re-clusters ALL executed tests from scratch.
    n grows as iterations progress (n ≈ iteration × MAX_TESTS_PER_CALL).

Representative selection:
    Per cluster: test with highest score (coverage delta + bug signal).

Consumers:
    llm_test_generator.py — receives representative raw tests for prompt.
    LLM never sees signatures, only raw representative tests.
"""
import math
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from Stage1.config import MAX_CLUSTER_CAP


class Test_Clustering_Engine:
    def __init__(self, max_cluster_cap=None):
        """
        Args:
            max_cluster_cap: optional hard upper bound on cluster count
        """
        self.max_cluster_cap = max_cluster_cap if max_cluster_cap is not None else MAX_CLUSTER_CAP

    def cluster(self, tests, signatures):
        """
        Cluster tests and return representative raw tests.

        Args:
            tests: list of executed test dicts (raw, all fields intact)
            signatures: list of signature dicts from Test_Signature_Engine
                        (each has cluster_vector, score, test_id)

        Returns:
            {
                "k": int,
                "representatives": [raw_test, ...],
                "cluster_metadata": [
                    {
                        "cluster_id": int,
                        "size": int,
                        "representative_test_id": str,
                        "member_test_ids": [str, ...],
                        "mean_score": float
                    },
                    ...
                ]
            }
        """
        n = len(tests)

        if n == 0:
            return {"k": 0, "representatives": [], "cluster_metadata": []}

        if n <= 2:
            return self._trivial_clustering(tests, signatures)

        # Compute k
        k = math.ceil(math.sqrt(n))
        if self.max_cluster_cap:
            k = min(k, self.max_cluster_cap)
        k = min(k, n)

        # Cluster
        vectors = np.array([sig["cluster_vector"] for sig in signatures])

        row_norms = np.linalg.norm(vectors, axis=1)
        zero_mask = row_norms == 0
        if np.any(zero_mask):
            vectors[zero_mask] = 1e-10

        model = AgglomerativeClustering(
            n_clusters=k,
            metric="cosine",
            linkage="average"
        )
        labels = model.fit_predict(vectors)

        # Build results
        return self._build_results(tests, signatures, labels, k)

    def _build_results(self, tests, signatures, labels, k):
        """Select representatives and build cluster metadata."""
        representatives = []
        cluster_metadata = []

        for cluster_id in range(k):
            member_indices = [i for i, label in enumerate(labels) if label == cluster_id]

            if not member_indices:
                continue

            # Representative: highest score in cluster
            best_idx = max(member_indices, key=lambda i: signatures[i]["score"])
            representatives.append(tests[best_idx])

            member_scores = [signatures[i]["score"] for i in member_indices]
            member_ids = [signatures[i]["test_id"] for i in member_indices]

            cluster_metadata.append({
                "cluster_id": cluster_id,
                "size": len(member_indices),
                "representative_test_id": signatures[best_idx]["test_id"],
                "member_test_ids": member_ids,
                "mean_score": sum(member_scores) / len(member_scores)
            })

        return {
            "k": k,
            "representatives": representatives,
            "cluster_metadata": cluster_metadata
        }

    def _trivial_clustering(self, tests, signatures):
        """n <= 2: each test is its own cluster."""
        representatives = list(tests)
        cluster_metadata = []

        for i, (test, sig) in enumerate(zip(tests, signatures)):
            cluster_metadata.append({
                "cluster_id": i,
                "size": 1,
                "representative_test_id": sig["test_id"],
                "member_test_ids": [sig["test_id"]],
                "mean_score": sig["score"]
            })

        return {
            "k": len(tests),
            "representatives": representatives,
            "cluster_metadata": cluster_metadata
        }