"""Separate Record/Playback eligibility from selection of a recording slot."""
from pathlib import Path
import datetime
import json
import shutil
import sys
import zlib

root = Path(__file__).resolve().parents[1]
payload = json.loads(zlib.decompress((Path(__file__).with_name('record_entry_v2_patch.zlib')).read_bytes()))
pending = []
for name, versions in payload.items():
    path = root / name
    current = path.read_text(encoding='utf-8')
    if current == versions['after']:
        continue
    if current != versions['before']:
        raise SystemExit(f'Unexpected source contents: {name}. No files changed. Send this output before continuing.')
    pending.append((path, versions['after']))
if not pending:
    print('Record entry playback fix V2 already installed and verified.')
    sys.exit(0)
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path, replacement in pending:
    shutil.copy2(path, path.with_name(path.name + '.before-record-entry-v2-' + stamp))
for path, replacement in pending:
    path.write_text(replacement, encoding='utf-8')
    print('Updated', path.relative_to(root))
print('Installed record entry playback fix V2. Rebuild and package next.')
