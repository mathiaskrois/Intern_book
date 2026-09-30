"""Local configuration. Credentials are held in memory only."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def credentials():
    values = dict(os.environ)
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                values.setdefault(k.strip(), v.strip().strip('"\'“”'))
    # The supplied brief contains the fallback configuration. Never echo it.
    required = ['WEBSITE_URL', 'WEBSITE_USERNAME', 'WEBSITE_PASSWORD']
    if any(not values.get(k) for k in required):
        brief = subprocess.check_output(['textutil', '-convert', 'txt', '-stdout', str(ROOT / 'project_description.rtf')], text=True)
        for k in required:
            match = re.search(k + r'=[“"\']([^“”"\'\s]+)', brief)
            if match:
                values.setdefault(k, match.group(1))
    if any(not values.get(k) for k in required):
        raise RuntimeError('Website credentials are missing from the environment and local configuration.')
    return {k: values[k] for k in required}

def launch(p):
    auth = ROOT / '.auth'
    auth.mkdir(exist_ok=True, mode=0o700)
    return p.chromium.launch_persistent_context(str(auth / 'browser'), channel='chrome', headless=True,
        viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)

def authenticate(page, cfg):
    page.goto(cfg['WEBSITE_URL'], wait_until='networkidle')
    if page.locator('input[type=password]').count():
        page.locator('input[name=username]').fill(cfg['WEBSITE_USERNAME'])
        page.locator('input[name=password]').fill(cfg['WEBSITE_PASSWORD'])
        page.get_by_role('button', name='Log ind', exact=True).click()
        page.wait_for_load_state('networkidle')
    if page.locator('input[type=password]').count():
        raise RuntimeError('Authentication needs manual attention; login form remains.')
