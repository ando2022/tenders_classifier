"""
Migrate Historical Experiments to MLflow

This script imports previously run experiments from:
- results/prompt_comparison_*.json
- EXPERIMENT_LOG.md (manual documentation)

Into MLflow for unified tracking.
"""
import json
import mlflow
from pathlib import Path
from datetime import datetime


def migrate_prompt_comparison_experiments(comparison_file: Path):
    """Migrate experiments from prompt_comparison JSON files."""
    print(f"\n📥 Migrating from: {comparison_file}")
    
    with open(comparison_file) as f:
        experiments = json.load(f)
    
    mlflow.set_experiment("tender_classification")
    
    for exp in experiments:
        run_name = f"historical_{exp['version'].replace(' ', '_').lower()}"
        
        print(f"\n  Migrating: {exp['version']}")
        
        with mlflow.start_run(run_name=run_name):
            # Set tags
            mlflow.set_tag("migrated", "true")
            mlflow.set_tag("original_source", str(comparison_file))
            mlflow.set_tag("description", f"Historical experiment: {exp['version']}")
            mlflow.set_tag("experiment_type", "prompt_comparison")
            
            # Log timestamp
            try:
                timestamp = datetime.fromisoformat(exp['timestamp'])
                mlflow.set_tag("original_timestamp", exp['timestamp'])
            except:
                timestamp = datetime.now()
            
            # Log parameters
            mlflow.log_param("prompt_path", exp.get('prompt_path', 'unknown'))
            mlflow.log_param("input.use_full_text", exp.get('use_full_text', False))
            mlflow.log_param("test_cases", exp.get('test_cases', 0))
            mlflow.log_param("errors", exp.get('errors', 0))
            mlflow.log_param("version_name", exp.get('version', 'unknown'))
            
            # Log metrics
            mlflow.log_metric("accuracy", exp.get('accuracy', 0))
            mlflow.log_metric("precision", exp.get('precision', 0))
            mlflow.log_metric("recall", exp.get('recall', 0))
            mlflow.log_metric("f1_score", exp.get('f1_score', 0))
            mlflow.log_metric("tp", exp.get('tp', 0))
            mlflow.log_metric("fp", exp.get('fp', 0))
            mlflow.log_metric("tn", exp.get('tn', 0))
            mlflow.log_metric("fn", exp.get('fn', 0))
            
            print(f"    ✓ Logged metrics: Acc={exp['accuracy']:.1%}, "
                  f"Prec={exp['precision']:.1%}, Rec={exp['recall']:.1%}")


def create_manual_experiments_from_log():
    """Create placeholder runs for manually documented experiments."""
    print("\n📝 Creating entries for manually documented experiments")
    
    mlflow.set_experiment("tender_classification")
    
    # Experiment #1: Conservative (from EXPERIMENT_LOG.md)
    with mlflow.start_run(run_name="historical_exp1_conservative"):
        mlflow.set_tag("migrated", "true")
        mlflow.set_tag("original_source", "EXPERIMENT_LOG.md")
        mlflow.set_tag("description", "Experiment #1: Initial Conservative Prompt")
        mlflow.set_tag("original_timestamp", "2024-10-08")
        mlflow.set_tag("experiment_type", "manual_log")
        mlflow.set_tag("status", "failed")
        
        mlflow.log_param("prompt_version", "v1_conservative")
        mlflow.log_param("input.use_full_text", False)
        mlflow.log_param("test_cases", 10)
        mlflow.log_param("notes", "Too conservative - rejected ALL positives")
        
        # Metrics (from log)
        mlflow.log_metric("accuracy", 0.80)
        mlflow.log_metric("precision", 0)  # N/A - no predictions
        mlflow.log_metric("recall", 0.0)
        mlflow.log_metric("f1_score", 0.0)
        mlflow.log_metric("tp", 0)
        mlflow.log_metric("fp", 0)
        mlflow.log_metric("tn", 8)
        mlflow.log_metric("fn", 2)
        
        print("  ✓ Experiment #1 (Conservative) - FAILED")
    
    # Experiment #2: Balanced (from EXPERIMENT_LOG.md)
    with mlflow.start_run(run_name="historical_exp2_balanced"):
        mlflow.set_tag("migrated", "true")
        mlflow.set_tag("original_source", "EXPERIMENT_LOG.md")
        mlflow.set_tag("description", "Experiment #2: Balanced Prompt (50 cases)")
        mlflow.set_tag("original_timestamp", "2024-10-08")
        mlflow.set_tag("experiment_type", "manual_log")
        mlflow.set_tag("status", "success")
        
        mlflow.log_param("prompt_version", "v2_balanced")
        mlflow.log_param("input.use_full_text", False)
        mlflow.log_param("test_cases", 50)
        mlflow.log_param("notes", "Much better! 92% accuracy. Ready for production testing.")
        
        # Metrics (from log)
        mlflow.log_metric("accuracy", 0.92)
        mlflow.log_metric("precision", 0.952)
        mlflow.log_metric("recall", 0.87)
        mlflow.log_metric("f1_score", 0.909)
        mlflow.log_metric("tp", 20)
        mlflow.log_metric("fp", 1)
        mlflow.log_metric("tn", 26)
        mlflow.log_metric("fn", 3)
        
        print("  ✓ Experiment #2 (Balanced) - SUCCESS")


def main():
    base = Path(__file__).parent.parent
    
    # Set up MLflow
    mlflow_dir = base / "mlruns"
    mlflow_dir.mkdir(exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{mlflow_dir}/mlflow.db")
    
    print("="*80)
    print("MIGRATING HISTORICAL EXPERIMENTS TO MLFLOW")
    print("="*80)
    
    # Migrate from JSON comparison files
    results_dir = base / "results"
    if results_dir.exists():
        for json_file in results_dir.glob("prompt_comparison_*.json"):
            try:
                migrate_prompt_comparison_experiments(json_file)
            except Exception as e:
                print(f"  ✗ Error migrating {json_file.name}: {e}")
    
    # Create entries for manually documented experiments
    try:
        create_manual_experiments_from_log()
    except Exception as e:
        print(f"  ✗ Error creating manual entries: {e}")
    
    print("\n" + "="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print("\nYou can now view all experiments (historical + new) in MLflow UI:")
    print(f"  mlflow ui --backend-store-uri sqlite:///{mlflow_dir}/mlflow.db")
    print("  Then open: http://localhost:5000")
    print("\nHistorical experiments are tagged with 'migrated=true'")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

