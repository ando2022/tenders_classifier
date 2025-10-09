#!/usr/bin/env python
"""
Master Pipeline Script for Tenders-LLM

Runs the complete pipeline from raw data to predictions.
Can run full pipeline or individual steps.

Usage:
    # Full pipeline
    python run_pipeline.py --all

    # Individual steps
    python run_pipeline.py --reload
    python run_pipeline.py --prepare
    python run_pipeline.py --splits
    python run_pipeline.py --prompt
    python run_pipeline.py --predict
    python run_pipeline.py --eval

    # Custom combinations
    python run_pipeline.py --reload --prepare --splits
    
    # Quick dev mode (small sample)
    python run_pipeline.py --all --dev
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_command(script_path: Path, description: str):
    """Run a Python script and handle errors."""
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print("="*80)
    print(f"Running: {script_path}")
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with error code {e.returncode}")
        print(f"Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Tenders-LLM pipeline")
    
    # Individual steps
    parser.add_argument("--reload", action="store_true", help="Step 0: Reload data from Excel")
    parser.add_argument("--prepare", action="store_true", help="Step 1: Prepare and clean data")
    parser.add_argument("--splits", action="store_true", help="Step 2: Create train/val/test splits")
    parser.add_argument("--prompt", action="store_true", help="Step 3: Build LLM prompt")
    parser.add_argument("--predict", action="store_true", help="Step 4: Run LLM predictions")
    parser.add_argument("--eval", action="store_true", help="Step 5: Evaluate results")
    
    # Shortcuts
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--data-only", action="store_true", help="Run steps 0-2 (data preparation)")
    parser.add_argument("--llm-only", action="store_true", help="Run steps 3-5 (LLM pipeline)")
    
    # Options
    parser.add_argument("--dev", action="store_true", help="Use dev mode (small sample)")
    parser.add_argument("--skip-predict", action="store_true", help="Skip prediction step (use existing predictions)")
    
    args = parser.parse_args()
    
    # Determine which steps to run
    if args.all:
        steps = ["reload", "prepare", "splits", "prompt", "predict", "eval"]
    elif args.data_only:
        steps = ["reload", "prepare", "splits"]
    elif args.llm_only:
        steps = ["prompt", "predict", "eval"]
    else:
        steps = []
        if args.reload:
            steps.append("reload")
        if args.prepare:
            steps.append("prepare")
        if args.splits:
            steps.append("splits")
        if args.prompt:
            steps.append("prompt")
        if args.predict and not args.skip_predict:
            steps.append("predict")
        if args.eval:
            steps.append("eval")
    
    if not steps:
        parser.print_help()
        print("\n✗ No steps selected. Use --all or individual flags.")
        return 1
    
    # Get base directory
    base_dir = Path(__file__).parent
    scripts_dir = base_dir / "scripts"
    
    # Pipeline configuration
    pipeline = {
        "reload": {
            "script": scripts_dir / "00_reload_data_with_fulltext.py",
            "description": "Reload data from Excel (tenders_content.xlsx)"
        },
        "prepare": {
            "script": scripts_dir / "01_prepare_data.py",
            "description": "Prepare data (clean text, detect language)"
        },
        "splits": {
            "script": scripts_dir / "02_make_splits.py",
            "description": "Create train/val/test splits"
        },
        "prompt": {
            "script": scripts_dir / "03_build_prompt.py",
            "description": "Build LLM prompt with few-shot examples"
        },
        "predict": {
            "script": scripts_dir / "04_llm_predict.py",
            "description": "Run LLM predictions (this may take a while!)"
        },
        "eval": {
            "script": scripts_dir / "05_eval.py",
            "description": "Evaluate predictions and generate reports"
        }
    }
    
    # Print pipeline plan
    print("\n" + "="*80)
    print("TENDERS-LLM PIPELINE")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DEV (small sample)' if args.dev else 'FULL'}")
    print(f"\nSteps to run ({len(steps)}):")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {pipeline[step]['description']}")
    print()
    
    input("Press ENTER to start, or Ctrl+C to cancel...")
    
    # Run pipeline
    start_time = datetime.now()
    failed_steps = []
    
    for step in steps:
        config = pipeline[step]
        success = run_command(config["script"], config["description"])
        
        if not success:
            failed_steps.append(step)
            print(f"\n⚠️  Pipeline stopped at step: {step}")
            break
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("PIPELINE SUMMARY")
    print("="*80)
    print(f"Start time:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time:    {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:    {duration}")
    print(f"Steps run:   {len(steps) - len(failed_steps)}/{len(steps)}")
    
    if failed_steps:
        print(f"\n✗ Failed steps: {', '.join(failed_steps)}")
        return 1
    else:
        print(f"\n✓ All steps completed successfully!")
        
        # Show output locations
        print("\nOutput files:")
        print("  data/processed/tenders_clean.parquet  - Cleaned data")
        print("  data/processed/train_ids.txt          - Training IDs")
        print("  data/processed/val_ids.txt            - Validation IDs")
        print("  data/processed/test_ids.txt           - Test IDs")
        print("  prompts/classify_tender.md            - Generated prompt")
        if "predict" in steps:
            print("  data/processed/preds_val.jsonl        - Validation predictions")
            print("  data/processed/preds_test.jsonl       - Test predictions")
        if "eval" in steps:
            print("  reports/pr_curve_val.png              - Validation PR curve")
            print("  reports/pr_curve_test.png             - Test PR curve")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())

