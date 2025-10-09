"""
Experiment Tracking Utilities for Tenders-LLM
Tracks data, services, keywords, prompts, and results
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


def compute_file_hash(filepath: Path) -> str:
    """Compute MD5 hash of a file for change detection."""
    if not filepath.exists():
        return "missing"
    
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()[:12]  # First 12 chars


def get_dataset_metadata(data_path: Path, splits_dir: Path) -> Dict[str, Any]:
    """Extract metadata about the dataset."""
    df = pd.read_parquet(data_path)
    
    # Load split IDs
    train_ids = set(open(splits_dir / "train_ids.txt").read().splitlines()) if (splits_dir / "train_ids.txt").exists() else set()
    val_ids = set(open(splits_dir / "val_ids.txt").read().splitlines()) if (splits_dir / "val_ids.txt").exists() else set()
    test_ids = set(open(splits_dir / "test_ids.txt").read().splitlines()) if (splits_dir / "test_ids.txt").exists() else set()
    
    # Dataset stats
    total = len(df)
    positives = int(df['label'].sum())
    
    # Split stats
    df['id_str'] = df['id'].astype(str)
    train_df = df[df['id_str'].isin(train_ids)]
    val_df = df[df['id_str'].isin(val_ids)]
    test_df = df[df['id_str'].isin(test_ids)]
    
    # Date range
    if 'date' in df.columns:
        date_min = df['date'].min()
        date_max = df['date'].max()
        date_range = f"{date_min} to {date_max}"
    else:
        date_range = "unknown"
    
    # Language distribution
    if 'lang' in df.columns:
        lang_dist = df['lang'].value_counts().to_dict()
    else:
        lang_dist = {}
    
    return {
        "tenders_total": total,
        "tenders_positive": positives,
        "tenders_negative": total - positives,
        "positive_rate": round(positives / total, 4) if total > 0 else 0,
        "date_range": date_range,
        "language_distribution": lang_dist,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "train_positives": int(train_df['label'].sum()) if len(train_df) > 0 else 0,
        "val_positives": int(val_df['label'].sum()) if len(val_df) > 0 else 0,
        "test_positives": int(test_df['label'].sum()) if len(test_df) > 0 else 0,
        "data_file": str(data_path),
        "data_hash": compute_file_hash(data_path)
    }


def get_services_metadata(services_file: Path) -> Dict[str, Any]:
    """Extract metadata about services file."""
    if not services_file.exists():
        return {
            "source_file": str(services_file),
            "exists": False,
            "services_count": 0
        }
    
    if services_file.suffix == '.md':
        text = services_file.read_text(encoding='utf-8')
        # Count services (assume ## headers are services)
        services_count = text.count('\n## ') + text.count('\n# ')
    elif services_file.suffix == '.xlsx':
        df = pd.read_excel(services_file)
        services_count = len(df)
        text = df.to_string()
    else:
        text = services_file.read_text(encoding='utf-8')
        services_count = 1
    
    return {
        "source_file": str(services_file),
        "exists": True,
        "services_count": services_count,
        "total_chars": len(text),
        "services_hash": compute_file_hash(services_file)
    }


def get_keywords_metadata(keywords_file: Path) -> Dict[str, Any]:
    """Extract metadata about keywords file."""
    if not keywords_file.exists():
        return {
            "source_file": str(keywords_file),
            "exists": False,
            "keywords_count": 0
        }
    
    df = pd.read_csv(keywords_file)
    
    categories = []
    if 'category' in df.columns:
        categories = df['category'].unique().tolist()
    
    languages = []
    if 'lang' in df.columns:
        languages = df['lang'].unique().tolist()
    
    return {
        "source_file": str(keywords_file),
        "exists": True,
        "keywords_count": len(df),
        "categories": categories,
        "languages": languages,
        "keywords_hash": compute_file_hash(keywords_file)
    }


def get_prompt_metadata(prompt_file: Path) -> Dict[str, Any]:
    """Extract metadata about prompt file."""
    if not prompt_file.exists():
        return {
            "prompt_file": str(prompt_file),
            "exists": False
        }
    
    text = prompt_file.read_text(encoding='utf-8')
    
    # Count few-shot examples (lines starting with '- ')
    lines = text.split('\n')
    example_lines = [l for l in lines if l.strip().startswith('- ') and len(l) > 50]
    
    return {
        "prompt_file": str(prompt_file),
        "exists": True,
        "prompt_length_chars": len(text),
        "prompt_length_lines": len(lines),
        "estimated_examples": len(example_lines),
        "prompt_hash": compute_file_hash(prompt_file)
    }


def create_experiment_config(
    base_dir: Path,
    experiment_name: str,
    description: str = "",
    use_full_text: bool = False,
    model_config: Optional[Dict] = None,
    input_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create comprehensive experiment configuration."""
    
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    prompts_dir = base_dir / "prompts"
    
    # Default configs
    if model_config is None:
        model_config = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "temperature": 0.1
        }
    
    if input_config is None:
        input_config = {
            "use_full_text": use_full_text,
            "max_title_chars": 300,
            "max_text_chars": 1200,
            "text_summarization": True
        }
    
    # Collect all metadata
    config = {
        "experiment_name": experiment_name,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "data": get_dataset_metadata(
            processed_dir / "tenders_clean.parquet",
            processed_dir
        ),
        "input": input_config,
        "services": get_services_metadata(raw_dir / "services.md"),
        "services_excel": get_services_metadata(raw_dir / "Services.xlsx"),
        "keywords": get_keywords_metadata(raw_dir / "keywords.csv"),
        "prompt": get_prompt_metadata(prompts_dir / "classify_tender.md"),
        "model": model_config
    }
    
    return config


def save_experiment_config(config: Dict[str, Any], output_dir: Path):
    """Save experiment configuration to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = output_dir / "experiment_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Saved experiment config to: {config_file}")
    return config_file


def compare_configs(config1: Dict, config2: Dict) -> Dict[str, Any]:
    """Compare two experiment configs and highlight differences."""
    differences = {}
    
    # Data changes
    if config1['data']['data_hash'] != config2['data']['data_hash']:
        differences['data_changed'] = {
            'tenders_total': (config1['data']['tenders_total'], config2['data']['tenders_total']),
            'tenders_positive': (config1['data']['tenders_positive'], config2['data']['tenders_positive']),
            'data_hash': (config1['data']['data_hash'], config2['data']['data_hash'])
        }
    
    # Services changes
    if config1['services']['services_hash'] != config2['services']['services_hash']:
        differences['services_changed'] = {
            'services_count': (config1['services']['services_count'], config2['services']['services_count']),
            'services_hash': (config1['services']['services_hash'], config2['services']['services_hash'])
        }
    
    # Keywords changes
    if config1['keywords']['keywords_hash'] != config2['keywords']['keywords_hash']:
        differences['keywords_changed'] = {
            'keywords_count': (config1['keywords']['keywords_count'], config2['keywords']['keywords_count']),
            'keywords_hash': (config1['keywords']['keywords_hash'], config2['keywords']['keywords_hash'])
        }
    
    # Prompt changes
    if config1['prompt']['prompt_hash'] != config2['prompt']['prompt_hash']:
        differences['prompt_changed'] = {
            'prompt_hash': (config1['prompt']['prompt_hash'], config2['prompt']['prompt_hash'])
        }
    
    # Input config changes
    if config1['input'] != config2['input']:
        differences['input_config_changed'] = {
            'old': config1['input'],
            'new': config2['input']
        }
    
    # Model config changes
    if config1['model'] != config2['model']:
        differences['model_config_changed'] = {
            'old': config1['model'],
            'new': config2['model']
        }
    
    return differences


def print_config_summary(config: Dict[str, Any]):
    """Print human-readable summary of experiment config."""
    print("\n" + "="*80)
    print(f"EXPERIMENT: {config['experiment_name']}")
    print("="*80)
    
    if config.get('description'):
        print(f"\nDescription: {config['description']}")
    
    print(f"\nTimestamp: {config['timestamp']}")
    
    print(f"\n--- DATA ---")
    print(f"  Total tenders: {config['data']['tenders_total']}")
    print(f"  Positives: {config['data']['tenders_positive']} ({config['data']['positive_rate']:.1%})")
    print(f"  Date range: {config['data']['date_range']}")
    print(f"  Train/Val/Test: {config['data']['train_size']}/{config['data']['val_size']}/{config['data']['test_size']}")
    print(f"  Data hash: {config['data']['data_hash']}")
    
    print(f"\n--- SERVICES ---")
    print(f"  File: {config['services']['source_file']}")
    print(f"  Exists: {config['services']['exists']}")
    if config['services']['exists']:
        print(f"  Count: {config['services']['services_count']}")
        print(f"  Hash: {config['services']['services_hash']}")
    
    print(f"\n--- KEYWORDS ---")
    print(f"  File: {config['keywords']['source_file']}")
    print(f"  Exists: {config['keywords']['exists']}")
    if config['keywords']['exists']:
        print(f"  Count: {config['keywords']['keywords_count']}")
        print(f"  Hash: {config['keywords']['keywords_hash']}")
    
    print(f"\n--- PROMPT ---")
    print(f"  File: {config['prompt']['prompt_file']}")
    print(f"  Length: {config['prompt'].get('prompt_length_chars', 0):,} chars")
    print(f"  Examples: ~{config['prompt'].get('estimated_examples', 0)}")
    print(f"  Hash: {config['prompt'].get('prompt_hash', 'N/A')}")
    
    print(f"\n--- INPUT CONFIG ---")
    print(f"  Use full text: {config['input']['use_full_text']}")
    print(f"  Max title chars: {config['input']['max_title_chars']}")
    print(f"  Summarization: {config['input']['text_summarization']}")
    
    print(f"\n--- MODEL ---")
    print(f"  Provider: {config['model']['provider']}")
    print(f"  Model: {config['model']['model_name']}")
    print(f"  Temperature: {config['model']['temperature']}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent
    
    config = create_experiment_config(
        base_dir=base_dir,
        experiment_name="exp_20251009_baseline",
        description="Baseline experiment with current prompt",
        use_full_text=False
    )
    
    print_config_summary(config)
    
    # Save config
    save_experiment_config(config, base_dir / "experiments" / "exp_20251009_baseline")

