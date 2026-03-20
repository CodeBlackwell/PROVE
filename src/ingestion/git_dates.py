import subprocess
from datetime import date


def get_chunk_dates(repo_path, rel_path, start_line, end_line) -> tuple[date | None, date | None]:
    try:
        result = subprocess.run(
            ["git", "blame", "--date=short", f"-L{start_line},{end_line}", "--", rel_path],
            cwd=repo_path, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None, None
        dates = []
        for line in result.stdout.splitlines():
            for token in line.split():
                if len(token) == 10 and token[4] == "-" and token[7] == "-":
                    try:
                        dates.append(date.fromisoformat(token))
                    except ValueError:
                        continue
        if not dates:
            return None, None
        return min(dates), max(dates)
    except (subprocess.TimeoutExpired, OSError):
        return None, None
