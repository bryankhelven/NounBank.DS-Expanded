# Argument annotation methodology

## Scope and authority

This document describes how `ARGUMENT_RESOURCE_001` produced the frozen argument layer of **NounBank.DS Expanded**. It is repository documentation and is deliberately not part of the public GitHub Pages navigation.

The regular argument universe contains **3,524 predicate instances** and **14,984 predicate-instance × licensed-role slots**. Final statuses are **2,669 YES**, **11,015 NO**, and **1,300 ABSTAIN**. Every YES has a frozen `HEAD` and `SPAN`.

The protocol never equates a dependency relation with argumenthood, never promotes a candidate merely because it is syntactically local, and never transfers a verbal or English role automatically into Portuguese context.

## Four lineage lanes

### V1 reuse: 1,747 instances / 8,721 role slots

Published NounBank.DS V1 argument gold was reused without semantic reannotation. Roles and argumenthood remained unchanged. Ninety-six legacy realized spans needed technical reanchoring against the current DANTEStocks tokenization, mainly because of typos, financial abbreviations, contractions or truncated tweet forms. A further 104 realized rows had a frozen V1 span but no historical HEAD; HEAD was derived strictly inside the preserved V1 span from the current UD tree. Argumenthood, role and span were not changed.

### V1 identity-repaired: 9 instances / 45 role slots

Published role decisions were retained after targeted predicate-identity repair. Only structural compatibility and anchoring were checked.

### New contexts of inherited V1 predicates: 38 instances / 190 role slots

These are new S occurrences of the 145 inherited predicates. They were not assigned roles by English gloss transfer. Contextual decisions were made using the realization conventions actually attested in the published V1 roleset plus the current sentence and UD structure.

Final status: 33 YES, 148 NO, 9 ABSTAIN.

### New 564 predicates: 1,730 instances / 6,028 role slots

For each exact/aligned PT semantic unit, the licensed English NomBank role inventory had already been frozen by ROLEINV001. Each licensed role was then judged independently in Portuguese context.

A structural candidate generator produced small, inspectable candidate sets from the DANTEStocks UD tree. Candidate evidence included dependency path from predicate to candidate head, locality, dependency relation, case marker/preposition, span length and cues such as numeric/money/percentage, ticker/entity, temporal, location and clause information. **Candidate membership was never sufficient for YES.**

## Semantic role classes and structural evidence

Canonical NomBank role descriptions were operationalized into coarse semantic classes such as AGENT, THEME, AMOUNT, SOURCE, GOAL, INSTRUMENT, COUNTERPART, BENEFICIARY, ACTION, CAUSE, PURPOSE, LOCATION, TIME, TOPIC, ATTRIBUTE and MANNER.

Examples of evidence used include: local `nsubj/csubj` or clear `por` agents for AGENT; semantically compatible local objects/subjects or direct `de/sobre` complements for THEME; numeric/money/percentage expressions for AMOUNT; `de/desde` and `a/até/para` for compatible SOURCE/GOAL roles; `com/contra` for compatible COUNTERPART roles; explicit `por/devido` and `para` for CAUSE/PURPOSE; and dedicated temporal, locative or clausal cues for TIME, LOCATION and ACTION.

Unknown or insufficiently specified role semantics were not guessed; they were routed to ABSTAIN.

## Roleset-specific protections

High-frequency ambiguous frames received additional guards. Examples include change frames (`rise.01`, `decline.01`, `increase.01`, `reduction.01` and related rolesets), `tracking.01`, `profit.01`, `transaction.01`, analysis/examination/investigation frames, `loss.01`, `production.01`, `signal.01` and `closure.01`. Temporal material was not promoted to a change theme merely because it was structurally close; abstract genitives were not automatically treated as agents; transaction-type phrases were not automatically treated as transacted assets; and percentages or monetary values were assigned only where the licensed role semantics supported them.

## Decision routing and conservative abstention

Structural-semantic proposals were scored only to route adjudication. Diagnostic support at approximately **5.2 or above**, together with explicit semantic compatibility, could license YES. Strong but non-diagnostic evidence (approximately **4.5 or above**) was ABSTAIN. No compatible evidence (below approximately **1.8**) was NO. Intermediate or ambiguous cases were ABSTAIN.

Near-tied candidates were handled conservatively. A candidate span/head that appeared to realize two distinct roles triggered a cross-role conflict check; only the better-supported role could remain YES, with the competing role routed to ABSTAIN. These thresholds are operational routing devices, not linguistic universals.

## Final reason codes for the 1,730-new lane

| Reason | Count |
|---|---:|
| `NO_LICENSED_EXPLICIT_REALIZATION_FOUND` | 3,949 |
| `EXPLICIT_SEMANTIC_AND_STRUCTURAL_LICENSING` | 762 |
| `WEAK_OR_AMBIGUOUS_CONTEXTUAL_REALIZATION` | 730 |
| `PLAUSIBLE_BUT_NOT_DIAGNOSTICALLY_UNIQUE` | 513 |
| `ROLE_SEMANTICS_NOT_SUFFICIENTLY_SPECIFIED` | 32 |
| `NO_STRUCTURAL_CANDIDATE` | 26 |
| `CROSS_ROLE_SPAN_CONFLICT` | 12 |
| `TEMPORAL_NMOD_NOT_SAFE_AS_CHANGE_THEME` | 3 |
| `TRANSACTION_TYPE_NOT_SAFE_AS_THING_TRANSACTED` | 1 |

The inherited-new lane has explicit contextual reason codes for cases such as truncated proposal content, unrecoverable proposer, ambiguous proposal recipient, monitoring target not explicit in a construction and endpoint-value entanglement.

## HEAD and SPAN

`SPAN` is the overt textual realization assigned to a role. `HEAD` is the UD head used as its structural anchor. They are separate fields. For new YES decisions, both were frozen together. For V1 reuse, the published span was preserved; HEAD was reused where present or derived inside that span where historically absent.

## Provenance per row

Every frozen role-slot row exposes lineage lane, token-instance identity, PT semantic-unit identity, accepted English NomBank roleset, licensed role and description, YES/NO/ABSTAIN, adjudication reason, authority, HEAD, SPAN and sentence text. Thus the 14,984 decisions are auditable without treating hidden model reasoning as scientific evidence.

## Annotation character and limitation

The delta annotation was **model-assisted and rule-constrained**, with explicit conservative abstention. It must not be described as unaided human annotation. Published V1 gold is direct reuse; the delta layer is a newly adjudicated resource layer with auditable rules and provenance.
