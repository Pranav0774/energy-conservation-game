"""Assemble submission/ in the order of the five deliverables.

Run after tools.build_report and tools.build_deck:  python -m tools.package_submission
  submission/1_problem_statement.pdf
  submission/2_dataset/        raw/ and clean/ CSVs plus README
  submission/3_source_code/    README with the repo link; source_code.zip beside it
  submission/4_final_report.pdf
  submission/5_presentation.pptx
"""
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUB = ROOT / "submission"
REPO = "https://github.com/Pranav0774/energy-conservation-game"
SKIP_PARTS = {".claude", "node_modules", "__pycache__", ".pytest_cache", ".git", ".venv"}


def copy_dataset() -> None:
    dest = SUB / "2_dataset"
    if dest.exists():
        shutil.rmtree(dest)
    for part in ("raw", "clean"):
        shutil.copytree(ROOT / "data" / part, dest / part)
    shutil.copy2(ROOT / "data" / "README.md", dest / "README.md")


def zip_source() -> Path:
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    out = SUB / "3_source_code" / "source_code.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files):
            p = ROOT / f
            if p.is_file() and not (SKIP_PARTS & set(Path(f).parts)) and not f.startswith("submission/"):
                z.write(p, f)
    (SUB / "3_source_code" / "README.md").write_text(
        f"# Source code\n\nRepository: {REPO}\n\nThe repository is private. If a grader cannot open it, use `source_code.zip` in this folder "
        "(the working tree at the time the submission was assembled, without git history).\n\n"
        "Run the game:\n\n```bash\npython -m pip install -r requirements.txt\npython -m streamlit run app.py\n```\n\n"
        "Run the tests: `python -m pip install -r requirements-dev.txt` then `python -m pytest`. See the top-level README for the layout.\n",
        encoding="utf-8")
    return out


def main() -> None:
    SUB.mkdir(exist_ok=True)
    copy_dataset()
    z = zip_source()
    missing = [n for n in ("1_problem_statement.pdf", "4_final_report.pdf", "5_presentation.pptx") if not (SUB / n).exists()]
    print("zip:", z.relative_to(ROOT), f"{z.stat().st_size / 1024:.0f} KB")
    print("missing deliverables:", missing or "none")


if __name__ == "__main__":
    main()
