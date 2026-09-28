# Public JSON schema

Each lemma JSON has a compatibility envelope. For inherited V1 lemmas, original V1 top-level fields are preserved. The current Expanded layer is under `expanded_v2`.

`expanded_v2` contains lineage, lexical authority, a per-lemma summary and `current_record`, the frozen Expanded scientific record. The current record carries contextual instances, WSD, PT semantic-unit binding, English alignment, argument-resource status and terminal exceptions. Realized role rows contain HEAD and SPAN plus authority and reason codes.

The website consumes `expanded_v2`; legacy clients may continue reading the preserved V1 fields on inherited lemmas.
