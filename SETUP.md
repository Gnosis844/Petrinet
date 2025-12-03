# Quick Setup and Test Guide

## Step 1: Install Dependencies (1 minute)

```bash
cd "...\PetriNetBDDs"
pip install -r requirements.txt
```

If you get errors, install individually:
```bash
pip install lxml dd
```

## Step 2: Verify Installation (30 seconds)

```bash
python -c "from lxml import etree; from dd.autoref import BDD; print('✓ Ready to go!')"
```

## Step 3: Run Tests (1 minute)

```bash
cd src
python run_task3_experiments
```

You should see:
```
✓ ALL TESTS PASSED
  Both methods agree on reachable markings
  Task 3 (Symbolic BDD) integrates correctly with Tasks 1 & 2
```

## Step 4: Test Individual Components

### Test Task 1 (Parser)
```bash
python pnml_parser.py example.pnml
```

### Test Task 2 (Explicit)
```bash
python explicit.py
```

### Test Task 3 (Symbolic - YOUR CODE)
```bash
python symbolic.py
```

