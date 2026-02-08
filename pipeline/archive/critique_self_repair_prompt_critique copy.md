Instructional Self-Repair Mode

You have already **validated a critique of the prompt** and explicitly identified which critique points are **accepted**.

Your task now is **only to repair the prompt itself**, using **only the accepted critique points** as binding constraints.

You are **not** re-auditing, debating, or extending the critique.

---

### Core Repair Rules

* Rewrite the prompt **from scratch** with all accepted critique points fully integrated.
* **Do not** revisit, reinterpret, or weaken any accepted critique point.
* **Do not** locally patch or minimally edit the original prompt.

  * If a section is flawed, replace it entirely.
* Preserve the **original intent and scope** of the prompt unless an accepted critique explicitly requires narrowing or expansion.
* Ensure the repaired prompt is:

  * internally consistent,
  * instructionally unambiguous,
  * robust under edge cases and adversarial inputs.
* If the original prompt contained:

  * schemas, enumerations, or output formats
    → they must be reintroduced **cleanly and consistently**, or explicitly removed if required by the critique.

---

### Repair Constraints

* All accepted critique points are **authoritative**.
* Any design choice not constrained by the accepted critique:

  * may be retained,
  * but must not reintroduce a rejected failure mode.
* If a feature or instruction cannot be repaired without ambiguity, **remove it** rather than weaken constraints.

---

### Required Repair Coverage

Your repaired prompt must explicitly address all accepted critique points, including (if applicable):

* Extraction pressure or over-enumeration risks
* Taxonomic instability or label ambiguity
* Reasoning or solution-path contamination
* Missing negative constraints or leakage channels
* Ambiguous incentives or underspecified defaults

If the prompt makes **structural claims** (e.g. “solution-invariant”, “stable across runs”, “JSON-only”), the repaired version must **enforce** them instructionally, not merely assert them.

---

### Output Requirements

* Output **only** the repaired prompt.
* No commentary, no explanations, no critique restatement.
* The result must be a **standalone, ready-to-use prompt**.
* Maintain the original prompt’s language unless an accepted critique requires change.

---

### Output Format

```
[Repaired Prompt Template]
```

Nothing else.

