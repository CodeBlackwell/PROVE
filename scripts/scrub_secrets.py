"""Scan Neo4j CodeSnippets for sensitive keys/secrets."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import Settings
from src.core import Neo4jClient

PATTERNS = [
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AWS access key'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'OpenAI/Anthropic key'),
    (re.compile(r'ghp_[a-zA-Z0-9]{36}'), 'GitHub PAT'),
    (re.compile(r'github_pat_[a-zA-Z0-9_]{60,}'), 'GitHub fine-grained PAT'),
    (re.compile(r'xoxb-[0-9]{10,}'), 'Slack bot token'),
    (re.compile(r'xoxp-[0-9]{10,}'), 'Slack user token'),
    (re.compile(r'nvapi-[a-zA-Z0-9_\-]{20,}'), 'NVIDIA API key'),
    (re.compile(r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----'), 'private key'),
    (re.compile(r'mongodb(?:\+srv)?://[^\s"]+:[^\s"]+@'), 'MongoDB URI with creds'),
    (re.compile(r'postgres(?:ql)?://[^\s"]+:[^\s"]+@'), 'Postgres URI with creds'),
    (re.compile(r'redis://:[^\s"]+@'), 'Redis URI with creds'),
    (re.compile(r'(?:api_key|secret_key|password|auth_token)\s*=\s*["\'][A-Za-z0-9_/+=\-]{16,}["\']', re.I), 'hardcoded secret assignment'),
    (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]{20,}'), 'Bearer token'),
    (re.compile(r'NORDVPN_WIREGUARD_KEY\s*=\s*\S+'), 'VPN key'),
]


def main():
    s = Settings.load()
    n = Neo4jClient(s.neo4j_uri, s.neo4j_user, s.neo4j_password)

    with n.driver.session() as sess:
        results = sess.run(
            "MATCH (cs:CodeSnippet) WHERE cs.content IS NOT NULL "
            "RETURN cs.name AS name, cs.file_path AS fp, cs.content AS content"
        ).data()

    print(f"Scanning {len(results)} snippets...")
    hits = []
    for r in results:
        content = r["content"] or ""
        for pat, label in PATTERNS:
            for match in pat.finditer(content):
                matched_text = match.group()
                # Skip obvious placeholders/examples
                if any(x in matched_text.lower() for x in [
                    "your_", "example", "xxx", "placeholder", "changeme",
                    "sk-your", "sk-ant-", "<", "test_", "fake", "dummy",
                    "replace_", "insert_", "TODO",
                ]):
                    continue
                hits.append((label, r["fp"], r["name"], matched_text[:80]))

    if not hits:
        print("No secrets found!")
    else:
        print(f"\nFound {len(hits)} potential secrets:\n")
        for label, fp, name, match in hits:
            print(f"  [{label}] {fp} :: {name}")
            print(f"    -> {match}")
            print()

    n.close()
    return hits


if __name__ == "__main__":
    found = main()
    sys.exit(1 if found else 0)
