"""
Test Signature Module for Stage-1.

Computes a fixed-dimension numeric signature per test for clustering.

Signature components:
    Static  — coverage region: where in the code this test exercises
              2 floats: [position_centroid, spread]
              Scaled by deterministic weight: sqrt(dynamic_dim / static_dim)

    Dynamic — operation activation profile:
              TF-IDF weighted frequencies (name-only, pruned vocabulary)
              + 3 failure indicators (weighted × WEIGHT_FAILURE)
              + M group activations (conditional: only when vocab < MIN_VOCAB_FOR_GROUPS)
              All L2 normalized after weighting.

    Score   — coverage delta + bug confidence (representative selection only)

Pruning:
    Operations with document frequency < MIN_DOC_FREQ are dropped.
    Remaining vocabulary capped at MAX_VOCAB_SIZE by descending doc frequency.

IDF smoothing:
    idf = log((doc_count + 1) / (df + 1)) + 1

Static-dynamic balancing:
    weight_static = sqrt(dynamic_dim / 2)
    Applied to static sub-vector before concatenation with dynamic.

Group features:
    Included only when pruned vocab < MIN_VOCAB_FOR_GROUPS.
    Prevents double-counting when TF-IDF already captures enough signal.

Failure signal:
    Weighted × WEIGHT_FAILURE (default 2.0) before normalization.
    Ensures bug-triggering tests form distinct clusters.
"""
import uuid
import math
from collections import Counter
from Stage1.config import MAX_VOCAB_SIZE, MIN_DOC_FREQ, WEIGHT_TFIDF, WEIGHT_FAILURE, MIN_VOCAB_FOR_GROUPS


# ── Operation category grouping ──
OPERATION_GROUPS = {
    # Math
    "add": "math", "sub": "math", "mult": "math", "div": "math",
    "floordiv": "math", "mod": "math", "pow": "math",
    "log": "math", "sqrt": "math", "abs": "math", "ceil": "math",
    "floor": "math", "round": "math", "sum": "math", "min": "math",
    "max": "math",

    # Comparison
    "eq": "comparison", "noteq": "comparison", "lt": "comparison",
    "lteq": "comparison", "gt": "comparison", "gteq": "comparison",
    "is_": "comparison", "isnot": "comparison", "in_": "comparison",
    "notin": "comparison",

    # Logic
    "and_": "logic", "or_": "logic", "not_": "logic",
    "uadd": "logic", "usub": "logic",

    # Data structure
    "append": "data_structure", "pop": "data_structure",
    "push": "data_structure", "insert": "data_structure",
    "remove": "data_structure", "extend": "data_structure",
    "sort": "data_structure", "sorted": "data_structure",
    "reverse": "data_structure", "index": "data_structure",
    "slice": "data_structure", "len": "data_structure",
    "get": "data_structure", "keys": "data_structure",
    "values": "data_structure", "items": "data_structure",
    "update": "data_structure", "discard": "data_structure",
    "heappush": "data_structure", "heappop": "data_structure",
    "heapify": "data_structure", "deque": "data_structure",

    # String
    "join": "string", "split": "string", "strip": "string",
    "replace": "string", "find": "string", "startswith": "string",
    "endswith": "string", "lower": "string", "upper": "string",
    "format": "string", "encode": "string", "decode": "string",

    # IO
    "print": "io", "input": "io", "open": "io",
    "read": "io", "write": "io", "close": "io",

    # Control
    "assert": "control", "yield": "control", "yield_from": "control",
    "await": "control", "listcomp": "control", "dictcomp": "control",
    "setcomp": "control", "genexp": "control",

    # Type operations
    "int": "type_ops", "float": "type_ops", "str": "type_ops",
    "list": "type_ops", "dict": "type_ops", "set": "type_ops",
    "tuple": "type_ops", "bool": "type_ops", "type": "type_ops",
    "isinstance": "type_ops", "issubclass": "type_ops",

    # Iteration
    "range": "iteration", "enumerate": "iteration",
    "zip": "iteration", "map": "iteration", "filter": "iteration",
    "iter": "iteration", "next": "iteration", "reversed": "iteration",
}

GROUP_NAMES = sorted(set(OPERATION_GROUPS.values()))


class Test_Signature_Engine:
    def __init__(self, executable_lines, operation_vocabulary,
                 weight_tfidf=None, weight_failure=None,
                 max_vocab_size=None, min_doc_freq=None,
                 min_vocab_for_groups=None):
        """
        Args:
            executable_lines: set of executable line numbers from semantic engine
            operation_vocabulary: list of {"category": str, "name": str} from semantic engine
            weight_tfidf: weight for TF-IDF component
            weight_failure: weight for failure indicators
            max_vocab_size: cap on pruned vocabulary size
            min_doc_freq: minimum document frequency to keep an operation
            min_vocab_for_groups: vocab threshold below which group features are included
        """
        self.executable_lines = set(executable_lines) if executable_lines else set()
        self.max_line = max(self.executable_lines) if self.executable_lines else 1
        self.min_line = min(self.executable_lines) if self.executable_lines else 1
        self.line_range = self.max_line - self.min_line if self.max_line != self.min_line else 1

        # Store raw vocabulary (pruning happens per batch)
        self.raw_vocab = set()
        for entry in (operation_vocabulary or []):
            self.raw_vocab.add(entry["name"])

        # Group index
        self.group_index = {name: i for i, name in enumerate(GROUP_NAMES)}
        self.group_size = len(GROUP_NAMES)

        # Configurable parameters
        self.weight_tfidf = weight_tfidf if weight_tfidf is not None else WEIGHT_TFIDF
        self.weight_failure = weight_failure if weight_failure is not None else WEIGHT_FAILURE
        self.max_vocab_size = max_vocab_size if max_vocab_size is not None else MAX_VOCAB_SIZE
        self.min_doc_freq = min_doc_freq if min_doc_freq is not None else MIN_DOC_FREQ
        self.min_vocab_for_groups = min_vocab_for_groups if min_vocab_for_groups is not None else MIN_VOCAB_FOR_GROUPS

        # Per-batch state (set during compute_batch_signatures)
        self.pruned_vocab_index = {}
        self.pruned_vocab_size = 0
        self.use_groups = False
        self.weight_static = 1.0
        self.doc_count = 0
        self.doc_freq = Counter()

    def compute_batch_signatures(self, tests):
        """
        Compute signatures for a batch of tests.

        Three phases:
            Phase 1 — collect per-test counters + document frequencies
            Phase 2 — prune vocabulary, compute dimensions, set weights
            Phase 3 — compute TF-IDF signatures per test
        """
        # ── Phase 1: collect frequencies ──
        self.doc_count = len(tests)
        self.doc_freq = Counter()
        per_test_counters = []

        for test in tests:
            raw_ops = test.get("called_operations", [])
            counter = self.build_name_counter(raw_ops)
            per_test_counters.append(counter)

            for name in counter:
                self.doc_freq[name] += 1

        # ── Phase 2: prune vocabulary + compute weights ──
        self.prune_vocabulary()
        self.compute_dimensions_and_weights()

        # ── Phase 3: compute signatures ──
        signatures = []
        cumulative_coverage = set()

        for i, test in enumerate(tests):
            sig = self.compute_signature(
                test, per_test_counters[i], cumulative_coverage
            )
            test["test_id"] = sig["test_id"]
            signatures.append(sig)

            covered = test.get("per_test_executed_lines", set())
            cumulative_coverage.update(covered & self.executable_lines)

        return signatures

    def build_name_counter(self, raw_ops):
        """Convert raw called_operations list to name-only frequency counter."""
        counter = Counter()
        for op in raw_ops:
            if isinstance(op, (list, tuple)) and len(op) == 2:
                counter[op[1]] += 1
        return counter

    def prune_vocabulary(self):
        """
        Prune vocabulary:
            1. Drop operations with doc frequency < min_doc_freq
            2. Cap at max_vocab_size by descending doc frequency
        """
        # Filter by minimum document frequency
        candidates = {
            name: freq for name, freq in self.doc_freq.items()
            if freq >= self.min_doc_freq and name in self.raw_vocab
        }

        # Also include operations seen in tests but not in static vocab
        # (runtime-discovered operations)
        for name, freq in self.doc_freq.items():
            if freq >= self.min_doc_freq and name not in candidates:
                candidates[name] = freq

        # Sort by frequency descending, cap at max_vocab_size
        sorted_ops = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        pruned = sorted_ops[:self.max_vocab_size]

        # Build ordered index
        self.pruned_vocab_index = {}
        for i, (name, _) in enumerate(pruned):
            self.pruned_vocab_index[name] = i
        self.pruned_vocab_size = len(self.pruned_vocab_index)

    def compute_dimensions_and_weights(self):
        """
        After pruning, compute:
            - whether to include group features
            - dynamic dimension
            - deterministic static weight = sqrt(dynamic_dim / 2)
        """
        # Conditional group inclusion
        self.use_groups = self.pruned_vocab_size < self.min_vocab_for_groups

        # Dynamic dimension
        dynamic_dim = self.pruned_vocab_size + 3  # tfidf + failure
        if self.use_groups:
            dynamic_dim += self.group_size

        # Static weight: balance 2 static dims against dynamic_dim
        static_dim = 2
        self.weight_static = math.sqrt(dynamic_dim / static_dim)

    def compute_signature(self, test, op_counter, coverage_before):
        """Compute full signature for a single test."""
        test_id = str(uuid.uuid4())

        static = self.compute_static(test)
        dynamic = self.compute_dynamic(test, op_counter)
        score = self.compute_score(test, coverage_before)

        # Apply static weight for balanced clustering
        static_weighted = [v * self.weight_static for v in static]

        cluster_vector = static_weighted + dynamic

        return {
            "test_id": test_id,
            "static": static,
            "dynamic": dynamic,
            "score": score,
            "cluster_vector": cluster_vector,
            "full_vector": cluster_vector + [score]
        }

    def compute_static(self, test):
        """Static: [position_centroid, spread] — 2 floats in [0, 1]."""
        covered = test.get("per_test_executed_lines", set())

        if not covered or not self.executable_lines:
            return [0.0, 0.0]

        relevant = covered & self.executable_lines
        if not relevant:
            return [0.0, 0.0]

        positions = [(line - self.min_line) / self.line_range for line in relevant]
        centroid = sum(positions) / len(positions)
        spread = (max(relevant) - min(relevant)) / self.line_range

        return [centroid, spread]

    def compute_dynamic(self, test, op_counter):
        """
        Dynamic: weighted TF-IDF + failure indicators + conditional groups.
        L2 normalized after weighting.
        """
        tfidf = self.compute_tfidf(op_counter)
        failure = self.compute_failure_indicators(test)

        # Apply component weights
        tfidf_weighted = [v * self.weight_tfidf for v in tfidf]
        failure_weighted = [v * self.weight_failure for v in failure]

        combined = tfidf_weighted + failure_weighted

        # Conditionally include group features
        if self.use_groups:
            groups = self.compute_group_activations(op_counter)
            # No extra alpha needed — groups are only included when vocab
            # is small, so they ADD signal rather than double-count
            combined = combined + groups

        return self.l2_normalize(combined)

    def compute_tfidf(self, op_counter):
        """
        TF-IDF over pruned name-only vocabulary.
        Smoothed IDF: log((N+1)/(df+1)) + 1
        """
        total_ops = sum(op_counter.values()) if op_counter else 1
        vector = [0.0] * self.pruned_vocab_size

        for name, idx in self.pruned_vocab_index.items():
            if name in op_counter:
                tf = op_counter[name] / total_ops
                df = self.doc_freq.get(name, 0)
                idf = math.log((self.doc_count + 1) / (df + 1)) + 1
                vector[idx] = tf * idf

        return vector

    def compute_failure_indicators(self, test):
        """3 floats: [exception, incorrect_output, timeout_or_crash]"""
        status = test.get("execution_status", "")
        verdict = test.get("verdict", "")

        return [
            1.0 if status == "exception" else 0.0,
            1.0 if verdict in ("confirmed_bug", "inconclusive") else 0.0,
            1.0 if status in ("timeout", "crash") else 0.0
        ]

    def compute_group_activations(self, op_counter):
        """
        Aggregate operation frequencies into coarse category groups.
        Only called when pruned vocab < MIN_VOCAB_FOR_GROUPS.
        """
        total_ops = sum(op_counter.values()) if op_counter else 1
        vector = [0.0] * self.group_size

        for name, count in op_counter.items():
            group = OPERATION_GROUPS.get(name)
            if group and group in self.group_index:
                vector[self.group_index[group]] += count / total_ops

        return vector

    def compute_score(self, test, coverage_before):
        """Score: coverage gain + bug confidence. For selection, not clustering."""
        covered = test.get("per_test_executed_lines", set())
        relevant = covered & self.executable_lines if self.executable_lines else set()

        new_lines = relevant - coverage_before
        if self.executable_lines:
            coverage_delta = len(new_lines) / len(self.executable_lines)
        else:
            coverage_delta = 0.0

        confidence = test.get("validation_confidence", 0.0)
        status = test.get("execution_status", "")
        verdict = test.get("verdict", "")

        bug_signal = 0.0
        if status in ("exception", "timeout", "crash"):
            bug_signal = confidence
        elif verdict in ("confirmed_bug", "inconclusive"):
            bug_signal = confidence

        return coverage_delta + bug_signal

    def l2_normalize(self, vector):
        """L2 normalize. Returns zero vector if norm is 0."""
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    def get_cluster_vector_dimension(self):
        """Post-pruning dimension used for clustering."""
        dynamic_dim = self.pruned_vocab_size + 3
        if self.use_groups:
            dynamic_dim += self.group_size
        return 2 + dynamic_dim

    def get_full_vector_dimension(self):
        """Full dimension including score."""
        return self.get_cluster_vector_dimension() + 1