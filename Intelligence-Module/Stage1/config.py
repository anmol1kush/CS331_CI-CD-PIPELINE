"""
Stage-1 Configuration

Central configuration for all Stage-1 modules.
All configurable values are defined here to avoid
hardcoded magic numbers across the codebase.
"""


# Tests Executor:-
# Timeout for user code execution (seconds)
# How long a child process gets to run user-submitted code
TEST_TIMEOUT = 10

# Timeout for reading result from dead child process (seconds)
# Only waits for OS to flush queue data — child is already dead by this point
QUEUE_DRAIN_TIMEOUT = 1


# LLM Provider:-
# Gemini model identifier
GEMINI_MODEL = "gemini-2.5-flash"
#GEMINI_MODEL = "gemini-3-flash-preview"

# Max retry attempts for transient API failures (429, 503)
LLM_MAX_RETRIES = 3

# Base delay for exponential backoff (seconds)
# Actual delay: LLM_RETRY_DELAY ** (attempt + 1)
# Attempt 1: 2s, Attempt 2: 4s, Attempt 3: 8s
LLM_RETRY_DELAY = 2

# Token limit for LLM responses
# Not set for current increment — test objects are small
# Add max_output_tokens when optimizing costs at pipeline deployment stage
# GEMINI_MAX_OUTPUT_TOKENS = 1000


# LLM Tests Generator
# Maximum number of test cases per LLM call
MAX_TESTS_PER_CALL = 3


# Agent Loop (Environment)
# Maximum iterations for the agent loop
MAX_ITERATIONS = 2

# Agent:-

# ── Contextual TS-UCB Bandit ──
# UCB exploration constant (higher = more exploration)
UCB_CONSTANT = 1.0

# Sliding window size for FRRMAB-style reward decay
# Controls how many recent observations shape the posterior
SLIDING_WINDOW_SIZE = 8

# Beta prior parameters (uniform prior = 1, 1)
PRIOR_ALPHA = 1
PRIOR_BETA = 1

# Contextual bonus weights per strategy
# Higher = stronger bias toward that strategy when structural features match
CONTEXT_WEIGHT_BRANCH = 0.15
CONTEXT_WEIGHT_EDGE = 0.15
CONTEXT_WEIGHT_ADVERSARIAL = 0.15
# Temperature decay exponent
# 1 = linear, 2 = squared, 3 = cubed, 4 = quartic
# Higher = shifts to exploitation faster
TEMPERATURE_EXPONENT = 1.5

# Number of stagnant iterations before forced random pick
STAGNATION_THRESHOLD = 5

# Oracle validation Layer 1 - Stage1
# Master toggle — when False, no verification calls are made
ENABLE_TRIANGULATION = True

# Temperature for verification LLM call
VERIFICATION_TEMPERATURE = 1.0

# Maximum character length for optional user context
# Keeps user input bounded without eating into primary prompt space
# 2000 chars ≈ 1-2 paragraphs of guidance — sufficient for focus hints
USER_CONTEXT_MAX_LENGTH = 2000

# ──────────────────────────────────────────────
# Runtime Override Support
# ──────────────────────────────────────────────
# These values can be overridden by cost_modes via Orchestrator.
# Call apply_mode_overrides() before pipeline starts.

# ── Test Signature ──
# Maximum vocabulary size after pruning (top-K by doc frequency)
MAX_VOCAB_SIZE = 25

# Minimum document frequency to retain an operation in vocabulary
MIN_DOC_FREQ = 2

# Component weights for signature vector
WEIGHT_TFIDF = 1.0
WEIGHT_FAILURE = 2.0

# Pruned vocab threshold below which group features are included
MIN_VOCAB_FOR_GROUPS = 15

# ── Test Clustering ──
# Hard upper bound on cluster count (None = no cap, uses sqrt(n) only)
MAX_CLUSTER_CAP = None

def apply_mode_overrides(mode_config):
    """
    Overrides Stage 1 config values with mode-specific values.

    Args:
        mode_config: dict from cost_modes.get_mode()
                     Keys: max_iterations, max_tests_per_call, gemini_model
    """
    global MAX_ITERATIONS, MAX_TESTS_PER_CALL, GEMINI_MODEL

    if mode_config.get("max_iterations") is not None:
        MAX_ITERATIONS = mode_config["max_iterations"]

    if mode_config.get("max_tests_per_call") is not None:
        MAX_TESTS_PER_CALL = mode_config["max_tests_per_call"]

    if mode_config.get("gemini_model") is not None:
        GEMINI_MODEL = mode_config["gemini_model"]

    if mode_config.get("ucb_constant") is not None:
        UCB_CONSTANT = mode_config["ucb_constant"]

    if mode_config.get("sliding_window_size") is not None:
        SLIDING_WINDOW_SIZE = mode_config["sliding_window_size"]