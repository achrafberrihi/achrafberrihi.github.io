# Software Engineering & Code

Prompts for writing, reviewing, testing and documenting code.

## 1. Code review

```text
Review this {language} code as a senior engineer.

{code}

Report, in order of severity: bugs, security issues, performance problems, then
readability. For each: the line, the problem, why it matters, and a fixed snippet.
Skip style nitpicks a linter would catch. If the code is fine, say so.
```

> **Why it works:** severity ordering puts real bugs first; "say so if fine" avoids invented issues.

## 2. Unit test generator

```text
Write {framework} unit tests for this function:

{code}

Cover: normal cases, edge cases (empty, zero, very large, unicode), invalid input,
and one test per branch. Use descriptive test names. Do not mock what you can call directly.
```

> **Why it works:** an explicit edge-case checklist produces tests that actually catch bugs.

## 3. Bug diagnosis

```text
I get this error:
{error_and_stack_trace}

Relevant code:
{code}

What I expected: {expected}
What happens: {actual}

Give the most likely root cause first, then 2 alternatives. For each, a quick way to
confirm it and the fix.
```

> **Why it works:** ranked hypotheses with confirmation steps mirror how good engineers debug.

## 4. Refactoring plan

```text
Refactor this code to improve maintainability without changing behavior:

{code}

First list the problems (duplication, long functions, unclear names, tight coupling).
Then give the refactored code. Finally, list what tests should exist before merging.
```

> **Why it works:** "without changing behavior" plus a test list keeps the refactor safe.

## 5. README writer

```text
Write a README for this project.

Project files: {file_tree}
Main code: {key_files}

Sections: one-line description, features, quick start (copy-paste commands), configuration,
usage examples, project structure, and limitations. Only describe what the code actually does.
```

> **Why it works:** grounding in the files avoids documenting features that don't exist.
