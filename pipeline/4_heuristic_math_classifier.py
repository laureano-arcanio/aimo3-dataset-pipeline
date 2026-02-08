"""Heuristic Math Classifier Module

Provides heuristic-based classification for math problems:
- Domain classification (algebra, number_theory, combinatorics, geometry)
- from_text extraction: objects, constraints, output_type
- from_solution extraction: reasoning_shape, case_split, auxiliary_construction, 
  reasoning_depth_proxy, intermediate_reuse_proxy

Usage:
    from heuristic_math_classifier import extract_all_heuristic

    result = extract_all_heuristic(payload)
    ms = result["math_structure"]
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field


# Configuration
ALLOWED_DOMAINS = {"algebra", "number_theory", "combinatorics", "geometry"}
DEFAULT_H_THRESHOLD = 6


# Pattern Definitions

@dataclass
class DomainPatterns:
    """Pattern definitions for a single domain."""
    hard_override_patterns: List[str] = field(default_factory=list)
    hard_override_min_matches: int = 1
    scoring_rules: List[Tuple[List[str], int, str]] = field(default_factory=list)
    penalty_conditions: List[str] = field(default_factory=list)
    penalty_score: int = -4


# Number Theory Patterns
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
        (NT_PLAN_PATTERNS, 4, 'plan_goal'),
    ],
    penalty_conditions=['combinatorial_enumeration'],
    penalty_score=-4,
)


# Algebra Patterns
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
        (ALG_PLAN_PATTERNS, 4, 'plan_goal'),
    ],
    penalty_conditions=['strong_nt'],
    penalty_score=-4,
)


# Geometry Patterns
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
        (GEOM_PLAN_PATTERNS, 4, 'plan_goal'),
        (GEOM_CODE_PATTERNS, 6, 'code'),
    ],
    penalty_conditions=['strong_nt'],
    penalty_score=-4,
)


# Combinatorics Patterns
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
        (COMB_PLAN_PATTERNS, 4, 'plan_goal'),
    ],
    penalty_conditions=['strong_nt', 'strong_alg'],
    penalty_score=-4,
)


# Pattern Matching Utilities

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


# Field Extraction

def extract_fields(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant text fields from payload.

    Args:
        payload: Problem payload with 'problem', 'goal', 'plan', 'code' fields

    Returns:
        Dictionary with extracted and combined text fields:
        - text: problem text
        - goal: goal text
        - plan: plan text
        - code: code text
        - all_text: combined problem + goal + plan
        - plan_goal: combined plan + goal
        - everything: all fields combined
    """
    problem_text = payload.get("problem", {}).get("text", "") or ""
    goal = payload.get("goal", "") or ""
    plan = payload.get("plan", "") or ""
    code = payload.get("code", "") or ""

    # Resolve code from attempts when top-level code is missing
    if not code:
        pass_at_k = payload.get("outcome", {}).get("pass_at_k") or 0
        attempts = payload.get("attempts", [])
        if pass_at_k > 0 and pass_at_k <= len(attempts):
            code = attempts[pass_at_k - 1].get("code", "") or ""

    # Combine for convenience
    all_text = f"{problem_text} {goal} {plan}"
    plan_goal = f"{plan} {goal}"

    return {
        "text": problem_text,
        "goal": goal,
        "plan": plan,
        "code": code,
        "all_text": all_text,
        "plan_goal": plan_goal,
        "everything": f"{all_text} {code}",
    }


# Signal Detection

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


# Heuristic Scoring

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
        elif target == 'plan_goal':
            text = fields["plan_goal"]
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


# Hard Override Logic

def check_nt_hard_override(fields: Dict[str, str]) -> bool:
    """Force number_theory if NT tokens appear unless geometry is dominant."""
    has_nt = has_any_pattern(fields["everything"], NT_HARD_OVERRIDE)
    if not has_nt:
        return False

    # Check if geometry is dominant (2+ strong geometry objects)
    geom_count = count_pattern_matches(fields["all_text"], GEOM_HARD_OVERRIDE)
    if geom_count >= 2:
        return False  # Geometry dominates

    return True


def check_alg_hard_override(fields: Dict[str, str]) -> bool:
    """Force algebra if algebra tokens appear and no strong NT tokens."""
    has_alg = has_any_pattern(fields["everything"], ALG_HARD_OVERRIDE)
    if not has_alg:
        return False

    # Check no strong NT tokens
    if has_any_pattern(fields["everything"], NT_HARD_OVERRIDE):
        return False

    return True


def check_geom_hard_override(fields: Dict[str, str]) -> bool:
    """Force geometry if text contains at least two strong geometry objects."""
    geom_count = count_pattern_matches(fields["all_text"], GEOM_HARD_OVERRIDE)
    return geom_count >= 2


def check_comb_hard_override(fields: Dict[str, str]) -> bool:
    """Force combinatorics if code + text signals present and no NT/algebra tokens."""
    has_comb_code = has_any_pattern(fields["code"], COMB_HARD_CODE)
    if not has_comb_code:
        return False

    has_comb_text = has_any_pattern(fields["all_text"], COMB_HARD_TEXT)
    if not has_comb_text:
        return False

    if has_any_pattern(fields["everything"], NT_HARD_OVERRIDE):
        return False
    if has_any_pattern(fields["everything"], ALG_HARD_OVERRIDE):
        return False

    return True


def get_hard_override(fields: Dict[str, str]) -> Optional[str]:
    """Check all hard override rules in priority order.
    
    Returns the forced domain or None if no override applies.
    """
    if check_geom_hard_override(fields):
        return "geometry"

    if check_nt_hard_override(fields):
        return "number_theory"

    if check_alg_hard_override(fields):
        return "algebra"
    if check_comb_hard_override(fields):
        return "combinatorics"

    return None


# LLM Domain Extraction
DOMAIN_NORMALIZATION = {
    "arithmetic": "algebra",
    "probability": "combinatorics",
    "inequalities": "algebra",
    "functional_equations": "algebra",
    "mixed": None,  # signals ambiguous — let heuristic decide
}


def get_llm_domain(payload: Dict[str, Any]) -> Optional[str]:
    """Extract LLM domain from math_structure.from_text.domain.
    
    Normalizes non-standard domains via DOMAIN_NORMALIZATION.
    """
    ms = payload.get("math_structure") or {}
    from_text = ms.get("from_text") or {}
    raw_domain = from_text.get("domain")

    if raw_domain is None:
        return None

    raw_domain = raw_domain.strip().lower()

    if raw_domain in ALLOWED_DOMAINS:
        return raw_domain
    return DOMAIN_NORMALIZATION.get(raw_domain, None)


# Main Classifier

def add_2nd_stage_domain(
    payload: Dict[str, Any],
    h_threshold: int = DEFAULT_H_THRESHOLD,
) -> Dict[str, Any]:
    """Compute 2nd stage domain and write to math_structure.
    
    Sets payload["math_structure"]["domain"] and ["domain_meta"].
    """
    fields = extract_fields(payload)
    llm_domain = get_llm_domain(payload)
    scores = compute_all_scores(fields)
    heur_best, heur_second, heur_margin = get_heuristic_ranking(scores)
    forced_domain = get_hard_override(fields)
    if forced_domain is not None:
        resolved_domain = forced_domain
        decision_reason = f"hard_override:{forced_domain}"
    elif llm_domain is None:
        resolved_domain = heur_best if scores.get(heur_best, 0) > 0 else "algebra"
        decision_reason = "llm_missing_heuristic_fallback"
    elif llm_domain == heur_best:
        resolved_domain = llm_domain
        decision_reason = "agree"
    elif heur_margin >= h_threshold:
        resolved_domain = heur_best
        decision_reason = f"heuristic_override:margin={heur_margin}"
    else:
        resolved_domain = llm_domain
        decision_reason = "llm_default"
    if resolved_domain not in ALLOWED_DOMAINS:
        resolved_domain = llm_domain if llm_domain in ALLOWED_DOMAINS else "algebra"
        decision_reason = "fallback_to_allowed"
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
    """Convenience function to get just the resolved domain."""
    result = add_2nd_stage_domain(payload)
    return result["math_structure"]["domain"]


# From Text Heuristic: Objects
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
    if "positive_integer" in matched and "integer" in matched:
        matched.remove("integer")
    return matched[:_MAX_OBJECTS]


# From Text Heuristic: Constraints

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


# From Text Heuristic: Output Type
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


# From Solution Heuristic: Reasoning Shape

def extract_reasoning_shape(code: str) -> str:
    """
    Classify reasoning shape from solution code.

    Returns: "linear" | "branching"
    """
    if not code:
        return "linear"

    if_count = len(re.findall(r"^\s*if\s+", code, re.MULTILINE))
    elif_count = len(re.findall(r"^\s*elif\s+", code, re.MULTILINE))
    else_count = len(re.findall(r"^\s*else\s*:", code, re.MULTILINE))

    case_labels = len(set(re.findall(r"\b[Cc]ase\s+(\d+)", code)))

    branch_signals = elif_count + case_labels
    if branch_signals >= 1 or (if_count >= 2 and else_count >= 2):
        return "branching"

    return "linear"


# From Solution Heuristic: Case Split

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
    if if_count >= 1 and else_count >= 1 and elif_count == 0:
        return "binary"

    return "none"


# From Solution Heuristic: Auxiliary Construction

_STRUCTURAL_PATTERNS = [
    r"^\s*def\s+\w+\s*\(",        # function definitions
    r"^\s*class\s+\w+",           # class definitions
    r"\bdefaultdict\b",
    r"\bCounter\b",
    r"\bdeque\b",
    r"\bheapq\b",
]

_SKIP_VARS = frozenset((
    "_", "i", "j", "k", "n", "m", "x", "y", "f", "line", "ans", "result",
    "res", "ret", "output", "answer", "MOD", "mod", "INF", "inf",
))


def extract_auxiliary_construction(code: str) -> str:
    """Detect auxiliary constructions in solution code.
    
    Returns: "none" | "symbolic" | "structural"
    """
    if not code:
        return "none"
    if has_any_pattern(code, _STRUCTURAL_PATTERNS, flags=re.MULTILINE):
        return "structural"
    assignments = re.findall(
        r"^\s*([a-zA-Z_]\w*)\s*=(?!=)", code, re.MULTILINE,
    )
    meaningful = [v for v in assignments if v not in _SKIP_VARS]
    if len(meaningful) >= 3:
        return "symbolic"

    return "none"


# From Solution Heuristic: Reasoning Depth Proxy

def extract_reasoning_depth_proxy(code: str) -> str:
    """Estimate reasoning depth from code structure.
    
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


# From Solution Heuristic: Intermediate Reuse Proxy

def extract_intermediate_reuse_proxy(code: str) -> str:
    """Estimate intermediate-result reuse from code.
    
    Returns: "none" | "single" | "multiple"
    """
    if not code:
        return "none"

    lines = code.splitlines()
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


# Combined Heuristic Extraction

def extract_from_text_heuristic(fields: Dict[str, str]) -> Dict[str, Any]:
    """Extract from_text properties heuristically (objects, constraints, output_type)."""
    text = fields["text"]
    return {
        "objects": extract_objects(text),
        "constraints": extract_constraints(text),
        "output_type": extract_output_type(text),
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
    """Full heuristic extraction: domain + from_text + from_solution.
    
    Returns new payload dict with all heuristic fields populated.
    """
    payload_out = add_2nd_stage_domain(payload, h_threshold)
    fields = extract_fields(payload)

    ms = dict(payload_out.get("math_structure", {}))
    ms["from_text_heuristic"] = extract_from_text_heuristic(fields)
    ms["from_solution_heuristic"] = extract_from_solution_heuristic(fields)
    payload_out["math_structure"] = ms
    return payload_out
