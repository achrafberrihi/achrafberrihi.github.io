# Speech, Audio & ASR

Prompts for transcription quality, speech data and spoken-language tasks.

## 1. ASR error analysis

```text
Compare the ASR hypothesis with the reference transcript.

Reference:  "{reference}"
Hypothesis: "{hypothesis}"

List each error as JSON: {"type": "substitution|deletion|insertion|named_entity|number_format|code_switch",
"reference": "...", "hypothesis": "...", "severity": "minor|major"}.
Ignore casing and punctuation. Return {"errors": [...], "meaning_preserved": true|false}.
```

> **Why it works:** an error taxonomy turns "bad transcript" into trackable categories across model versions.

## 2. Transcript normalizer

```text
Normalize this raw transcript according to the style guide:
- Numbers: spell out 0–9, digits from 10 ("three", "25").
- Remove fillers (uh, um, euh) but keep repetitions that change meaning.
- Mark unclear audio as [inaudible] and overlapping speech as [crosstalk].
- Keep code-switching as spoken: do not translate Darija or French words.

Raw transcript: """{transcript}"""
Return only the normalized transcript.
```

> **Why it works:** explicit rules for numbers, fillers and code-switching are where annotators disagree most.

## 3. Speaker diarization reviewer

```text
This transcript has speaker labels produced automatically:
"""{diarized_transcript}"""

Find likely diarization errors: turns attributed to the wrong speaker, one speaker split
into two labels, or two speakers merged. Use cues like questions/answers, names and
self-references. Return a list of {line, issue, suggested_speaker, confidence}.
```

> **Why it works:** conversational cues (who asks, who answers) are strong signals for speaker attribution.

## 4. Dialect and code-switching tagger

```text
Tag each segment of this Maghrebi speech transcript with its language:
MSA (Modern Standard Arabic), DARIJA, FR (French), EN, or MIXED.

Transcript: """{transcript}"""

Return JSON lines: {"segment": "...", "language": "...", "notes": "<loanwords or spelling variants>"}.
Do not correct or translate the text.
```

> **Why it works:** segment-level tags let you measure ASR quality per language, where Darija usually lags.

## 5. Call summary for support teams

```text
Summarize this customer-support call transcript for the CRM.

Transcript: """{transcript}"""

Return:
- Reason for call (1 line)
- Customer sentiment at start and end
- Actions taken by the agent
- Open issues and promised follow-ups with dates
- Compliance flags (e.g. agent didn't verify identity) — "none" if none
Max 120 words.
```

> **Why it works:** a fixed structure makes summaries comparable and searchable across thousands of calls.
