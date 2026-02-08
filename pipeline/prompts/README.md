# Prompt Templates Directory

This directory contains all prompt templates used across the pipeline notebooks.

## Naming Convention

All prompt files follow the pattern: `nb{N}_{category}_{subcategory}.md`

Where:
- `{N}` = Notebook number (0, 2, 3, etc.)
- `{category}` = Main category (code, math_structure, etc.)
- `{subcategory}` = Specific purpose (generation, repair, verifier, etc.)

## File Inventory

### Notebook 0: Data Extraction and Code Generation
- `nb0_code_generation_base.md` - Base prompt for generating Python code from math problems
- `nb0_code_repair_timeout.md` - Repair prompt for timeout errors
- `nb0_code_repair_error.md` - Repair prompt for runtime errors
- `nb0_code_repair_wrong_answer.md` - Repair prompt for incorrect answers
- `nb0_code_verifier.md` - Verifier prompt for assessing code quality
- `nb0_code_repair_quality.md` - Repair prompt based on verifier feedback

### Notebook 2: Computation Bucket Classification
- `nb2_code_generation_simple.md` - Simple code generation prompt for bucket classification

### Notebook 3: Math Structure Extraction
- `nb3_math_structure_from_text.md` - Extract mathematical structure from problem text
- `nb3_math_structure_from_solution.md` - Extract reasoning patterns from solution code

## Template Variables

### Common Variables
- `{problem}` - The mathematical problem statement
- `{solution}` - The solution trace or reasoning (when available)
- `{code}` - Generated or previous code attempt
- `{expected_answer}` - Expected/correct answer
- `{predicted_answer}` - Actual output from code execution

### Error Repair Variables
- `{error}` - Error message or traceback
- `{timeout_seconds}` - Timeout duration
- `{previous_code}` - Code that failed
- `{wrong_answer}` - Incorrect answer produced
- `{base_prompt}` - Reference to base generation requirements

### Verifier Variables
- `{bad_signals}` - Quality issues identified by verifier

## Usage

### In Python Code
```python
from pathlib import Path

PROMPT_DIR = Path("prompts")
prompt_template = (PROMPT_DIR / "nb0_code_generation_base.md").read_text(encoding="utf-8")
formatted_prompt = prompt_template.format(problem=problem_text, solution=solution_text)
```

### In Notebooks
```python
# Load prompt template
PROMPT_DIR = Path("prompts")
BASE_PROMPT = (PROMPT_DIR / "nb0_code_generation_base.md").read_text(encoding="utf-8")

# Format with variables
formatted = BASE_PROMPT.format(problem="...", solution="...")
```

## Maintenance

When adding new prompts:
1. Follow the naming convention: `nb{N}_{category}_{subcategory}.md`
2. Document all template variables in the file header
3. Update this README with the new file
4. Use consistent formatting and structure
5. Test that all variable placeholders work correctly

When modifying prompts:
1. Update the file directly in this directory
2. Test changes in the corresponding notebook
3. Document any new variables or significant changes
4. Consider backward compatibility if used across multiple notebooks

## Archive

Unused or deprecated prompt files are moved to `../archive/` directory.
