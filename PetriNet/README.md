# Petri Net Analysis with BDD - Complete Implementation

A comprehensive implementation of formal methods for analyzing 1-safe Petri nets, featuring explicit and symbolic reachability analysis, deadlock detection, and optimization using Binary Decision Diagrams (BDDs) and Integer Linear Programming (ILP).

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Tasks Description](#tasks-description)
- [Installation](#installation)
- [Usage](#usage)
- [Test Cases](#test-cases)
- [Docker Support](#docker-support)
- [Dependencies](#dependencies)
- [Output Format](#output-format)
- [Architecture](#architecture)

---

## Overview

This project implements a complete Petri net analysis framework for **CO2011 - Mathematical Modeling** course. It provides both explicit and symbolic methods for analyzing 1-safe Petri nets, including:

- **PNML parsing** and model validation
- **Explicit reachability analysis** using BFS/DFS
- **Symbolic reachability analysis** using Binary Decision Diagrams (BDDs)
- **Deadlock detection** using ILP over reachable markings
- **Optimization** over reachable markings with BDD verification

The system processes standard PNML (Petri Net Markup Language) files and performs comprehensive analysis, comparing explicit and symbolic approaches, detecting deadlocks, and finding optimal markings.

---

## Features

### Core Capabilities

1. **Multi-format Input**: Supports standard PNML XML format
2. **Dual Analysis Methods**:
   - Explicit state enumeration (BFS)
   - Symbolic BDD-based analysis
3. **Automatic Comparison**: Validates consistency between explicit and symbolic results
4. **Deadlock Detection**: ILP-based deadlock finding with BDD integration
5. **Optimization**: Finds optimal reachable markings with objective functions
6. **Comprehensive Testing**: 37+ test cases covering all scenarios
7. **Batch Processing**: Automatically discovers and runs all test cases
8. **Detailed Reporting**: Generates comprehensive analysis reports

### Key Advantages

- **Memory Efficiency**: BDD representation handles large state spaces efficiently
- **Verification**: Cross-validation between explicit and symbolic methods
- **Extensibility**: Modular design allows easy extension
- **Robustness**: Comprehensive error handling and validation

---

## Project Structure

```
 PetriNet/
    ├── Dockerfile              # Multi-stage Docker build configuration
    ├── .dockerignore          # Docker build optimization
    ├── README.md               # This file
    ├── requirements.txt       # Python dependencies
    └── src/
        ├── main.py            # Main entry point (Tasks 1-5 integration)
        ├── model.py           # Core data structures (Place, Transition, PNModel)
        ├── task1_PnmlParsing/
        │   ├── __init__.py
        │   └── pnml_parser.py # PNML file parser
        ├── task2_ExplicitReachability/
        │   ├── __init__.py
        │   └── explicit_reachability.py # BFS-based explicit analysis
        ├── task3_BddBasedReachability/
        │   ├── __init__.py
        │   └── bdd_reachability.py # Symbolic BDD analysis
        ├── task4_IlpBddDeadlockDetection/
        │   ├── __init__.py
        │   └── deadlock_detection.py # ILP-based deadlock detection
        ├── task5_ReachableOptimization/
        │   ├── __init__.py
        │   └── optimization.py # Optimization with BDD verification
        └── testcases/         # 37+ test case files
            ├── test_task1_*.pnml
            ├── test_task2_*.pnml
            ├── test_task3_*.pnml
            ├── test_task4_*.pnml
            ├── test_task5_*.pnml
            ├── test_integration_*.pnml
            └── test_invalid_*.pnml
```

---

## Tasks Description

### Task 1: PNML Parsing and Validation

**Purpose**: Read and parse standard PNML files, construct internal representation, and verify consistency.

**Implementation**:

- Parses XML-based PNML format
- Extracts places, transitions, and arcs
- Builds internal `PNModel` representation
- Validates consistency (no missing arcs or nodes)
- Handles initial markings (1-safe nets: 0 or 1 token per place)

**Key Features**:

- Robust XML parsing with namespace handling
- Comprehensive error detection
- Support for standard PNML 2009 format

**Files**: `task1_PnmlParsing/pnml_parser.py`, `model.py`

---

### Task 2: Explicit Reachability Analysis

**Purpose**: Enumerate all reachable markings using breadth-first search (BFS).

**Implementation**:

- BFS traversal of state space
- Marks transitions as enabled/disabled
- Fires transitions to compute successor markings
- Detects deadlock markings (no enabled transitions)
- Returns complete reachability graph

**Key Features**:

- Efficient state enumeration
- Deadlock detection
- Detailed transition firing information
- Performance metrics (time, state count)

**Files**: `task2_ExplicitReachability/explicit_reachability.py`

**Algorithm**:

```
1. Initialize queue with initial marking M0
2. While queue not empty:
   a. Pop marking M
   b. For each transition t:
      - If enabled in M, fire t to get M'
      - If M' not visited, add to queue
3. Return all visited markings
```

---

### Task 3: Symbolic BDD Reachability Analysis

**Purpose**: Compute reachable markings symbolically using Binary Decision Diagrams (BDDs).

**Implementation**:

- Encodes markings as BDD variables (one per place)
- Uses fixed-point iteration to compute reachable set
- Symbolic image computation for transitions
- Compares with explicit method for verification

**Key Features**:

- Memory-efficient for large state spaces
- Automatic BDD variable management
- Fixed-point detection
- State space enumeration (when feasible)

**Files**: `task3_BddBasedReachability/bdd_reachability.py`

**Algorithm**:

```
1. Initialize BDD variables for each place
2. Encode initial marking M0 as BDD
3. While not fixed point:
   a. Compute image of current reachable set
   b. Union with existing set
   c. Check for fixed point
4. Return BDD representing all reachable markings
```

**Advantages**:

- Handles exponentially large state spaces
- Compact representation
- Efficient set operations

---

### Task 4: Deadlock Detection using ILP and BDD

**Purpose**: Detect reachable deadlock markings using Integer Linear Programming.

**Implementation**:

- Uses reachable markings from Task 2 or Task 3
- Formulates deadlock detection as ILP problem
- Selects one marking from reachable set
- Constrains that no transition is enabled
- Returns one deadlock if exists

**Key Features**:

- Works with both explicit and symbolic reachable sets
- Efficient ILP formulation
- Cross-validates with explicit deadlock detection

**Files**: `task4_IlpBddDeadlockDetection/deadlock_detection.py`

**ILP Formulation**:

```
Variables:
  - y_i ∈ {0,1}: selector for reachable marking i
  - M_p ∈ {0,1}: marking of place p

Constraints:
  - Σ_i y_i = 1 (select exactly one marking)
  - M_p = Σ_i y_i * marking_i[p] (link marking to selection)
  - For each transition t: Σ_{p∈pre(t)} M_p ≤ |pre(t)| - 1 (deadlock)

Objective: None (feasibility problem)
```

---

### Task 5: Optimization over Reachable Markings

**Purpose**: Find optimal reachable marking maximizing a linear objective function.

**Implementation**:

- Uses state equation: M = M0 + A·σ
- ILP optimization with BDD verification
- Iterative no-good cuts for unreachable solutions
- Returns optimal reachable marking

**Key Features**:

- Flexible objective functions
- BDD-based reachability verification
- Handles cases where ILP optimum is unreachable
- Automatic cut generation

**Files**: `task5_ReachableOptimization/optimization.py`

**Algorithm**:

```
1. Build incidence matrix A = Post - Pre
2. Solve ILP: max c^T M subject to M = M0 + A·σ
3. While ILP solution exists:
   a. Check if solution is reachable (via BDD)
   b. If reachable: return optimal marking
   c. If not: add no-good cut, re-solve
4. Return None if no reachable optimum found
```

**Objective Functions**:

- Default: maximize total tokens (c_p = 1 for all places)
- Mutex nets: weighted (CS places: 10, Request: 2, Others: 1)
- Custom: user-defined weight vectors

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Docker for containerized execution

### Step 1: Navigate to Project Directory

```bash
cd /path/to/Petrinet
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**System Dependencies** (for `lxml` on Linux):

```bash
# Ubuntu/Debian
sudo apt-get install build-essential libxml2-dev libxslt1-dev python3-dev

# Fedora/CentOS
sudo yum install gcc libxml2-devel libxslt1-devel python3-devel
```

### Step 4: Verify Installation

```bash
cd src
python -c "from lxml import etree; from dd.autoref import BDD; import pulp; import numpy; print(' All dependencies installed!')"
```

---

## Usage

### Basic Usage

Run all valid test cases (default behavior):

```bash
cd src
python main.py
```

This will:

- Discover all valid test cases in `testcases/` directory
- Run Tasks 1-5 on each test case
- Generate `results.txt` with complete analysis
- Display summary table in console

### Command-Line Options

```bash
# Run specific test files
python main.py testcases/test_task2_valid_simple.pnml testcases/test_task3_valid_large.pnml

# Filter by task type
python main.py --filter-type task2        # Only Task 2 tests
python main.py --filter-type task4       # Only Task 4 tests
python main.py --filter-type integration # Only integration tests

# Include invalid test cases
python main.py --include-invalid

# Custom output file
python main.py --output my_results.txt

# Quiet mode (file only, no console output)
python main.py --quiet

# Custom testcases directory
python main.py --testcases-dir my_testcases
```

### Advanced Examples

```bash
# Run only integration tests and save to file
python main.py --filter-type integration --output integration_results.txt

# Run all tests quietly (background processing)
python main.py --quiet --output batch_results.txt

# Run specific test with detailed output
python main.py testcases/test_integration_mutex_2processes.pnml
```

---

## Test Cases

The project includes **37+ comprehensive test cases** organized by task:

### Task 1 Tests (PNML Parsing)

**Valid Tests**:

- `test_task1_valid_empty_net.pnml` - Empty net (no places/transitions)
- `test_task1_valid_single_place.pnml` - Single place with token
- `test_task1_valid_isolated_transition.pnml` - Isolated transition
- `test_task1_valid_multiple_initial_tokens.pnml` - Multiple initial tokens

**Invalid Tests** (for error handling):

- `test_task1_invalid_malformed_xml.pnml` - Malformed XML
- `test_task1_invalid_invalid_initial_marking.pnml` - Non-1-safe marking
- `test_task1_invalid_self_loop_place.pnml` - Invalid place-to-place arc
- `test_task1_invalid_missing_source_node.pnml` - Missing source node
- `test_task1_invalid_missing_target_node.pnml` - Missing target node
- And more...

### Task 2 Tests (Explicit Reachability)

- `test_task2_valid_chain_4places.pnml` - Sequential chain (4 states)
- `test_task2_valid_cycle_3states.pnml` - Cycle pattern (3 states)
- `test_task2_valid_branch_merge.pnml` - Branch and merge
- `test_task2_valid_fork_join.pnml` - Fork-join pattern
- `test_task2_valid_parallel_independent.pnml` - Independent parallel processes
- `test_task2_valid_producer_consumer_cycle.pnml` - Producer-consumer cycle

### Task 3 Tests (BDD Reachability)

- `test_task3_valid_large_state_space.pnml` - Large state space (32 states)
- `test_task3_valid_symmetric_net.pnml` - Symmetric net (BDD compression)

### Task 4 Tests (Deadlock Detection)

- `test_task4_valid_deadlock_simple.pnml` - Simple deadlock
- `test_task4_valid_no_deadlock.pnml` - No deadlock (infinite cycle)
- `test_task4_valid_multiple_deadlocks.pnml` - Multiple deadlock states
- `test_task4_valid_deadlock_reachable.pnml` - Reachable deadlock
- `test_task4_valid_deadlock_after_cycle.pnml` - Deadlock after cycle

### Task 5 Tests (Optimization)

- `test_task5_valid_optimization_simple.pnml` - Simple optimization
- `test_task5_valid_optimization_cycle.pnml` - Optimization with cycles
- `test_task5_valid_optimization_no_solution.pnml` - No reachable solution
- `test_task5_valid_optimization_conflict.pnml` - Conflicting objectives

### Integration Tests

- `test_integration_complex_workflow.pnml` - Complex workflow
- `test_integration_dining_philosophers.pnml` - Dining philosophers (2 philosophers)
- `test_integration_mutex_2processes.pnml` - Mutex with 2 processes
- `test_integration_producer_consumer_buffer.pnml` - Producer-consumer with buffer

### Naming Convention

Test files follow the pattern:

- `test_<task>_<validity>_<description>.pnml` for task-specific tests
- `test_integration_<description>.pnml` for integration tests
- `test_invalid_<error_type>.pnml` for invalid/error tests

---

## Docker Support

### Build Docker Image

**Option 1: Build from PetriNet directory (recommended)**

```bash
cd PetriNet
docker build -t petrinet-analysis .
```

**Option 2: Build from root directory**

```bash
# From Petrinet/ root directory
docker build -f PetriNet/Dockerfile -t petrinet-analysis PetriNet/
```

### Run Container

```bash
# Run all tests (default)
docker run --rm petrinet-analysis

# Run with custom options
docker run --rm petrinet-analysis python src/main.py --filter-type task2

# Run and save results to host
docker run --rm -v $(pwd)/results:/app/results petrinet-analysis python src/main.py --output results/analysis.txt

# Quiet mode
docker run --rm petrinet-analysis python src/main.py --quiet
```

### Docker Features

- **Multi-stage build**: Optimized image size
- **Pre-installed dependencies**: No setup required
- **Isolated environment**: Consistent execution
- **Volume mounting**: Easy result extraction

---

## Dependencies

### Core Dependencies

| Package | Version | Purpose                                  |
| ------- | ------- | ---------------------------------------- |
| `lxml`  | ≥5.3.0  | PNML XML parsing (Task 1)                |
| `dd`    | ≥0.5.6  | Binary Decision Diagrams (Task 3)        |
| `pulp`  | ≥2.8.0  | Integer Linear Programming (Tasks 4 & 5) |
| `numpy` | ≥1.24.0 | Matrix operations (Task 5)               |

### Standard Library

- `argparse` - Command-line argument parsing
- `pathlib` - Path manipulation
- `typing` - Type hints
- `collections` - Data structures (deque)
- `dataclasses` - Data classes
- `datetime` - Timestamp generation

---

## Output Format

### Console Output

The program displays:

- Per-model analysis results
- Task-by-task progress
- Comparison between explicit and symbolic methods
- Deadlock detection results
- Optimization results
- Global summary table

### File Output

Results are saved to `results.txt` (or custom filename) containing:

1. **Header**: Timestamp, configuration
2. **Per-Model Analysis**:
   - Task 1: Parsing results
   - Task 2: Explicit reachability (states, deadlocks, time)
   - Task 3: BDD reachability (states, BDD nodes, time)
   - Comparison: Task 2 vs Task 3
   - Task 4: Deadlock detection results
   - Task 5: Optimization results
3. **Global Summary Table**: Aggregated statistics

### Summary Table Columns

| Column    | Description                    |
| --------- | ------------------------------ |
| Model     | Test case filename             |
| P         | Number of places               |
| T         | Number of transitions          |
| T2_States | Explicit reachable markings    |
| T2_Dead   | Explicit deadlock count        |
| T3_States | BDD reachable markings         |
| BDD_Nodes | BDD node count                 |
| T2=T3?    | Reachable sets equal?          |
| DeadEq?   | Deadlock sets equal?           |
| T4_OK?    | ILP deadlock matches explicit? |
| T5_Obj    | Optimal objective value        |

---

## Architecture

### Design Principles

1. **Modularity**: Each task is a separate module
2. **Separation of Concerns**: Parsing, analysis, and reporting are separated
3. **Extensibility**: Easy to add new analysis methods
4. **Validation**: Cross-validation between methods

### Data Flow

```
PNML File
    ↓
[Task 1] Parser → PNModel
    ↓
[Task 2] Explicit Analysis → Reachable Markings (Set)
    ↓
[Task 3] BDD Analysis → Reachable Markings (BDD)
    ↓
[Comparison] Validate Consistency
    ↓
[Task 4] ILP Deadlock Detection → Deadlock Marking (if exists)
    ↓
[Task 5] Optimization → Optimal Marking (if exists)
    ↓
Report Generation
```

### Key Classes

- **`PNModel`**: Internal representation of Petri net
- **`Place`**: Place with marking information
- **`Transition`**: Transition with input/output places
- **`SymbolicAnalyzer`**: BDD-based analysis engine
- **`DeadlockTransition`**: Transition representation for ILP
- **`Marking`**: Type alias for `FrozenSet[str]` (marked place IDs)

---

## Example Output

```
================================================================================
Petri Net Analysis - Tasks 1-5
Started at: 2024-12-15 14:30:22
Output file: results.txt
================================================================================

Discovered 30 test case(s) from testcases:

MODEL: test_task2_valid_simple.pnml
================================================================================
[Task 1] Parsed model: 2 places, 1 transitions, 2 arcs
[Task 2] Reachable markings: 2
[Task 2] Deadlock markings: 1
[Task 3] Reachable markings (BDD): 2
[Task 3] BDD node count: 3
[Compare Task 2 vs Task 3]
  Reachable sets equal?   True
  #Deadlocks (Task 2):    1
  #Deadlocks (from BDD):  1
  Deadlock sets equal?    True
[Task 4] ILP-based deadlock detection...
  ILP found reachable deadlock (using BDD (Task 3))
[Task 5] Optimization max c^T M over Reach(M0)...
  Optimal reachable marking M*: {'P2': 1, 'P1': 0}
  Max objective value c^T M*: 1

================================================================================
GLOBAL SUMMARY (Tasks 2, 3, 4, 5)
================================================================================
Model                  P   T  T2_States  T2_Dead  T3_States  BDD_Nodes  T2=T3? DeadEq?  T4_OK?  T5_Obj
test_task2_valid_simple 2   1          2        1          2          3    True    True    True        1
...
```

---

## Development

### Adding New Test Cases

1. Create `.pnml` file in `testcases/` directory
2. Follow naming convention: `test_<category>_<description>.pnml`
3. Run: `python main.py` to include in analysis

### Extending Functionality

- **New Analysis Method**: Add module in `src/taskX_*/`
- **Custom Objective**: Modify `optimize_reachable()` in Task 5
- **Additional Validation**: Extend `PNModel.validate()`

---
