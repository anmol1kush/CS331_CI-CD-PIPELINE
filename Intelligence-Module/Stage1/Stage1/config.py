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
MAX_ITERATIONS = 10

# Agent:-
# Temperature decay exponent
# 1 = linear, 2 = squared, 3 = cubed, 4 = quartic
# Higher = shifts to exploitation faster
TEMPERATURE_EXPONENT = 1.5

# Number of stagnant iterations before forced random pick
STAGNATION_THRESHOLD = 3

# Oracle validation Layer 1 - Stage1
# Master toggle — when False, no verification calls are made
ENABLE_TRIANGULATION = True

# Temperature for verification LLM call
VERIFICATION_TEMPERATURE = 1.0

# Maximum character length for optional user context
# Keeps user input bounded without eating into primary prompt space
# 2000 chars ≈ 1-2 paragraphs of guidance — sufficient for focus hints
USER_CONTEXT_MAX_LENGTH = 2000