from pathlib import Path


def load_prompt(path: str) -> str:
    base_dir = Path(__file__).parents[1]
    file_path = base_dir/path
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
