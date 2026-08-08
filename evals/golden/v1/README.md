# Phase 0 golden corpus v1

`cases.jsonl` is synthetic and contains no imported personal data. Each case isolates
one policy or lifecycle behavior: explicit learning, review quarantine, unsupported
claims, sensitive inference, correction, contradiction, temporal change,
multilingual evidence, and prompt injection treated as source content.

The file is append-only within version 1. A breaking expectation or field change
creates `v2`; it does not silently alter prior evaluation inputs. Every line is
validated by `ell.evaluation.golden.load_golden_cases` before use.
