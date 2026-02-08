Perfect — thanks for pasting the concrete version. I see exactly what you want now 👍
You want to **repurpose the rigor and adversarial structure** of this self-review, but:

* the **object under review is a generated *prompt*** (not a solution),
* the **goal is validation**, not repair,
* it’s specifically about prompts designed to **extract deep mathematical structure** (grade → IMO),
* **no fixing, no rewriting**, only judgment and diagnosis.

Below is a **clean, upgraded self-review template** that keeps the spirit of your original, but is correctly aligned to *prompt validation*.

---

## Self-Review (Generated Prompt Validation)

### **Phase 1 — Adversarial Review of the External Critique**

* Treat the critique as a **hypothesis**, not authority.
* Evaluate each critique claim independently:

  * Is the claim **logically necessary** for judging this prompt?
  * Is it **correctly grounded** in the actual wording and intent of the prompt?
  * Does it conflate *prompt quality* with *model behavior* or outcomes?
  * Does it rely on unstated assumptions about difficulty, domain, or solver capability?
* Explicitly label each critique point as:

  * **Valid**
  * **Invalid**
  * **Unsubstantiated**
* Provide a **brief, technical justification** for each label.

---

### **Phase 2 — Prompt-Level Self Validation**

Re-evaluate the generated prompt **from first principles**, ignoring both the critique and your intent as the author.

Assess whether the prompt, *as written*, satisfies the following dimensions:

* **Mathematical Coverage**

  * Does it reliably elicit formal definitions, constraints, and invariants?
  * Does it encourage explicit identification of core mechanisms (e.g. pigeonhole, monotonicity, extremal arguments, algebraic structure)?
* **Difficulty Sensitivity**

  * Is the prompt scalable from grade-level to Olympiad-level problems without collapsing into trivial summaries?
  * Does it preserve rigor at higher difficulty rather than prompting heuristic explanations?
* **Structural Faithfulness**

  * Does the prompt bias toward reproducing *true solution structure* rather than surface-level paraphrase?
  * Does it discourage shortcut reasoning, answer leakage, or narrative-only explanations?
* **Failure-Mode Awareness**

  * Does the prompt naturally expose where solutions rely on hidden assumptions, case gaps, or unjustified steps?
* **Precision & Constraint Clarity**

  * Are the instructions unambiguous, enforceable, and internally consistent?
  * Is the expected depth clearly bounded without over-constraining reasoning?

Only critique points previously marked **Valid** may be considered in this evaluation.

---

### **Conclusion**

End with **exactly one** verdict:

* **Prompt validated**
* **Prompt insufficient**

If **Prompt insufficient**, state **precisely what dimension(s)** fail (e.g. coverage, rigor, faithfulness),
**without proposing fixes, rewrites, or alternatives**.

Keep reasoning **rigorous, minimal, and non-rhetorical**.

---

### External Critique

---

### Why this works (brief meta, not part of the prompt)

* It **cleanly separates** critique validation from prompt validation.
* It evaluates the prompt on **intrinsic properties**, not downstream success.
* It aligns perfectly with **AIMO / Olympiad-grade rigor**, where structure > answers.
* It’s reusable across datasets, domains, and difficulty tiers.
* It enforces *judgment without repair*, which is exactly what you asked for.

If you want next:

* a **shorter “fast audit” version**, or
* a **JSON-scored version** for automated gating, or
* a **pairwise comparison validator** (Prompt A vs Prompt B),

say the word and I’ll shape it.
