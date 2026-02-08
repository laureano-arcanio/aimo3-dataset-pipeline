# AIMO3 Dataset Pipeline

A production pipeline for processing mathematical problems into high-quality training datasets. The pipeline extracts problems from databases, generates solutions via LLM, classifies difficulty and structure, filters for quality, and produces labeled datasets ready for model training.

## Pipeline Stages

### 0. Data Extraction from Sources

**Problem:** Raw mathematical problems need executable solutions with verified answers.

**Process:** Queries source databases, filters by domain, deduplicates, then uses LLM to generate Python code that solves each problem. Handles execution failures through iterative repair (timeouts, errors, wrong answers).

**Input:** Database queries, problem statements  
**Output:** JSONL with problems, working code solutions, execution results

**Value:** Creates the foundation dataset with verified computational solutions rather than just text answers.

---

### 2. Bucket Classification

**Problem:** Training requires problems stratified by computational difficulty, not just mathematical complexity.

**Process:** Tests each problem against a series of increasingly capable models (0.5B to 20B+ parameters). Assigns difficulty bucket based on which models can solve it. Early exits when solved to save compute.

**Input:** Dataset from stage 0  
**Output:** Same dataset enriched with `computation_buckets` field

**Value:** Enables curriculum learning and difficulty-based sampling. Identifies problems that challenge even large models.

---

### 3. Math Structure Extraction

**Problem:** Understanding what makes problems hard requires structured mathematical metadata beyond difficulty scores.

**Process:** Uses LLM to analyze problems from two angles: the problem statement itself (domain, objects, constraints) and the solution approach (reasoning patterns, case analysis, construction techniques).

**Input:** Dataset from stage 2  
**Output:** Dataset enriched with `math_structure` field containing domain, reasoning patterns, depth

**Value:** Enables fine-grained filtering, balancing datasets by mathematical content, and analyzing model weaknesses in specific reasoning types.

---

### 4. Heuristic Math Classifier

**Problem:** LLM-based classification is slow and expensive for large datasets.

**Process:** Pattern matching on problem text and code using keyword scoring and hard rules. Can run standalone or as a fast pre-filter before LLM classification.

**Input:** Problem payload (text, code, plan)  
**Output:** Domain classification (algebra, number_theory, combinatorics, geometry)

**Value:** 100x faster than LLM classification. Useful for quick filtering and catching obvious cases without API costs.

---

### 5. Leak Detection

**Problem:** Generated code sometimes hardcodes answers rather than computing them, making problems useless for training.

**Process:** Scans code for suspicious patterns (string matching, hardcoded values). Flags potential leaks for LLM verification and attempts automated repair.

**Input:** Dataset from stage 3  
**Output:** Dataset filtered for quality, leaks removed or repaired

**Value:** Ensures models learn computational reasoning rather than pattern matching. Critical for training data integrity.

---

### 6. Effective Difficulty Levels

**Problem:** Need continuous difficulty scores for fine-grained curriculum design.

**Process:** Computes effective difficulty from bucket classifications and model solve rates.

**Input:** Dataset with computation_buckets  
**Output:** Dataset with normalized difficulty scores

**Value:** Enables smooth difficulty progression in training rather than discrete jumps.

---

### 7. Normalization

**Problem:** Raw data has inconsistent formatting, field naming, and structure across sources.

**Process:** Standardizes field names, formats, numerical representations, and text encoding.

**Input:** Dataset from stage 6  
**Output:** Normalized dataset with consistent schema

**Value:** Simplifies downstream processing and model training. Ensures reproducibility.

---

### 8. Dataset Filtering and Splitting

**Problem:** Need clean train/test splits that respect problem similarity and prevent leakage.

**Process:** Applies quality filters, removes outliers, splits into train/validation/test sets using stratified sampling by difficulty and domain.

**Input:** Normalized dataset from stage 7  
**Output:** Train, validation, and test JSONL files

**Value:** Produces final datasets ready for training with proper evaluation protocol.

---

### 9. EDA and Charts

**Problem:** Understanding dataset characteristics requires visualization.

**Process:** Generates statistical summaries and plots: difficulty distributions, domain balance, solution length patterns, error analysis.

**Input:** Final datasets from stage 8  
**Output:** Charts and summary statistics

**Value:** Validates dataset quality and informs hyperparameter choices for training.

---

### 10. Model Evaluation

**Problem:** Need to measure model performance across different difficulty levels and domains.

**Process:** Runs inference on test set, computes metrics by bucket and domain, identifies failure patterns.

**Input:** Test dataset, trained model  
**Output:** Performance metrics, failure analysis

**Value:** Quantifies model capabilities and guides further data collection or training adjustments.

---

### 11. Model Training

**Problem:** Fine-tuning mathematical reasoning models on custom datasets.

**Process:** Fine-tunes Qwen models using prepared datasets with appropriate hyperparameters for mathematical reasoning tasks.

**Input:** Train/validation datasets from stage 8  
**Output:** Fine-tuned model checkpoints

**Value:** Produces specialized models trained on high-quality, difficulty-stratified mathematical problems.

---

## Dependencies

**Core Requirements:**
```bash
pip install -r requirements.txt
```

Includes: pandas, numpy, tqdm, anyio, httpx, tenacity, jupyter, scikit-learn, matplotlib, seaborn

**Optional Requirements:**
- Development tools: `pip install -r requirements-dev.txt`
- Model training (GPU required): `pip install -r requirements-training.txt`

**Verify Installation:**
```bash
python verify_install.py
```

See INSTALLATION.md for detailed setup instructions and platform-specific notes.

---

## Utilities

**Location:** `pipeline/utils/`

**LLMPool** - Async LLM client with bounded concurrency, retry logic, and timeout handling.

**RuntimeConfig** - Hot-reloadable JSON configuration for live parameter updates during long runs.

**Import:**
```python
from utils import LLMPool, RuntimeConfig
```

See `pipeline/utils/README.md` for API details.

---

## Configuration

Edit `pipeline/config.json` to adjust:
- Retry counts for execution and API failures
- Timeout values for code execution and LLM requests
- Concurrency limits for parallel processing

Changes are picked up automatically during execution.

---

## Running the Pipeline

1. Install dependencies: `pip install -r requirements.txt`
2. Configure API endpoints in notebook cells
3. Run stages sequentially: 0 → 2 → 3 → 5 → 6 → 7 → 8
4. Optionally: 9 for analysis, 10 for evaluation, 11 for training
5. Use stage 4 as alternative to stage 3 when speed matters more than precision

Each stage writes JSONL files that become input for the next stage.

---

## Conclusions

This pipeline transforms raw mathematical problems into training-ready datasets with:

1. **Verified solutions** - All problems have working, tested code
2. **Difficulty stratification** - Problems labeled by computational complexity
3. **Rich metadata** - Mathematical structure, reasoning patterns, domain labels
4. **Quality assurance** - Leak detection, deduplication, normalization
5. **Proper splits** - Train/test separation that prevents data leakage

The result is a dataset suitable for training mathematical reasoning models with curriculum learning, fine-grained evaluation, and analysis of specific reasoning capabilities.

The pipeline is production-ready: it handles failures gracefully, checkpoints progress, processes data in parallel, and allows live configuration updates. It has been used to process thousands of problems and is actively maintained.
