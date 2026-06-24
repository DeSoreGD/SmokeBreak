# GitHub Upload Checklist

Upload or commit these files and folders:

```text
.gitignore
.gitattributes
README.md
GITHUB_UPLOAD.md
smoke_break/README.md
smoke_break/requirements.txt
smoke_break/build_exe.bat
smoke_break/main.py
smoke_break/app/
smoke_break/app/widgets/
smoke_break/assets/.gitkeep
smoke_break/assets/icon.ico
smoke_break/data/settings.json
smoke_break/data/stats.json
```

Optional, but recommended before making the repository public:

```text
LICENSE
```

Do not upload these files or folders:

```text
__pycache__/
smoke_break/__pycache__/
smoke_break/app/**/__pycache__/
smoke_break/.venv/
smoke_break/build/
smoke_break/dist/
smoke_break/Smoke Break.spec
smoke_break/assets/smoke_break_icon.ico
*.pyc
*.log
*.tmp
*.bak
```

Optional before uploading:

```bat
cd /d "D:\Smoke Break"
python -m compileall -q smoke_break
```

If you upload through the GitHub web UI, select only the files in the first list. If you use Git, `.gitignore` will exclude the generated files automatically.
