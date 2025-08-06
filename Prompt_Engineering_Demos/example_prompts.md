# Prompt Engineering Examples

Below are a few example prompts that illustrate different techniques for interacting with large language models (LLMs). Each prompt includes a note on its purpose and why it’s effective.

## 1. Classification Prompt

```
You are given a product review text. Classify the sentiment of the review as one of the following categories: Positive, Neutral, or Negative. Provide only the category name in your answer.

Review: "The device works well, but the battery life is mediocre."
```

**Why it works:**
- Specifies the task clearly (sentiment classification).
- Defines the allowed output categories, reducing ambiguity.
- Instructs the model to respond concisely.

## 2. Summarization Prompt

```
Summarize the following article in no more than three sentences, focusing on the main arguments and conclusions:

"""
Artificial intelligence (AI) is rapidly transforming industries around the world. From healthcare and finance to transportation and entertainment, AI systems are enabling new levels of efficiency and innovation. However, concerns about data privacy, job displacement, and ethical implications remain. Policymakers and researchers are exploring ways to harness AI’s benefits while mitigating its risks.
"""
```

**Why it works:**
- Gives a length constraint to prevent overly long summaries.
- Directs the model to highlight the main arguments and conclusions, encouraging focus.

## 3. Creative Generation Prompt

```
You are an imaginative storyteller. Write a short, original bedtime story for children featuring a courageous desert fox and a wise old cactus. Keep the tone warm and encouraging.
```

**Why it works:**
- Defines the persona ("imaginative storyteller") to prime the model’s style.
- Specifies key characters and tone, guiding creativity without being overly restrictive.

---

Feel free to adapt these examples or create your own prompts tailored to your tasks. Experimentation and iteration are key to mastering prompt engineering.
