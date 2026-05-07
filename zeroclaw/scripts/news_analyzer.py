#!/usr/bin/env python3
import argparse
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER = "Jessliang/rachel-finetuned"

print("Loading model...", file=sys.stderr)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    dtype=torch.float16,
    device_map={"": "mps"}
)
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
print("Model ready.", file=sys.stderr)

def analyze(text):
    messages = [
        {
            "role": "system",
            "content": "Summarize the following financial news article in 1-2 sentences. Then classify the sentiment as Positive, Neutral, or Negative."
        },
        {"role": "user", "content": text}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("mps")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=False)
    result = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    sentiment = "Neutral"
    result_lower = result.lower()
    if "sentiment: positive" in result_lower or "sentiment is positive" in result_lower:
        sentiment = "Positive"
    elif "sentiment: negative" in result_lower or "sentiment is negative" in result_lower:
        sentiment = "Negative"

    return result.strip(), sentiment

parser = argparse.ArgumentParser()
parser.add_argument("--news", nargs="+", required=True)
parser.add_argument("--titles", nargs="+", default=None)
args = parser.parse_args()

scores = {"Positive": 1, "Neutral": 0, "Negative": -1}
total = 0

for i, text in enumerate(args.news, 1):
    title = args.titles[i-1] if args.titles and i-1 < len(args.titles) else f"Article {i}"
    summary, sentiment = analyze(text)
    score = scores[sentiment]
    total += score
    print(f"\n[{i}] {title}")
    print(f"Summary: {summary}")
    print(f"Sentiment: {sentiment} ({'+' if score > 0 else ''}{score})")

print(f"\n{'='*40}")
print(f"Total Sentiment Score: {total}/{len(args.news)}")
if total > 0:
    print("Overall: BULLISH")
elif total < 0:
    print("Overall: BEARISH")
else:
    print("Overall: NEUTRAL")
