# === gpt_cost.py ===

import tiktoken
from openai import OpenAI  # ensure you have openai package installed

# Pricing for GPT-4o-mini
MODEL = "gpt-4o"
COST_INPUT_PER_1K = 0.005
COST_OUTPUT_PER_1K = 0.015

# Global counters
total_input_tokens = 0
total_output_tokens = 0
total_cost = 0.0

# Token estimation
def count_tokens(messages, model=MODEL):
    model = "gpt-4o" if model in ("gpt-4o-mini", "gpt-4o") else model
    encoding = tiktoken.encoding_for_model(model)
    tokens = 0
    for message in messages:
        tokens += len(encoding.encode(message.get("content", "")))
    return tokens

# Reset token + cost counters
def reset_cost_summary():
    global total_input_tokens, total_output_tokens, total_cost
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

# Track usage + cost
def tracked_chat_completion(messages, temperature=0.3, model=MODEL, client=None, **kwargs):
    global total_input_tokens, total_output_tokens, total_cost

    model = "gpt-4o" if model in ("gpt-4o-mini", "gpt-4o") else model

    if client is None:
        client = OpenAI()

    input_tokens = count_tokens(messages, model)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        **kwargs
    )

    output_content = response.choices[0].message.content
    output_tokens = len(tiktoken.encoding_for_model(model).encode(output_content))

    total_input_tokens += input_tokens
    total_output_tokens += output_tokens

    input_cost = (input_tokens / 1000) * COST_INPUT_PER_1K
    output_cost = (output_tokens / 1000) * COST_OUTPUT_PER_1K
    total_cost += input_cost + output_cost

    return response


# Print current usage summary
def print_cost_summary():
    print("\n----- GPT-4o Token Usage Summary -----")
    print(f"Total Input Tokens: {total_input_tokens}")
    print(f"Total Output Tokens: {total_output_tokens}")
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    print("-------------------------------------")
