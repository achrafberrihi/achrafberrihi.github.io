# Localization & Translation (French · Arabic · Darija · English)

Prompts for multilingual content and localization QA.

## 1. Context-aware translator

```text
Translate the text from {source_lang} to {target_lang}.

Context: {where_it_appears} (e.g. mobile app button, legal notice, marketing email)
Audience: {audience}
Register: {formal|neutral|casual}
Glossary (must use): {glossary}

Keep placeholders like {name} and HTML tags unchanged. Respect length limits: {max_chars}.
Return only the translation.
```

> **Why it works:** context, register and a glossary fix most translation inconsistencies.

## 2. Translation quality review (MQM-style)

```text
Review this translation.

Source ({source_lang}): """{source}"""
Translation ({target_lang}): """{translation}"""

List errors with category (accuracy, omission, addition, terminology, grammar, style,
locale convention), severity (minor/major/critical) and a corrected version.
End with a score: 100 − (1×minor + 5×major + 10×critical).
```

> **Why it works:** a standard error typology makes translation quality measurable.

## 3. Darija ↔ French/English conversion

```text
Convert this Moroccan Darija text into natural {target_lang}:
"""{darija_text}"""

The text may be written in Arabic script or Latin script with numbers (3 = ع, 7 = ح, 9 = ق).
Give: the translation, a literal gloss for idioms, and note any word with several possible meanings.
```

> **Why it works:** handling Arabizi and flagging ambiguity reflects how Darija is actually written online.

## 4. Marketing transcreation

```text
Adapt this marketing message for the {target_market} market in {target_lang}:
"""{message}"""

Don't translate literally: keep the intent and emotion, adapt idioms, cultural references,
humor, units, dates and currency. Give 2 versions (bold and conservative) and explain the main adaptations.
```

> **Why it works:** transcreation preserves impact where literal translation falls flat.

## 5. Localization QA for software strings

```text
Check these UI strings localized into {target_lang}:
{strings_json}  (key, source, translation, max_length)

Flag: broken placeholders, length overflows, untranslated text, inconsistent terminology
across keys, wrong number/date formats, and right-to-left issues for Arabic.
Return JSON: [{"key": "...", "issue": "...", "fix": "..."}]
```

> **Why it works:** catches the technical localization bugs that break interfaces.
