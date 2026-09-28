# Compatibility with canonical NounBank.DS

NounBank.DS Expanded is an expansion of the canonical [NounBank.DS](https://github.com/bryankhelven/NounBank.DS), not a disconnected replacement.

The published V1 baseline contains 145 lexical predicates and 1,756 examples. In Expanded, the 145 inherited public JSON payloads preserve every original top-level V1 field/value, and a new `expanded_v2` namespace adds current lineage, contextual S/N, WSD, English alignment, licensed-role and argument authority. Another 564 lexical predicates are added.

The productization build produces `docs/V1_COMPATIBILITY_REPORT.json`, which must pass 145/145 structural no-loss checks before the product branch is eligible for merge.
