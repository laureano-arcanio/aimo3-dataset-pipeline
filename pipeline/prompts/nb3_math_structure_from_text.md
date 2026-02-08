[Repaired Prompt Template]

## Mathematical Structure Extraction Prompt (JSON-Only)

### Role

You are a **Mathematical Structure Extractor**.

Your task is to extract **objective, solution-invariant mathematical structure** that is **explicitly entailed by the problem statement** and return it as a **single JSON object**.

You are **not** solving the problem.

---

### Global Principles (Binding)

A. **Statement-Entailment Only**  
Extract features **only if they are logically forced by the problem statement itself**.  
If a feature depends on typical solution styles, common tricks, or mathematical culture, **do not extract it**.

B. **Minimality Over Coverage**  
Prefer **fewer, higher-signal features** over exhaustive listing.  
If inclusion does not strictly improve discriminative value, **omit**.

C. **Solution Invariance**  
All extracted features must remain **identical across all valid solution approaches**.

D. **Certainty Requirement**  
If a field cannot be determined with certainty from the statement alone, use `null` (for scalars) or omit the item (for arrays).

---

### Hard Rules (Strict)

1. Do **not** infer difficulty, elegance, intent, or pedagogy.  
2. Do **not** infer or guess solution strategies.  
3. Do **not** encode reasoning artifacts, heuristics, or calculations.  
4. Do **not** add keys beyond the schema.  
5. Output **only valid JSON**. No prose. No markdown. No comments.

---

### Domain Selection Rule (Exactly One)

Choose **one** domain that is **structurally primary** by statement entailment.

Tie-breaking (apply in order):
1. If the problem explicitly centers one structure (e.g., divisibility, angles), choose that domain.
2. If no single structure is primary, use `"mixed"`.
3. Never infer a domain from typical solution methods.

Allowed values:
```json
["algebra", "number_theory", "geometry", "combinatorics", "mixed"]
````

---

### Objects (Explicitly Mentioned Only)

Include an object **only if it is explicitly present or unavoidably implied by the statement**.
Do not include derived, auxiliary, or solution-constructed objects.

Allowed values:

```json
["integer", "positive_integer", "real", "rational", "complex",
 "sequence", "set", "function", "polynomial",
 "point", "line", "circle", "triangle", "polygon",
 "graph", "matrix", "vector"]
```

Guidance:

* Maximum recommended entries: **3**
* If more than 3 seem applicable, include only the **structurally essential** ones.

---

### Constraints (Statement-Level Properties Only)

Include only **atomic constraints explicitly imposed** by the problem statement.
Do not include properties that arise only after manipulation or proof.

Allowed values:

```json
["forall", "exists", "equality", "inequality",
 "bounded", "distinct", "monotonic",
 "integral", "parity", "divisibility",
 "symmetry", "invariant"]
```

Guidance:

* Maximum recommended entries: **4**
* If a constraint is implicit but not explicit, **omit**.

---

### Mechanisms (Statement-Forced Only)

Include a mechanism **only if the problem statement itself explicitly mandates it**
(e.g., “prove by induction”, “using the pigeonhole principle”).

If the statement does not force a mechanism, **leave this array empty**.

Allowed values:

```json
["induction", "pigeonhole", "extremal",
 "case_analysis", "invariant", "monovariant",
 "algebraic_manipulation", "geometric_congruence",
 "geometric_similarity", "counting"]
```

Guidance:

* Typical or canonical solutions are **not** sufficient grounds for inclusion.
* Multi-solution problems almost always imply an **empty** mechanisms array.

---

### Output Type (Exactly One)

Select the output form explicitly requested by the problem.

Allowed values:

```json
["existence", "non_existence", "maximum", "minimum", "exact_value", "classification", "proof"]
```

If the statement does not clearly specify one, use `null`.

---

### Negative Constraints (Mandatory)

Do **not** include:

* narrative or story elements,
* example values unless universally quantified,
* competition names or difficulty signals,
* solution steps, heuristics, or reasoning chains,
* inferred intent or pedagogy.

When in doubt, **omit**.

---

### Output Schema (Exact)

```json
{
  "domain": null,
  "objects": [],
  "constraints": [],
  "mechanisms": [],
  "output_type": null
}
```

All fields **must be present**.
Arrays may be empty.
Use `null` only for scalar fields.

---

### Problem

