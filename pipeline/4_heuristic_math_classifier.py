"""
Heuristic Math Classifier Module

This module provides heuristic-based classification for math problems:
- Domain classification (algebra, number_theory, combinatorics, geometry)
- from_text extraction: objects, constraints, output_type
- from_solution extraction: reasoning_shape, case_split,
  auxiliary_construction, reasoning_depth_proxy, intermediate_reuse_proxy

Usage:
    from heuristic_math_classifier import extract_all_heuristic

    # Full heuristic extraction (domain + from_text + from_solution)
    result = extract_all_heuristic(payload)
    ms = result["math_structure"]
    # ms["domain"], ms["from_text_heuristic"], ms["from_solution_heuristic"]

    # Or individual extractors
    from heuristic_math_classifier import extract_fields
    fields = extract_fields(payload)

    from heuristic_math_classifier import extract_from_text_heuristic
    text_props = extract_from_text_heuristic(fields)
    # {"objects": [...], "constraints": [...], "output_type": "..."}

    from heuristic_math_classifier import extract_from_solution_heuristic
    sol_props = extract_from_solution_heuristic(fields)
    # {"reasoning_shape": "...", "case_split": "...", ...}
"""

import re
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field, asdict


# ============================================================================
# CONFIGURATION
# ============================================================================

# Allowed domains (final output must be one of these)
ALLOWED_DOMAINS = {"algebra", "number_theory", "combinatorics", "geometry"}

# Default heuristic threshold (single threshold for Option A)
DEFAULT_H_THRESHOLD = 6


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

@dataclass
class DomainPatterns:
    """Pattern definitions for a single domain."""
    # Hard override patterns (force this domain if matched)
    hard_override_patterns: List[str] = field(default_factory=list)
    hard_override_min_matches: int = 1  # For geometry: need 2 matches

    # Scoring patterns: (pattern_list, score, target_fields)
    # target_fields: 'code', 'text', 'all'
    scoring_rules: List[Tuple[List[str], int, str]] = field(default_factory=list)

    # Negative patterns (reduce score if other domain signals present)
    penalty_conditions: List[str] = field(default_factory=list)
    penalty_score: int = -4


# -----------------------------------------------------------------------------
# NUMBER THEORY PATTERNS
# -----------------------------------------------------------------------------
NT_HARD_OVERRIDE = [
    r"≡",
    r"\bmod\b",
    r"\bgcd\b",
    r"\blcm\b",
    r"\bisprime\b",
    r"\bfactorint\b",
    r"\bmod_inverse\b",
    r"\bcrt\b",
    r"\bvaluation\b",
    r"\bv_p\b",
    r"pow\s*\([^,]+,[^,]+,[^)]+\)",  # pow(a,b,mod) pattern
]

NT_CODE_PATTERNS = [
    r"\bgcd\b", r"\bigcd\b", r"\bisprime\b", r"\bfactorint\b",
    r"\bprimerange\b", r"\bmod_inverse\b", r"\bcrt\b",
    r"\bvaluation\b", r"\bv_p\b",
    r"pow\s*\([^,]+,[^,]+,[^)]+\)",
]

NT_TEXT_PATTERNS = [
    r"≡", r"\bmod\b", r"\bremainder\b", r"\bdivides\b",
    r"\bgcd\b", r"\blcm\b", r"\bprime\b", r"\bcomposite\b",
]

NT_TEXT_SECONDARY = [
    r"\bdiophantine\b",
    r"highest\s+power\s+of\s+p\s+dividing",
]

NT_PLAN_PATTERNS = [
    r"work\s+modulo", r"prime\s+factorization", r"divisibility",
]

NUMBER_THEORY_PATTERNS = DomainPatterns(
    hard_override_patterns=NT_HARD_OVERRIDE,
    hard_override_min_matches=1,
    scoring_rules=[
        (NT_CODE_PATTERNS, 6, 'code'),
        (NT_TEXT_PATTERNS, 5, 'text'),
        (NT_TEXT_SECONDARY, 3, 'text'),
        (NT_PLAN_PATTERNS, 4, 'text'),
    ],
    penalty_conditions=['combinatorial_enumeration'],
    penalty_score=-4,
)


# -----------------------------------------------------------------------------
# ALGEBRA PATTERNS
# -----------------------------------------------------------------------------
ALG_HARD_OVERRIDE = [
    r"\bMatrix\b", r"\bdet\b", r"\btrace\b", r"\brank\b", r"\beigen\b",
    r"\bPoly\b", r"\bgroebner\b", r"\bsolve\b", r"\blinsolve\b",
]

ALG_CODE_PATTERNS = [
    r"\bsolve\b", r"\blinsolve\b", r"\bPoly\b", r"\bgroebner\b",
    r"\bMatrix\b", r"\bdet\b", r"\btrace\b", r"\brank\b", r"\beigen\b",
]

ALG_TEXT_PATTERNS = [
    r"\bpolynomial\b", r"\broots\b", r"\bdegree\b", r"\bcoefficients?\b",
    r"functional\s+equation", r"system\s+of\s+equations",
    r"\bmatrix\b", r"\bdeterminant\b", r"\btrace\b",
    r"vector\s+space", r"linear\s+transformation",
]

ALG_TEXT_SECONDARY = [
    r"\bAM-GM\b", r"\bCauchy\b", r"\bJensen\b", r"\bSchur\b",
    r"\binequality\b", r"\binequalities\b",
]

ALG_PLAN_PATTERNS = [
    r"solve\s+for", r"find\s+all\s+functions",
    r"analyze\s+roots", r"analyze\s+coefficients",
]

ALGEBRA_PATTERNS = DomainPatterns(
    hard_override_patterns=ALG_HARD_OVERRIDE,
    hard_override_min_matches=1,
    scoring_rules=[
        (ALG_CODE_PATTERNS, 6, 'code'),
        (ALG_TEXT_PATTERNS, 5, 'text'),
        (ALG_TEXT_SECONDARY, 3, 'text'),
        (ALG_PLAN_PATTERNS, 4, 'text'),
    ],
    penalty_conditions=['strong_nt'],
    penalty_score=-4,
)


# -----------------------------------------------------------------------------
# GEOMETRY PATTERNS
# -----------------------------------------------------------------------------
GEOM_HARD_OVERRIDE = [
    r"\btriangle\b", r"\bcircle\b", r"\bangle\b", r"\bperpendicular\b",
    r"\bparallel\b", r"\btangent\b", r"\bchord\b", r"\barc\b",
    r"\bcircumcircle\b", r"\bincircle\b", r"\bmidpoint\b",
    r"\bbisector\b", r"\borthocenter\b", r"\bincenter\b",
    r"\bcircumcenter\b",
    r"∠", r"°", r"Ω", r"ω",
]

GEOM_TEXT_PATTERNS = [
    r"\btriangle\b", r"\bcircle\b", r"\bangle\b", r"\bperpendicular\b",
    r"\bparallel\b", r"\btangent\b", r"\bchord\b", r"\barc\b",
    r"\bcircumcircle\b", r"\bincircle\b", r"\bmidpoint\b",
    r"\bbisector\b", r"\borthocenter\b", r"\bincenter\b",
    r"\bcircumcenter\b",
    r"∠", r"°", r"Ω", r"ω",
]

GEOM_PLAN_PATTERNS = [
    r"let\s+points?\s+[A-Z]", r"\bintersection\b", r"\bconstruct\b",
    r"\breflection\b", r"\bhomothety\b",
]

GEOM_CODE_PATTERNS = [
    r"sympy\.geometry", r"\bPoint\b", r"\bLine\b", r"\bCircle\b",
]

GEOMETRY_PATTERNS = DomainPatterns(
    hard_override_patterns=GEOM_HARD_OVERRIDE,
    hard_override_min_matches=2,  # Need at least 2 strong geometry objects
    scoring_rules=[
        (GEOM_TEXT_PATTERNS, 6, 'text'),
        (GEOM_PLAN_PATTERNS, 4, 'text'),
        (GEOM_CODE_PATTERNS, 6, 'code'),
    ],
    penalty_conditions=['strong_nt'],
    penalty_score=-4,
)


# -----------------------------------------------------------------------------
# COMBINATORICS PATTERNS
# -----------------------------------------------------------------------------
COMB_CODE_ITERTOOLS = [
    r"itertools\.combinations", r"itertools\.permutations", r"itertools\.product",
]

COMB_CODE_ENUMERATION = [
    r"subset", r"bitmask", r"1\s*<<", r"bin\(",
]

COMB_CODE_STRING = [
    r"'\d+'|\"\\d+\"",  # String digit construction
    r"\.issubset\b", r"\bin\s+str\(",
]

COMB_TEXT_PATTERNS = [
    r"how\s+many", r"number\s+of\s+ways", r"\barrangements?\b",
    r"\bpermutation\b", r"\bcombination\b", r"\bchoose\b",
    r"\bcount\b", r"exactly\s+k\s+of", r"\bsubstring\b",
    r"\bforbidden\b", r"\bavoid\b", r"\bgraph\b",
    r"\bmatching\b", r"\bcoloring\b", r"\binvariant\b", r"\bgame\b",
]

COMB_PLAN_PATTERNS = [
    r"\benumerate\b", r"generate\s+all", r"\bfilter\b", r"brute\s+force",
]

# Hard override for combinatorics requires BOTH code signals AND text signals
# AND no strong NT/algebra tokens
COMB_HARD_CODE = [
    r"itertools\.combinations", r"itertools\.permutations", r"itertools\.product",
    r"\bsubset\b", r"\bbitmask\b",
]

COMB_HARD_TEXT = [
    r"\barrangements?\b", r"\bcounting\b", r"number\s+of\s+ways",
    r"exact\s+counts?", r"\bforbidden\b", r"\bsubstrings?\b",
    r"\bgraph\b", r"\bmatchings?\b",
]

COMBINATORICS_PATTERNS = DomainPatterns(
    hard_override_patterns=[],  # Handled specially
    hard_override_min_matches=1,
    scoring_rules=[
        (COMB_CODE_ITERTOOLS, 5, 'code'),
        (COMB_CODE_ENUMERATION, 5, 'code'),
        (COMB_CODE_STRING, 3, 'code'),
        (COMB_TEXT_PATTERNS, 4, 'text'),
        (COMB_PLAN_PATTERNS, 4, 'text'),
    ],
    penalty_conditions=['strong_nt', 'strong_alg'],
    penalty_score=-4,
)


# ============================================================================
# PATTERN MATCHING UTILITIES
# ============================================================================

def count_pattern_matches(text: str, patterns: List[str], flags: int = re.IGNORECASE) -> int:
    """Count how many distinct patterns match in the text."""
    if not text:
        return 0
    count = 0
    for pattern in patterns:
        if re.search(pattern, text, flags):
            count += 1
    return count


def has_any_pattern(text: str, patterns: List[str], flags: int = re.IGNORECASE) -> bool:
    """Check if any pattern matches in the text."""
    return count_pattern_matches(text, patterns, flags) > 0


# ============================================================================
# FIELD EXTRACTION
# ============================================================================

def extract_fields(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant text fields from payload.

    Args:
        payload: Problem payload with 'problem' and 'code'/'attempts' fields

    Returns:
        Dictionary with extracted and combined text fields:
        - text: problem text
        - code: solution code
        - everything: text + code combined
    """
    problem_text = payload.get("problem", {}).get("text", "") or ""
    code = payload.get("code", "") or ""

    # Resolve code from attempts when top-level code is missing
    if not code:
        pass_at_k = payload.get("outcome", {}).get("pass_at_k") or 0
        attempts = payload.get("attempts", [])
        if pass_at_k > 0 and pass_at_k <= len(attempts):
            code = attempts[pass_at_k - 1].get("code", "") or ""

    return {
        "text": problem_text,
        "code": code,
        "everything": f"{problem_text} {code}",
    }


# ============================================================================
# SIGNAL DETECTION
# ============================================================================

def check_strong_nt_signals(fields: Dict[str, str]) -> bool:
    """Check if strong number theory signals are present."""
    return has_any_pattern(fields["everything"], NT_HARD_OVERRIDE)


def check_strong_alg_signals(fields: Dict[str, str]) -> bool:
    """Check if strong algebra signals are present."""
    return has_any_pattern(fields["everything"], ALG_HARD_OVERRIDE)


def check_combinatorial_enumeration(fields: Dict[str, str]) -> bool:
    """Check if combinatorial enumeration dominates without NT tokens."""
    has_comb = has_any_pattern(fields["code"], COMB_CODE_ITERTOOLS + COMB_CODE_ENUMERATION)
    has_nt = check_strong_nt_signals(fields)
    return has_comb and not has_nt


# ============================================================================
# HEURISTIC SCORING
# ============================================================================

def compute_domain_score(domain: str, fields: Dict[str, str]) -> int:
    """
    Compute heuristic score for a domain.

    Args:
        domain: One of 'algebra', 'number_theory', 'combinatorics', 'geometry'
        fields: Extracted text fields from extract_fields()

    Returns:
        Non-negative integer score
    """
    score = 0

    if domain == "number_theory":
        patterns = NUMBER_THEORY_PATTERNS
    elif domain == "algebra":
        patterns = ALGEBRA_PATTERNS
    elif domain == "geometry":
        patterns = GEOMETRY_PATTERNS
    elif domain == "combinatorics":
        patterns = COMBINATORICS_PATTERNS
    else:
        return 0

    # Apply scoring rules
    for pattern_list, points, target in patterns.scoring_rules:
        if target == 'code':
            text = fields["code"]
        elif target == 'text':
            text = fields["text"]
        elif target == 'all':
            text = fields["everything"]
        else:
            text = fields.get(target, "")

        if has_any_pattern(text, pattern_list):
            score += points

    # Apply penalties
    for condition in patterns.penalty_conditions:
        if condition == 'strong_nt' and check_strong_nt_signals(fields):
            score += patterns.penalty_score
        elif condition == 'strong_alg' and check_strong_alg_signals(fields):
            score += patterns.penalty_score
        elif condition == 'combinatorial_enumeration' and check_combinatorial_enumeration(fields):
            score += patterns.penalty_score

    return max(0, score)  # Don't go below 0


def compute_all_scores(fields: Dict[str, str]) -> Dict[str, int]:
    """
    Compute heuristic scores for all domains.

    Args:
        fields: Extracted text fields from extract_fields()

    Returns:
        Dictionary mapping domain names to scores
    """
    return {
        "algebra": compute_domain_score("algebra", fields),
        "number_theory": compute_domain_score("number_theory", fields),
        "combinatorics": compute_domain_score("combinatorics", fields),
        "geometry": compute_domain_score("geometry", fields),
    }


def get_heuristic_ranking(scores: Dict[str, int]) -> Tuple[str, str, int]:
    """
    Get best domain, second best, and margin.

    Args:
        scores: Dictionary of domain scores

    Returns:
        Tuple of (best_domain, second_best_domain, margin)
    """
    sorted_domains = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    best = sorted_domains[0]
    second = sorted_domains[1] if len(sorted_domains) > 1 else (best[0], 0)
    margin = best[1] - second[1]
    return best[0], second[0], margin


# ============================================================================
# HARD OVERRIDE LOGIC
# ============================================================================

def check_nt_hard_override(fields: Dict[str, str]) -> bool:
    """
    FORCE number_theory if ANY NT tokens appear in code/text
    UNLESS geometry is dominant.
    """
    has_nt = has_any_pattern(fields["everything"], NT_HARD_OVERRIDE)
    if not has_nt:
        return False

    # Check if geometry is dominant (2+ strong geometry objects)
    geom_count = count_pattern_matches(fields["text"], GEOM_HARD_OVERRIDE)
    if geom_count >= 2:
        return False  # Geometry dominates

    return True


def check_alg_hard_override(fields: Dict[str, str]) -> bool:
    """
    FORCE algebra if algebra tokens appear in code/text
    AND no strong NT tokens from rule (1).
    """
    has_alg = has_any_pattern(fields["everything"], ALG_HARD_OVERRIDE)
    if not has_alg:
        return False

    # Check no strong NT tokens
    if has_any_pattern(fields["everything"], NT_HARD_OVERRIDE):
        return False

    return True


def check_geom_hard_override(fields: Dict[str, str]) -> bool:
    """
    FORCE geometry if problem.text contains
    at least TWO strong geometry objects.
    """
    geom_count = count_pattern_matches(fields["text"], GEOM_HARD_OVERRIDE)
    return geom_count >= 2


def check_comb_hard_override(fields: Dict[str, str]) -> bool:
    """
    FORCE combinatorics if:
    - code contains itertools.combinations/permutations/product OR subset/bitmask
    AND
    - text mentions arrangements, counting, etc.
    AND
    - no strong NT or algebra tokens
    """
    # Check code patterns
    has_comb_code = has_any_pattern(fields["code"], COMB_HARD_CODE)
    if not has_comb_code:
        return False

    # Check text patterns
    has_comb_text = has_any_pattern(fields["text"], COMB_HARD_TEXT)
    if not has_comb_text:
        return False

    # Check no strong NT or algebra tokens
    if has_any_pattern(fields["everything"], NT_HARD_OVERRIDE):
        return False
    if has_any_pattern(fields["everything"], ALG_HARD_OVERRIDE):
        return False

    return True


def get_hard_override(fields: Dict[str, str]) -> Optional[str]:
    """
    Check all hard override rules in priority order.
    Returns the forced domain or None if no override applies.

    Priority order:
    1. Geometry (if 2+ strong geometry objects) - highest priority
    2. Number theory (if NT tokens and not geometry dominant)
    3. Algebra (if algebra tokens and no NT tokens)
    4. Combinatorics (if code+text signals and no NT/algebra)
    """
    # Check geometry first (highest visual/structural priority)
    if check_geom_hard_override(fields):
        return "geometry"

    # Then number theory
    if check_nt_hard_override(fields):
        return "number_theory"

    # Then algebra
    if check_alg_hard_override(fields):
        return "algebra"

    # Finally combinatorics
    if check_comb_hard_override(fields):
        return "combinatorics"

    return None


# ============================================================================
# LLM DOMAIN EXTRACTION (from math_structure.from_text)
# ============================================================================

# Normalization map for domains outside ALLOWED_DOMAINS
DOMAIN_NORMALIZATION = {
    "arithmetic": "algebra",
    "probability": "combinatorics",
    "inequalities": "algebra",
    "functional_equations": "algebra",
    "mixed": None,  # signals ambiguous — let heuristic decide
}


def get_llm_domain(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract LLM domain from math_structure.from_text.domain.

    Normalizes non-standard domains via DOMAIN_NORMALIZATION.

    Args:
        payload: Problem payload with 'math_structure' field

    Returns:
        Normalized domain string, or None if missing / ambiguous
    """
    ms = payload.get("math_structure") or {}
    from_text = ms.get("from_text") or {}
    raw_domain = from_text.get("domain")

    if raw_domain is None:
        return None

    raw_domain = raw_domain.strip().lower()

    if raw_domain in ALLOWED_DOMAINS:
        return raw_domain

    # Apply normalization map
    return DOMAIN_NORMALIZATION.get(raw_domain, None)


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

def add_2nd_stage_domain(
    payload: Dict[str, Any],
    h_threshold: int = DEFAULT_H_THRESHOLD,
) -> Dict[str, Any]:
    """
    Main function: compute 2nd stage domain and write to math_structure.

    Sets payload["math_structure"]["domain"] and
    payload["math_structure"]["domain_meta"].

    Args:
        payload: Problem payload with problem text, code,
                 and math_structure fields
        h_threshold: Heuristic margin threshold above which the heuristic
                     overrides the LLM domain (default: 6)

    Returns:
        New payload dict with domain and domain_meta added to math_structure
    """
    # Extract fields for analysis
    fields = extract_fields(payload)

    # Step 1: Get LLM domain (from math_structure.from_text)
    llm_domain = get_llm_domain(payload)

    # Step 2: Compute heuristic scores
    scores = compute_all_scores(fields)
    heur_best, heur_second, heur_margin = get_heuristic_ranking(scores)

    # Step 3: Check hard overrides
    forced_domain = get_hard_override(fields)

    # Step 4: Apply decision logic
    if forced_domain is not None:
        # 1. Hard override fired
        resolved_domain = forced_domain
        decision_reason = f"hard_override:{forced_domain}"
    elif llm_domain is None:
        # 2. LLM domain missing or ambiguous → heuristic best (or algebra fallback)
        resolved_domain = heur_best if scores.get(heur_best, 0) > 0 else "algebra"
        decision_reason = "llm_missing_heuristic_fallback"
    elif llm_domain == heur_best:
        # 3. LLM agrees with heuristic best
        resolved_domain = llm_domain
        decision_reason = "agree"
    elif heur_margin >= h_threshold:
        # 4. Heuristic margin >= threshold → heuristic wins
        resolved_domain = heur_best
        decision_reason = f"heuristic_override:margin={heur_margin}"
    else:
        # 5. Otherwise → LLM wins
        resolved_domain = llm_domain
        decision_reason = "llm_default"

    # Ensure result is in allowed domains
    if resolved_domain not in ALLOWED_DOMAINS:
        resolved_domain = llm_domain if llm_domain in ALLOWED_DOMAINS else "algebra"
        decision_reason = "fallback_to_allowed"

    # Update payload (create new to avoid mutation issues)
    payload_out = dict(payload)
    ms = dict(payload_out.get("math_structure", {}))
    ms["domain"] = resolved_domain
    ms["domain_meta"] = {
        "llm_domain": llm_domain,
        "heur_scores": scores,
        "heur_best": heur_best,
        "heur_margin": heur_margin,
        "forced_domain": forced_domain,
        "decision_reason": decision_reason,
    }
    payload_out["math_structure"] = ms
    return payload_out


def classify_domain(payload: Dict[str, Any]) -> str:
    """
    Convenience function to get just the resolved domain.

    Args:
        payload: Problem payload

    Returns:
        Domain string (one of: algebra, number_theory, combinatorics, geometry)
    """
    result = add_2nd_stage_domain(payload)
    return result["math_structure"]["domain"]


# ============================================================================
# FROM_TEXT HEURISTIC: OBJECTS
# ============================================================================

# Each key is an allowed object label; values are regex patterns to detect it.
OBJECT_PATTERNS: Dict[str, List[str]] = {
    "integer": [
        r"\bintegers?\b", r"\bn\s*[∈∊]\s*ℤ\b", r"\bwhole\s+numbers?\b",
    ],
    "positive_integer": [
        r"\bpositive\s+integers?\b", r"\bnatural\s+numbers?\b",
        r"\bn\s*[∈∊]\s*ℕ\b", r"\bnonnegative\s+integers?\b",
    ],
    "real": [
        r"\breals?\b", r"\breal\s+numbers?\b", r"\bℝ\b",
    ],
    "rational": [
        r"\brationals?\b", r"\brational\s+numbers?\b", r"\bℚ\b",
    ],
    "complex": [
        r"\bcomplex\s+numbers?\b", r"\bℂ\b", r"\bimaginary\b",
    ],
    "sequence": [
        r"\bsequences?\b", r"\ba_n\b", r"\ba_\{?\d+\}?\b",
    ],
    "set": [
        r"\bsets?\b(?!\s+(?:up|to|equal))", r"\bsubsets?\b", r"\bempty\s+set\b",
    ],
    "function": [
        r"\bfunctions?\b", r"\bf\s*:\s*", r"\bf\s*\(\s*[a-z]\s*\)",
    ],
    "polynomial": [
        r"\bpolynomials?\b", r"\bdegree\s+\d", r"\bP\s*\(\s*x\s*\)",
    ],
    "point": [
        r"\bpoints?\b", r"\bvertices\b", r"\bvertex\b",
    ],
    "line": [
        r"\blines?\b", r"\bsegments?\b", r"\brays?\b",
    ],
    "circle": [
        r"\bcircles?\b", r"\bradius\b", r"\bdiameters?\b",
    ],
    "triangle": [
        r"\btriangles?\b", r"△",
    ],
    "polygon": [
        r"\bpolygons?\b", r"\bquadrilaterals?\b", r"\bpentagons?\b",
        r"\bhexagons?\b", r"\brectangles?\b", r"\bsquares?\b",
    ],
    "graph": [
        r"\bgraphs?\b", r"\bedges?\b.*\bvertices\b", r"\bvertices\b.*\bedges?\b",
    ],
    "matrix": [
        r"\bmatrix\b", r"\bmatrices\b",
    ],
    "vector": [
        r"\bvectors?\b",
    ],
}

_MAX_OBJECTS = 3


def extract_objects(problem_text: str) -> List[str]:
    """Extract mathematical objects mentioned in the problem text (max 3)."""
    if not problem_text:
        return []
    matched = []
    for obj, patterns in OBJECT_PATTERNS.items():
        if has_any_pattern(problem_text, patterns):
            matched.append(obj)
    # positive_integer subsumes integer — drop the generic one
    if "positive_integer" in matched and "integer" in matched:
        matched.remove("integer")
    return matched[:_MAX_OBJECTS]


# ============================================================================
# FROM_TEXT HEURISTIC: CONSTRAINTS
# ============================================================================

CONSTRAINT_PATTERNS: Dict[str, List[str]] = {
    "equality": [
        r"(?<![<>!])=(?!=)", r"\bequals?\b", r"\bequal\s+to\b",
    ],
    "inequality": [
        r"[<>≥≤≠]", r"\bgreater\s+than\b", r"\bless\s+than\b",
        r"\bat\s+least\b", r"\bat\s+most\b",
        r"\binequality\b", r"\binequalities\b",
    ],
    "divisibility": [
        r"\bdivides\b", r"\bdivisible\b", r"\bfactor\s+of\b",
        r"\bmultiple\s+of\b",
    ],
    "parity": [
        r"\beven\b", r"\bodd\b", r"\bparity\b",
    ],
    "forall": [
        r"\bfor\s+all\b", r"\bfor\s+every\b", r"\bfor\s+each\b", r"∀",
    ],
    "exists": [
        r"\bthere\s+exists?\b", r"\bfind\b.*\bsuch\s+that\b", r"∃",
    ],
    "bounded": [
        r"\bbounded\b", r"\bbetween\b",
        r"\d\s*[≤<].*[≤<]\s*\d",
    ],
    "distinct": [
        r"\bdistinct\b", r"\bno\s+two\b.*\bsame\b",
    ],
    "monotonic": [
        r"\bincreasing\b", r"\bdecreasing\b", r"\bmonotonic\b",
        r"\bnon-decreasing\b", r"\bnon-increasing\b",
    ],
    "symmetry": [
        r"\bsymmetric\b", r"\bsymmetry\b",
    ],
    "invariant": [
        r"\binvariant\b",
    ],
}

_MAX_CONSTRAINTS = 4


def extract_constraints(problem_text: str) -> List[str]:
    """Extract constraint types from the problem text (max 4)."""
    if not problem_text:
        return []
    matched = []
    for constraint, patterns in CONSTRAINT_PATTERNS.items():
        if has_any_pattern(problem_text, patterns):
            matched.append(constraint)
    return matched[:_MAX_CONSTRAINTS]


# ============================================================================
# FROM_TEXT HEURISTIC: OUTPUT_TYPE
# ============================================================================

# Ordered by priority — first match wins for ambiguous statements.
_OUTPUT_TYPE_RULES: List[Tuple[str, List[str]]] = [
    ("proof", [
        r"\bprove\b", r"\bshow\s+that\b",
    ]),
    ("existence", [
        r"\bdoes\s+there\s+exist\b", r"\bis\s+there\b.*\?",
    ]),
    ("non_existence", [
        r"\bno\s+such\b", r"\bcannot\s+exist\b", r"\bimpossible\b",
    ]),
    ("classification", [
        r"\bfind\s+all\b", r"\bdetermine\s+all\b", r"\bcharacterize\b",
    ]),
    ("maximum", [
        r"\bmaximum\b", r"\blargest\b", r"\bgreatest\b",
    ]),
    ("minimum", [
        r"\bminimum\b", r"\bsmallest\b", r"\bleast\b",
    ]),
    ("exact_value", [
        r"\bfind\b", r"\bcompute\b", r"\bcalculate\b", r"\bdetermine\b",
        r"\bwhat\s+is\b", r"\bhow\s+many\b", r"\bevaluate\b",
    ]),
]


def extract_output_type(problem_text: str) -> Optional[str]:
    """Determine the output type from the problem's question intent."""
    if not problem_text:
        return None
    for output_type, patterns in _OUTPUT_TYPE_RULES:
        if has_any_pattern(problem_text, patterns):
            return output_type
    return "exact_value"


# ============================================================================
# FROM_TEXT HEURISTIC: MECHANISMS
# ============================================================================

ALLOWED_MECHANISM_LABELS = frozenset([
    "induction", "pigeonhole", "extremal", "case_analysis",
    "invariant", "monovariant", "algebraic_manipulation",
    "geometric_congruence", "geometric_similarity", "counting",
])

_MAX_MECHANISMS = 3

# Regex patterns matched against the problem text
MECHANISM_TEXT_PATTERNS: Dict[str, List[str]] = {
    "induction": [
        r"\binduction\b", r"\binductive\b", r"\bbase\s+case\b",
    ],
    "pigeonhole": [
        r"\bpigeonhole\b", r"\bDirichlet\b",
    ],
    "extremal": [
        r"\bextremal\b", r"\bminimal\s+counterexample\b",
    ],
    "case_analysis": [
        r"\bconsider\s+cases\b", r"\bCase\s+1\b", r"\bWLOG\b",
    ],
    "invariant": [
        r"\binvariant\b", r"\bremains\s+constant\b", r"\bremains\s+unchanged\b",
    ],
    "monovariant": [
        r"\bmonovariant\b",
    ],
    "algebraic_manipulation": [
        r"\bVieta\b", r"\bAM-GM\b", r"\bCauchy-Schwarz\b",
        r"\bfactorize\b", r"\bsubstitution\b",
    ],
    "geometric_congruence": [
        r"\bcongruent\b.*\btriangle\b", r"\btriangle\b.*\bcongruent\b",
        r"\bSAS\b", r"\bASA\b", r"\bSSS\b", r"\bAAS\b",
    ],
    "geometric_similarity": [
        r"\bsimilar\s+triangles\b", r"\bhomothety\b",
    ],
    "counting": [
        r"\bhow\s+many\b", r"\bnumber\s+of\s+ways\b",
        r"\bcombinations?\b", r"\bpermutations?\b",
    ],
}

# Regex patterns matched against solution code
MECHANISM_CODE_PATTERNS: Dict[str, List[str]] = {
    "counting": [
        r"itertools\.combinations\b", r"itertools\.permutations\b",
        r"itertools\.product\b", r"\bmath\.comb\b", r"\bmath\.factorial\b",
    ],
    "algebraic_manipulation": [
        r"\bimport\s+sympy\b", r"\bfrom\s+sympy\b",
        r"\bsolve\s*\(", r"\bsimplify\s*\(", r"\bexpand\s*\(",
        r"\bfactor\s*\(", r"\bPoly\s*\(",
    ],
    "case_analysis": [
        r"#\s*[Cc]ase\s+\d",
    ],
}


def _detect_induction_code(code: str) -> bool:
    """Detect induction via recursive function definitions (def + self-call)."""
    if not code:
        return False
    func_names = re.findall(r"^\s*def\s+(\w+)\s*\(", code, re.MULTILINE)
    for name in func_names:
        # Check if the function body calls itself
        pattern = rf"\b{re.escape(name)}\s*\("
        # Find the def line, then search for self-call after it
        for m in re.finditer(rf"^\s*def\s+{re.escape(name)}\s*\(", code, re.MULTILINE):
            rest = code[m.end():]
            if re.search(pattern, rest):
                return True
    return False


def _detect_case_analysis_code(code: str) -> bool:
    """Detect case analysis via 2+ elif branches or 3+ Case labels."""
    if not code:
        return False
    elif_count = len(re.findall(r"^\s*elif\s+", code, re.MULTILINE))
    if elif_count >= 2:
        return True
    case_labels = set(re.findall(r"\b[Cc]ase\s+(\d+)", code))
    if len(case_labels) >= 3:
        return True
    return False


def extract_mechanisms(fields: Dict[str, str]) -> List[str]:
    """
    Extract mathematical mechanisms from problem text and solution code.

    Matches text patterns first, then code patterns, then custom detectors.
    Returns list of mechanism labels capped at _MAX_MECHANISMS.
    """
    text = fields.get("text", "")
    code = fields.get("code", "")
    matched = []
    seen = set()

    # 1. Text patterns
    for mechanism, patterns in MECHANISM_TEXT_PATTERNS.items():
        if mechanism not in seen and has_any_pattern(text, patterns):
            matched.append(mechanism)
            seen.add(mechanism)

    # 2. Code patterns
    for mechanism, patterns in MECHANISM_CODE_PATTERNS.items():
        if mechanism not in seen and has_any_pattern(code, patterns):
            matched.append(mechanism)
            seen.add(mechanism)

    # 3. Custom detectors
    if "induction" not in seen and _detect_induction_code(code):
        matched.append("induction")
        seen.add("induction")

    if "case_analysis" not in seen and _detect_case_analysis_code(code):
        matched.append("case_analysis")
        seen.add("case_analysis")

    return matched[:_MAX_MECHANISMS]


# ============================================================================
# FROM_SOLUTION HEURISTIC: REASONING SHAPE
# ============================================================================

def extract_reasoning_shape(code: str) -> str:
    """
    Classify reasoning shape from solution code.

    Returns: "linear" | "branching"
    """
    if not code:
        return "linear"

    # Count if/elif/else occurrences
    if_count = len(re.findall(r"^\s*if\s+", code, re.MULTILINE))
    elif_count = len(re.findall(r"^\s*elif\s+", code, re.MULTILINE))
    else_count = len(re.findall(r"^\s*else\s*:", code, re.MULTILINE))

    # Explicit "Case N" labels in comments or text
    case_labels = len(set(re.findall(r"\b[Cc]ase\s+(\d+)", code)))

    branch_signals = elif_count + case_labels
    # Single if/else is common control flow, not branching reasoning.
    # Require elif, multiple if/else pairs, or case labels.
    if branch_signals >= 1 or (if_count >= 2 and else_count >= 2):
        return "branching"

    return "linear"


# ============================================================================
# FROM_SOLUTION HEURISTIC: CASE SPLIT
# ============================================================================

def extract_case_split(code: str) -> str:
    """
    Detect case splitting in solution code.

    Returns: "none" | "binary" | "multi"
    """
    if not code:
        return "none"

    case_labels = set(re.findall(r"\b[Cc]ase\s+(\d+)", code))
    n_cases = len(case_labels)

    elif_count = len(re.findall(r"^\s*elif\s+", code, re.MULTILINE))
    if_count = len(re.findall(r"^\s*if\s+", code, re.MULTILINE))
    else_count = len(re.findall(r"^\s*else\s*:", code, re.MULTILINE))

    if n_cases >= 3 or elif_count >= 2:
        return "multi"
    if n_cases == 2 or (elif_count == 1):
        return "binary"
    # A single if/else pair with no elif: binary split
    if if_count >= 1 and else_count >= 1 and elif_count == 0:
        return "binary"

    return "none"


# ============================================================================
# FROM_SOLUTION HEURISTIC: AUXILIARY CONSTRUCTION
# ============================================================================

_STRUCTURAL_PATTERNS = [
    r"^\s*def\s+\w+\s*\(",        # function definitions
    r"^\s*class\s+\w+",           # class definitions
    r"\bdefaultdict\b",
    r"\bCounter\b",
    r"\bdeque\b",
    r"\bheapq\b",
]

# Skip these common LHS names when deciding "symbolic"
_SKIP_VARS = frozenset((
    "_", "i", "j", "k", "n", "m", "x", "y", "f", "line", "ans", "result",
    "res", "ret", "output", "answer", "MOD", "mod", "INF", "inf",
))


def extract_auxiliary_construction(code: str) -> str:
    """
    Detect auxiliary constructions in solution code.

    Returns: "none" | "symbolic" | "structural"
    """
    if not code:
        return "none"

    # Structural: helper functions, custom data structures
    if has_any_pattern(code, _STRUCTURAL_PATTERNS, flags=re.MULTILINE):
        return "structural"

    # Symbolic: count non-trivial variable assignments
    assignments = re.findall(
        r"^\s*([a-zA-Z_]\w*)\s*=(?!=)", code, re.MULTILINE,
    )
    meaningful = [v for v in assignments if v not in _SKIP_VARS]
    if len(meaningful) >= 3:
        return "symbolic"

    return "none"


# ============================================================================
# FROM_SOLUTION HEURISTIC: REASONING DEPTH PROXY
# ============================================================================

def extract_reasoning_depth_proxy(code: str) -> str:
    """
    Estimate reasoning depth from code structure.

    Counts logical steps (assignments + control flow) and max indentation.

    Returns: "shallow" | "medium" | "deep"
    """
    if not code:
        return "shallow"

    _STEP_PATTERNS = [
        r"^\s*[a-zA-Z_]\w*\s*[+\-*/]?=",   # assignments
        r"^\s*if\s+",
        r"^\s*elif\s+",
        r"^\s*for\s+",
        r"^\s*while\s+",
        r"^\s*return\b",
    ]

    total_steps = 0
    for pat in _STEP_PATTERNS:
        total_steps += len(re.findall(pat, code, re.MULTILINE))

    # Max indentation depth (approximate nesting level)
    max_indent = 0
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped:
            indent_chars = len(line) - len(stripped)
            level = indent_chars // 4
            if level > max_indent:
                max_indent = level

    if total_steps <= 8 and max_indent <= 2:
        return "shallow"
    if total_steps >= 25 or max_indent >= 5:
        return "deep"
    return "medium"


# ============================================================================
# FROM_SOLUTION HEURISTIC: INTERMEDIATE REUSE PROXY
# ============================================================================

def extract_intermediate_reuse_proxy(code: str) -> str:
    """
    Estimate intermediate-result reuse from code.

    Counts how many assigned variable names are referenced again downstream.

    Returns: "none" | "single" | "multiple"
    """
    if not code:
        return "none"

    lines = code.splitlines()

    # Collect (var_name, line_index) for non-trivial assignments
    assigned: List[Tuple[str, int]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^\s*([a-zA-Z_]\w*)\s*=(?!=)", line)
        if m:
            var = m.group(1)
            if var not in _SKIP_VARS:
                assigned.append((var, i))

    if not assigned:
        return "none"

    reused = 0
    for var, assign_idx in assigned:
        pat = re.compile(rf"\b{re.escape(var)}\b")
        for j in range(assign_idx + 1, len(lines)):
            later = lines[j]
            # Skip lines that re-assign this same var
            if re.match(rf"^\s*{re.escape(var)}\s*=(?!=)", later):
                continue
            if pat.search(later):
                reused += 1
                break

    if reused >= 3:
        return "multiple"
    if reused >= 1:
        return "single"
    return "none"


# ============================================================================
# COMBINED HEURISTIC EXTRACTION
# ============================================================================

def extract_from_text_heuristic(fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract from_text properties heuristically (objects, constraints, output_type, mechanisms).
    Domain is handled separately by the existing add_2nd_stage_domain logic.
    """
    text = fields["text"]
    return {
        "objects": extract_objects(text),
        "constraints": extract_constraints(text),
        "output_type": extract_output_type(text),
        "mechanisms": extract_mechanisms(fields),
    }


def extract_from_solution_heuristic(fields: Dict[str, str]) -> Dict[str, Any]:
    """Extract from_solution properties heuristically from the solution code."""
    code = fields["code"]
    return {
        "reasoning_shape": extract_reasoning_shape(code),
        "case_split": extract_case_split(code),
        "auxiliary_construction": extract_auxiliary_construction(code),
        "reasoning_depth_proxy": extract_reasoning_depth_proxy(code),
        "intermediate_reuse_proxy": extract_intermediate_reuse_proxy(code),
    }


def extract_all_heuristic(
    payload: Dict[str, Any],
    h_threshold: int = DEFAULT_H_THRESHOLD,
) -> Dict[str, Any]:
    """
    Full heuristic extraction: domain + from_text + from_solution.

    Writes to:
        math_structure.domain          (existing logic, unchanged)
        math_structure.domain_meta     (existing logic, unchanged)
        math_structure.from_text_heuristic   {objects, constraints, output_type}
        math_structure.from_solution_heuristic  {reasoning_shape, case_split, ...}

    Returns:
        New payload dict with all heuristic fields populated.
    """
    payload_out = add_2nd_stage_domain(payload, h_threshold)
    fields = extract_fields(payload)

    ms = dict(payload_out.get("math_structure", {}))
    ms["from_text_heuristic"] = extract_from_text_heuristic(fields)
    ms["from_solution_heuristic"] = extract_from_solution_heuristic(fields)
    payload_out["math_structure"] = ms
    return payload_out


# ============================================================================
# CONSENSUS MECHANISM
# ============================================================================

@dataclass
class ConsensusResult:
    """Result of merging heuristic and LLM values for a single field."""
    value: Any
    source: str          # "heuristic" | "llm" | "merged"
    confidence: str      # "high" | "med" | "low"
    disagreement: bool = False


# --- Per-field merge modes (for reference / future generic dispatch) ---
MERGE_MODE: Dict[str, str] = {
    "reasoning_shape":          "HARD_HEUR",
    "case_split":               "HARD_HEUR",
    "auxiliary_construction":    "HEUR_LLM_FALLBACK",
    "reasoning_depth_proxy":    "HARD_HEUR",
    "intermediate_reuse_proxy": "HARD_HEUR",
    "objects":                  "UNION_CAP",
    "constraints":              "HEUR_ADD_ONLY",
    "output_type":              "HEUR_LLM_FALLBACK",
    "mechanisms":               "UNION_CAP",
}

# Allowed labels (for filtering LLM values)
ALLOWED_OBJECT_LABELS = set(OBJECT_PATTERNS.keys())
ALLOWED_CONSTRAINT_LABELS = set(CONSTRAINT_PATTERNS.keys())

# Trigger words for forall/exists LLM add-only
_FORALL_TRIGGERS = [r"\bfor\s+all\b", r"\bfor\s+every\b", r"\bfor\s+each\b", r"∀"]
_EXISTS_TRIGGERS = [r"\bthere\s+exists?\b", r"\bfind\b.*\bsuch\s+that\b", r"∃"]

# Explicit output_type triggers (for LLM fallback acceptance)
_OUTPUT_TYPE_TRIGGERS: Dict[str, List[str]] = {
    "proof":          [r"\bprove\b", r"\bshow\s+that\b"],
    "existence":      [r"\bdoes\s+there\s+exist\b", r"\bis\s+there\b.*\?"],
    "non_existence":  [r"\bno\s+such\b", r"\bcannot\s+exist\b", r"\bimpossible\b"],
    "classification": [r"\bfind\s+all\b", r"\bdetermine\s+all\b", r"\bcharacterize\b"],
    "maximum":        [r"\bmaximum\b", r"\blargest\b", r"\bgreatest\b"],
    "minimum":        [r"\bminimum\b", r"\bsmallest\b", r"\bleast\b"],
}


# ============================================================================
# PER-FIELD CONSENSUS FUNCTIONS
# ============================================================================

def _consensus_reasoning_shape(
    heur_val: str, llm_val: Optional[str]
) -> ConsensusResult:
    """Heuristic always wins. High confidence when non-linear."""
    conf = "high" if heur_val != "linear" else "med"
    disagree = llm_val is not None and llm_val != heur_val
    return ConsensusResult(heur_val, "heuristic", conf, disagree)


def _consensus_case_split(
    heur_val: str, llm_val: Optional[str]
) -> ConsensusResult:
    """Heuristic always wins. High confidence for binary/multi."""
    conf = "high" if heur_val in ("binary", "multi") else "med"
    disagree = llm_val is not None and llm_val != heur_val
    return ConsensusResult(heur_val, "heuristic", conf, disagree)


def _consensus_auxiliary_construction(
    heur_val: str, llm_val: Optional[str]
) -> ConsensusResult:
    """Heuristic-first, LLM fallback only to upgrade from 'none' to 'structural'."""
    if heur_val == "structural":
        disagree = llm_val is not None and llm_val != heur_val
        return ConsensusResult("structural", "heuristic", "high", disagree)
    if heur_val == "symbolic":
        disagree = llm_val is not None and llm_val != heur_val
        return ConsensusResult("symbolic", "heuristic", "med", disagree)
    # heur_val == "none": accept LLM "structural" as low-confidence fallback
    if llm_val == "structural":
        return ConsensusResult("structural", "llm", "low", True)
    disagree = llm_val is not None and llm_val != "none"
    return ConsensusResult("none", "heuristic", "med", disagree)


def _consensus_reasoning_depth(
    heur_val: str, llm_val: Optional[str]
) -> ConsensusResult:
    """Heuristic-only proxy bucket."""
    disagree = llm_val is not None and llm_val != heur_val
    return ConsensusResult(heur_val, "heuristic", "med", disagree)


def _consensus_intermediate_reuse(
    heur_val: str, llm_val: Optional[str]
) -> ConsensusResult:
    """Heuristic-only proxy bucket."""
    disagree = llm_val is not None and llm_val != heur_val
    return ConsensusResult(heur_val, "heuristic", "med", disagree)


def _consensus_objects(
    heur_vals: List[str],
    llm_vals: Optional[List[str]],
    max_objects: int = 3,
) -> ConsensusResult:
    """Union with cap. Heuristic ranked first, LLM adds if in allowlist."""
    if not llm_vals:
        conf = "high" if heur_vals else "low"
        return ConsensusResult(heur_vals[:max_objects], "heuristic", conf, False)

    result = list(heur_vals)
    seen = set(result)

    for obj in llm_vals:
        if obj in ALLOWED_OBJECT_LABELS and obj not in seen and len(result) < max_objects:
            result.append(obj)
            seen.add(obj)

    if not heur_vals and llm_vals:
        source = "llm"
        conf = "low"
    elif set(heur_vals) != set(result):
        source = "merged"
        conf = "med"
    else:
        source = "heuristic"
        conf = "high"

    disagree = set(heur_vals) != set(llm_vals or [])
    return ConsensusResult(result[:max_objects], source, conf, disagree)


def _consensus_mechanisms(
    heur_vals: List[str],
    llm_vals: Optional[List[str]],
    max_mechanisms: int = _MAX_MECHANISMS,
) -> ConsensusResult:
    """Union with cap. Heuristic ranked first, LLM adds if in allowlist."""
    if not llm_vals:
        conf = "high" if heur_vals else "low"
        return ConsensusResult(heur_vals[:max_mechanisms], "heuristic", conf, False)

    result = list(heur_vals)
    seen = set(result)

    for mech in llm_vals:
        if mech in ALLOWED_MECHANISM_LABELS and mech not in seen and len(result) < max_mechanisms:
            result.append(mech)
            seen.add(mech)

    if not heur_vals and llm_vals:
        source = "llm"
        conf = "low"
    elif set(heur_vals) != set(result):
        source = "merged"
        conf = "med"
    else:
        source = "heuristic"
        conf = "high"

    disagree = set(heur_vals) != set(llm_vals or [])
    return ConsensusResult(result[:max_mechanisms], source, conf, disagree)


def _consensus_constraints(
    heur_vals: List[str],
    llm_vals: Optional[List[str]],
    problem_text: str,
    max_constraints: int = 4,
) -> ConsensusResult:
    """Heuristic base. LLM can add forall/exists only if trigger words present."""
    result = list(heur_vals)
    seen = set(result)
    added_from_llm = False

    if llm_vals:
        for c in llm_vals:
            if c in seen or c not in ("forall", "exists"):
                continue
            if len(result) >= max_constraints:
                break
            triggers = _FORALL_TRIGGERS if c == "forall" else _EXISTS_TRIGGERS
            if has_any_pattern(problem_text, triggers):
                result.append(c)
                seen.add(c)
                added_from_llm = True

    source = "merged" if added_from_llm else "heuristic"
    conf = "high" if heur_vals else "low"
    disagree = set(heur_vals) != set(llm_vals or [])
    return ConsensusResult(result[:max_constraints], source, conf, disagree)


def _consensus_output_type(
    heur_val: Optional[str],
    llm_val: Optional[str],
    problem_text: str,
) -> ConsensusResult:
    """Heuristic overrides. LLM fallback only when heuristic returns default."""
    heur_default = "exact_value"

    if heur_val and heur_val != heur_default:
        disagree = llm_val is not None and llm_val != heur_val
        return ConsensusResult(heur_val, "heuristic", "high", disagree)

    # Heuristic returned default; check if LLM has something more specific
    if llm_val and llm_val != heur_default and llm_val in _OUTPUT_TYPE_TRIGGERS:
        triggers = _OUTPUT_TYPE_TRIGGERS[llm_val]
        if has_any_pattern(problem_text, triggers):
            return ConsensusResult(llm_val, "llm", "med", True)

    val = heur_val or heur_default
    disagree = llm_val is not None and llm_val != val
    return ConsensusResult(val, "heuristic", "med", disagree)


# ============================================================================
# FULL CONSENSUS MERGE
# ============================================================================

def merge_consensus(
    payload: Dict[str, Any],
    h_threshold: int = DEFAULT_H_THRESHOLD,
) -> Dict[str, Any]:
    """
    Merge heuristic and LLM math_structure fields using consensus rules.

    Updates from_text and from_solution IN-PLACE with consensus values.
    Stores compact metadata in math_structure.consensus_meta.

    Returns:
        New payload with updated math_structure.
    """
    # Run heuristic extraction (populates domain, domain_meta,
    # from_text_heuristic, from_solution_heuristic)
    payload_out = extract_all_heuristic(payload, h_threshold)
    ms = dict(payload_out.get("math_structure", {}))

    llm_from_text = ms.get("from_text") or {}
    llm_from_sol = ms.get("from_solution") or {}
    heur_from_text = ms.get("from_text_heuristic") or {}
    heur_from_sol = ms.get("from_solution_heuristic") or {}
    problem_text = (payload.get("problem", {}).get("text", "") or "")

    # Mutable copies of the sections we'll update
    from_text = dict(llm_from_text)
    from_sol = dict(llm_from_sol)
    meta: Dict[str, Any] = {}

    # --- from_solution fields ---

    cr = _consensus_reasoning_shape(
        heur_from_sol.get("reasoning_shape", "linear"),
        llm_from_sol.get("reasoning_shape"),
    )
    from_sol["reasoning_shape"] = cr.value
    meta["reasoning_shape"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_case_split(
        heur_from_sol.get("case_split", "none"),
        llm_from_sol.get("case_split"),
    )
    from_sol["case_split"] = cr.value
    meta["case_split"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_auxiliary_construction(
        heur_from_sol.get("auxiliary_construction", "none"),
        llm_from_sol.get("auxiliary_construction"),
    )
    from_sol["auxiliary_construction"] = cr.value
    meta["auxiliary_construction"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_reasoning_depth(
        heur_from_sol.get("reasoning_depth_proxy", "shallow"),
        llm_from_sol.get("reasoning_depth"),
    )
    from_sol["reasoning_depth"] = cr.value
    meta["reasoning_depth"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_intermediate_reuse(
        heur_from_sol.get("intermediate_reuse_proxy", "none"),
        llm_from_sol.get("intermediate_reuse"),
    )
    from_sol["intermediate_reuse"] = cr.value
    meta["intermediate_reuse"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    # --- from_text fields ---

    cr = _consensus_objects(
        heur_from_text.get("objects", []),
        llm_from_text.get("objects"),
    )
    from_text["objects"] = cr.value
    meta["objects"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_constraints(
        heur_from_text.get("constraints", []),
        llm_from_text.get("constraints"),
        problem_text,
    )
    from_text["constraints"] = cr.value
    meta["constraints"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_mechanisms(
        heur_from_text.get("mechanisms", []),
        llm_from_text.get("mechanisms"),
    )
    from_text["mechanisms"] = cr.value
    meta["mechanisms"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    cr = _consensus_output_type(
        heur_from_text.get("output_type"),
        llm_from_text.get("output_type"),
        problem_text,
    )
    from_text["output_type"] = cr.value
    meta["output_type"] = {"source": cr.source, "confidence": cr.confidence, "disagreement": cr.disagreement}

    # Write back — update existing sections, no new top-level keys
    ms["from_text"] = from_text
    ms["from_solution"] = from_sol
    ms["consensus_meta"] = meta

    # Clean up intermediate heuristic sections
    ms.pop("from_text_heuristic", None)
    ms.pop("from_solution_heuristic", None)

    payload_out["math_structure"] = ms
    return payload_out


# ============================================================================
# JSONL BATCH PROCESSING
# ============================================================================

def run_consensus_on_jsonl(
    input_path: str,
    output_path: str,
    h_threshold: int = DEFAULT_H_THRESHOLD,
) -> Dict[str, Any]:
    """
    Read a JSONL file, run heuristic + consensus merge on each record,
    and write updated records to output_path.

    Args:
        input_path:  Path to input .jsonl file
        output_path: Path to output .jsonl file
        h_threshold: Heuristic margin threshold for domain override

    Returns:
        Summary stats dict with counts and disagreement rates.
    """
    total = 0
    consensus_fields = list(MERGE_MODE.keys())
    disagreement_counts: Dict[str, int] = {f: 0 for f in consensus_fields}
    source_counts: Dict[str, Dict[str, int]] = {
        f: {"heuristic": 0, "llm": 0, "merged": 0}
        for f in consensus_fields
    }

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            payload_out = merge_consensus(payload, h_threshold)
            fout.write(json.dumps(payload_out, ensure_ascii=False) + "\n")
            total += 1

            # Collect stats from consensus_meta
            meta = payload_out.get("math_structure", {}).get("consensus_meta", {})
            for field_name, m in meta.items():
                if field_name in disagreement_counts:
                    if m.get("disagreement"):
                        disagreement_counts[field_name] += 1
                    src = m.get("source", "heuristic")
                    if field_name in source_counts and src in source_counts[field_name]:
                        source_counts[field_name][src] += 1

    stats = {
        "total_records": total,
        "disagreement_counts": disagreement_counts,
        "disagreement_rates": {
            k: round(v / total, 4) if total > 0 else 0.0
            for k, v in disagreement_counts.items()
        },
        "source_counts": source_counts,
    }
    return stats
