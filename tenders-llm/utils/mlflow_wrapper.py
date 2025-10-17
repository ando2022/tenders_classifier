"""
MLflow Wrapper for Tenders-LLM
Integrates experiment_tracker with MLflow for comprehensive tracking
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import mlflow
from .experiment_tracker import (
    create_experiment_config,
    print_config_summary,
    save_experiment_config,
    compare_configs
)


class TenderMLflowTracker:
    """Wrapper for MLflow that tracks all experiment dependencies."""
    
    def __init__(self, base_dir: Path, mlflow_tracking_uri: Optional[str] = None):
        """
        Initialize MLflow tracker.
        
        Args:
            base_dir: Base directory of the project (tenders-llm/)
            mlflow_tracking_uri: MLflow tracking URI (default: local sqlite)
        """
        self.base_dir = Path(base_dir)
        
        # Set MLflow tracking URI
        if mlflow_tracking_uri is None:
            mlflow_dir = self.base_dir / "mlruns"
            mlflow_dir.mkdir(exist_ok=True)
            mlflow_tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
        
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        # Set experiment name
        mlflow.set_experiment("tender_classification")
        
        self.current_run = None
        self.current_config = None
    
    def start_run(
        self,
        experiment_name: str,
        description: str = "",
        use_full_text: bool = False,
        model_config: Optional[Dict] = None,
        input_config: Optional[Dict] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Start a new MLflow run with comprehensive tracking.
        
        Args:
            experiment_name: Name of the experiment (e.g., "exp_services_v2")
            description: Human-readable description
            use_full_text: Whether to use full tender text
            model_config: Model configuration dict
            input_config: Input processing configuration dict
            tags: Additional tags for the run
        """
        # Create comprehensive config
        self.current_config = create_experiment_config(
            base_dir=self.base_dir,
            experiment_name=experiment_name,
            description=description,
            use_full_text=use_full_text,
            model_config=model_config,
            input_config=input_config
        )
        
        # Print summary
        print_config_summary(self.current_config)
        
        # Save config to experiments directory
        exp_dir = self.base_dir / "experiments" / experiment_name
        save_experiment_config(self.current_config, exp_dir)
        
        # Start MLflow run
        self.current_run = mlflow.start_run(run_name=experiment_name)
        
        # Log all parameters
        self._log_all_params()
        
        # Log tags
        if tags:
            mlflow.set_tags(tags)
        
        mlflow.set_tag("description", description)
        mlflow.set_tag("experiment_name", experiment_name)
        
        return self
    
    def _log_all_params(self):
        """Log all configuration parameters to MLflow."""
        config = self.current_config
        
        # Data parameters
        mlflow.log_param("data.total_tenders", config['data']['tenders_total'])
        mlflow.log_param("data.positive_tenders", config['data']['tenders_positive'])
        mlflow.log_param("data.positive_rate", config['data']['positive_rate'])
        mlflow.log_param("data.train_size", config['data']['train_size'])
        mlflow.log_param("data.val_size", config['data']['val_size'])
        mlflow.log_param("data.test_size", config['data']['test_size'])
        mlflow.log_param("data.data_hash", config['data']['data_hash'])
        mlflow.log_param("data.date_range", config['data']['date_range'])
        
        # Services parameters
        mlflow.log_param("services.exists", config['services']['exists'])
        if config['services']['exists']:
            mlflow.log_param("services.count", config['services']['services_count'])
            mlflow.log_param("services.hash", config['services']['services_hash'])
            mlflow.log_param("services.file", config['services']['source_file'])
        
        # Keywords parameters
        mlflow.log_param("keywords.exists", config['keywords']['exists'])
        if config['keywords']['exists']:
            mlflow.log_param("keywords.count", config['keywords']['keywords_count'])
            mlflow.log_param("keywords.hash", config['keywords']['keywords_hash'])
        
        # Prompt parameters
        if config['prompt']['exists']:
            mlflow.log_param("prompt.hash", config['prompt']['prompt_hash'])
            mlflow.log_param("prompt.length_chars", config['prompt']['prompt_length_chars'])
            mlflow.log_param("prompt.estimated_examples", config['prompt']['estimated_examples'])
        
        # Input config
        for key, value in config['input'].items():
            mlflow.log_param(f"input.{key}", value)
        
        # Model config
        for key, value in config['model'].items():
            mlflow.log_param(f"model.{key}", value)
    
    def log_artifacts(self):
        """Log key files as artifacts."""
        config = self.current_config
        
        # Log prompt file
        if config['prompt']['exists']:
            prompt_file = Path(config['prompt']['prompt_file'])
            if prompt_file.exists():
                mlflow.log_artifact(str(prompt_file), "prompt")
        
        # Log services file
        if config['services']['exists']:
            services_file = Path(config['services']['source_file'])
            if services_file.exists():
                mlflow.log_artifact(str(services_file), "services")
        
        # Log keywords file
        if config['keywords']['exists']:
            keywords_file = Path(config['keywords']['source_file'])
            if keywords_file.exists():
                mlflow.log_artifact(str(keywords_file), "keywords")
        
        # Log experiment config
        exp_dir = self.base_dir / "experiments" / config['experiment_name']
        config_file = exp_dir / "experiment_config.json"
        if config_file.exists():
            mlflow.log_artifact(str(config_file), "config")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log evaluation metrics."""
        mlflow.log_metrics(metrics, step=step)
    
    def log_predictions(self, predictions_file: Path, artifact_name: str = "predictions"):
        """Log predictions file as artifact."""
        if predictions_file.exists():
            mlflow.log_artifact(str(predictions_file), artifact_name)
    
    def log_pr_curve(self, pr_curve_file: Path):
        """Log PR curve image."""
        if pr_curve_file.exists():
            mlflow.log_artifact(str(pr_curve_file), "plots")
    
    def log_cost(self, api_cost_usd: float, n_requests: int):
        """Log API costs."""
        mlflow.log_metric("api_cost_usd", api_cost_usd)
        mlflow.log_metric("n_api_requests", n_requests)
        mlflow.log_metric("cost_per_request", api_cost_usd / n_requests if n_requests > 0 else 0)
    
    def end_run(self, status: str = "FINISHED"):
        """End the current MLflow run."""
        if self.current_run:
            mlflow.end_run(status=status)
            self.current_run = None
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        if exc_type is not None:
            self.end_run(status="FAILED")
        else:
            self.end_run(status="FINISHED")
        return False


def compare_experiments(base_dir: Path, exp_name1: str, exp_name2: str):
    """Compare two experiments and show what changed."""
    import json
    
    exp1_config_file = base_dir / "experiments" / exp_name1 / "experiment_config.json"
    exp2_config_file = base_dir / "experiments" / exp_name2 / "experiment_config.json"
    
    if not exp1_config_file.exists():
        print(f"Error: {exp_name1} config not found")
        return
    
    if not exp2_config_file.exists():
        print(f"Error: {exp_name2} config not found")
        return
    
    with open(exp1_config_file) as f:
        config1 = json.load(f)
    
    with open(exp2_config_file) as f:
        config2 = json.load(f)
    
    differences = compare_configs(config1, config2)
    
    print("\n" + "="*80)
    print(f"COMPARISON: {exp_name1} vs {exp_name2}")
    print("="*80)
    
    if not differences:
        print("\n✓ No differences detected (configs are identical)")
        return
    
    print(f"\n🔍 Found {len(differences)} categories of changes:\n")
    
    for category, changes in differences.items():
        print(f"\n--- {category.upper().replace('_', ' ')} ---")
        for key, (old, new) in changes.items():
            print(f"  {key}:")
            print(f"    Old: {old}")
            print(f"    New: {new}")
    
    print("\n" + "="*80 + "\n")


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent
    
    # Example: Track an experiment
    tracker = TenderMLflowTracker(base_dir)
    
    with tracker.start_run(
        experiment_name="exp_20251009_test",
        description="Testing MLflow integration",
        use_full_text=False,
        model_config={
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "temperature": 0.1
        }
    ):
        # Log artifacts
        tracker.log_artifacts()
        
        # Simulate metrics
        tracker.log_metrics({
            "accuracy": 0.92,
            "precision": 0.95,
            "recall": 0.87,
            "f1_score": 0.909,
            "pr_auc": 0.91
        })
        
        # Log costs
        tracker.log_cost(api_cost_usd=5.50, n_requests=500)
        
        print("\n✓ Experiment tracked successfully!")

