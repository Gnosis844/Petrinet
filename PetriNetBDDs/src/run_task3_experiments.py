"""
Task 3 Experimental Results Generator
Run symbolic BDD analysis on multiple models and generate comparison data
"""

import time
from pnml_parser import PNModel
from symbolic import SymbolicAnalyzer


def run_experiment(filename):
    """Run Task 3 analysis on a single model and return metrics"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {filename}")
    print(f"{'='*70}")
    
    # Load model
    model = PNModel.load_pnml(filename)
    if not model:
        print("Failed to load model!")
        return None
    
    # Run symbolic analysis
    analyzer = SymbolicAnalyzer(model)
    results = analyzer.analyze()
    analyzer.print_results(results)
    
    return {
        'filename': filename,
        'places': len(model.places),
        'transitions': len(model.transitions),
        'arcs': len(model.arcs),
        'reachable_markings': results['num_markings'],
        'bdd_nodes': results['bdd_node_count'],
        'time_seconds': results['time_seconds']
    }


def print_experiment_summary(all_results):
    """Print a comprehensive summary table of all experiments"""
    print("\n" + "="*80)
    print("TASK 3 - SYMBOLIC BDD EXPERIMENTAL RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n{'Model':<20} {'Places':<8} {'Trans':<8} {'States':<10} {'BDD Nodes':<12} {'Time (s)':<12}")
    print("-" * 80)
    
    for r in all_results:
        print(f"{r['filename']:<20} {r['places']:<8} {r['transitions']:<8} "
              f"{r['reachable_markings']:<10} {r['bdd_nodes']:<12} {r['time_seconds']:<12.6f}")
    
    print("="*80)
    
    # Analysis
    print("\nKEY OBSERVATIONS:")
    print("-" * 80)
    
    # Find models with best BDD compression
    for r in all_results:
        if r['reachable_markings'] > 0:
            compression_ratio = r['reachable_markings'] / r['bdd_nodes'] if r['bdd_nodes'] > 0 else 1
            print(f"{r['filename']:<20} Compression: {compression_ratio:.2f}x "
                  f"({r['reachable_markings']} states in {r['bdd_nodes']} BDD nodes)")
    
    # Scalability
    print("\nSCALABILITY ANALYSIS:")
    print("-" * 80)
    for i, r in enumerate(all_results):
        if i > 0:
            prev = all_results[i-1]
            state_growth = r['reachable_markings'] / prev['reachable_markings'] if prev['reachable_markings'] > 0 else 0
            time_growth = r['time_seconds'] / prev['time_seconds'] if prev['time_seconds'] > 0 else 0
            print(f"{r['filename']:<20} State growth: {state_growth:.2f}x | Time growth: {time_growth:.2f}x")
    
    print("\n" + "="*80)


def generate_latex_table(all_results):
    """Generate LaTeX table for report"""
    print("\n\nLATEX TABLE FOR REPORT:")
    print("="*80)
    
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{Task 3: Symbolic BDD Reachability Analysis Results}")
    print("\\begin{tabular}{|l|c|c|c|c|c|}")
    print("\\hline")
    print("\\textbf{Model} & \\textbf{Places} & \\textbf{Trans.} & \\textbf{States} & \\textbf{BDD Nodes} & \\textbf{Time (s)} \\\\")
    print("\\hline")
    
    for r in all_results:
        print(f"{r['filename'].replace('_', '\\_'):<20} & {r['places']} & {r['transitions']} & "
              f"{r['reachable_markings']} & {r['bdd_nodes']} & {r['time_seconds']:.6f} \\\\")
        print("\\hline")
    
    print("\\end{tabular}")
    print("\\label{tab:task3_results}")
    print("\\end{table}")
    print("="*80)


def main():
    """Run all experiments for Task 3"""
    print("\n" + "="*80)
    print("TASK 3: SYMBOLIC BDD REACHABILITY ANALYSIS")
    print("Experimental Evaluation")
    print("="*80)
    
    # List of models to test (in order of complexity)
    test_models = [
        "example.pnml",           # Baseline: 2 states
        "chain_4.pnml",           # Simple: 4 states
        "mutex_2proc.pnml",       # Medium: ~20-30 states
        
    ]
    
    all_results = []
    
    # Run experiments
    for model_file in test_models:
        try:
            result = run_experiment(model_file)
            if result:
                all_results.append(result)
        except FileNotFoundError:
            print(f"⚠ Warning: {model_file} not found, skipping...")
        except Exception as e:
            print(f"✗ Error analyzing {model_file}: {e}")
    
    if not all_results:
        print("\n✗ No successful experiments!")
        return
    
    # Print summary
    print_experiment_summary(all_results)
    
    # Generate LaTeX table
    generate_latex_table(all_results)
    
    # Save results to file
    output_file = "task3_experimental_results.txt"
    with open(output_file, 'w') as f:
        f.write("TASK 3: SYMBOLIC BDD REACHABILITY ANALYSIS - EXPERIMENTAL RESULTS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"{'Model':<20} {'Places':<8} {'Trans':<8} {'States':<10} {'BDD Nodes':<12} {'Time (s)':<12}\n")
        f.write("-" * 80 + "\n")
        
        for r in all_results:
            f.write(f"{r['filename']:<20} {r['places']:<8} {r['transitions']:<8} "
                   f"{r['reachable_markings']:<10} {r['bdd_nodes']:<12} {r['time_seconds']:<12.6f}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write(f"\nTotal models tested: {len(all_results)}\n")
        f.write(f"Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\n✓ Results saved to: {output_file}")
    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
