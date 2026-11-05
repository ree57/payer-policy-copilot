"""push.py - Upload the app to the Hugging Face Space, and nothing else.

Run from the project root after `hf auth login`:
  .venv\\Scripts\\python space\\push.py
Copies an explicit list of files into a temporary folder and uploads that folder, so data/,
chroma_db/, eval results and .env can never end up in the (public) Space repo.
"""
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

SPACE = "ree57/payer-policy-copilot"
FILES = {  # path in the Space: path in this repo
    "app.py": "app.py",
    "rag.py": "rag.py",
    "embed.py": "embed.py",
    "requirements.txt": "space/requirements.txt",
    "Dockerfile": "space/Dockerfile",
    "README.md": "space/README.md",
}


def main():
    """Stage the listed files and upload them as one commit."""
    message = sys.argv[1] if len(sys.argv) > 1 else "Update app"
    with tempfile.TemporaryDirectory() as tmp:
        for target, source in FILES.items():
            shutil.copy(source, Path(tmp) / target)
        HfApi().upload_folder(repo_id=SPACE, repo_type="space", folder_path=tmp,
                              commit_message=message)
    print(f"Uploaded {', '.join(FILES)} to https://huggingface.co/spaces/{SPACE}")


if __name__ == "__main__":
    main()
