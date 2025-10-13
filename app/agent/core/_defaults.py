""" app/agent/core/_defaults.py """

import ollama

DEFAULT_OPTIONS = ollama.Options(
    num_ctx=1024,         # shorter context → less overhead
    temperature=0.3,      # still stable, but a touch livelier
    top_p=0.9,            # good nucleus sampling
    top_k=40,             # typical safe default
    repeat_penalty=1.05,  # lighter repetition check → less compute
    num_predict=128,      # cap on tokens (speeds up response)
    num_thread=2,         # match physical CPU cores (adjust to your machine)
    num_gpu=1,            # offload to GPU if you have one
    low_vram=True,       # only True if you’re memory-starved
    f16_kv=True,          # faster key/value cache
    use_mmap=True,        # mmap the model for faster loading
    use_mlock=False,      # set True if you want to lock into RAM
    seed=None             # nondeterministic, so cache doesn’t collide
)

CHAT_CONFIG = dict(
    stream=False,
    # think='low',
    options=DEFAULT_OPTIONS.model_dump(), # type: ignore
    keep_alive='15m',
    # tools = FUNCTION CALLABLES
)
