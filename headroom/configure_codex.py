"""Back up Codex config and add local Headroom routing; preserve other settings."""
from pathlib import Path
import re
import shutil

config = Path.home() / '.codex/config.toml'
backup = config.with_name('config.toml.before-headroom-20260913')
text = config.read_text()
if not backup.exists():
    shutil.copy2(config, backup)
marker = '# --- Local Headroom routing ---'
if marker not in text:
    text = marker + '\nmodel_provider = "headroom"\nopenai_base_url = "http://127.0.0.1:8787/v1"\n# --- End local Headroom routing ---\n\n' + text
    text += '\n[model_providers.headroom]\nname = "OpenAI via local Headroom"\nbase_url = "http://127.0.0.1:8787/v1"\nwire_api = "responses"\nsupports_websockets = true\nrequires_openai_auth = true\n'
start = text.index('[mcp_servers.headroom]')
end_match = re.search(r'^\[', text[start + 1:], re.M)
end = start + 1 + end_match.start() if end_match else len(text)
text = text[:start] + '''[mcp_servers.headroom]
command = "/usr/local/bin/docker"
args = ["run", "-i", "--rm", "--entrypoint", "headroom", "ghcr.io/chopratejas/headroom@sha256:50b85d8e320cfcdf1b38919bb7ae067b93ff7a8de0a93f05b2c1246370200d1c", "mcp", "serve", "--proxy-url", "http://host.docker.internal:8787"]
startup_timeout_sec = 60
tool_timeout_sec = 120

''' + text[end:]
config.write_text(text)
print(f'Updated {config}; backup: {backup}')
