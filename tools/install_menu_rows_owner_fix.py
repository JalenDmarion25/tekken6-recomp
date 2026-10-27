"""Make expanded menu-row lookup specific to the owning menu window."""
import argparse
import datetime
from pathlib import Path
import shutil

MARKER = 'OWNER-SCOPED MENU ROWS FIX'

def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit('Unexpected ' + label + '; no files changed')
    return text.replace(old, new, 1)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    header = root / 'src/tekken6_expanded_rows.h'
    impl = root / 'src/tekken6_expanded_rows.inc'
    adapter = root / 'tools/expand_menu_rows.py'
    files = [header, impl, adapter]
    original = [p.read_text(encoding='utf-8-sig') for p in files]
    if any(MARKER in s for s in original):
        if all(MARKER in s for s in original):
            print('Owner-scoped fix already installed. Rebuild and package.')
            return
        raise SystemExit('Partial installation detected; restore backups before retrying')
    h, c, a = original
    for name, second in [('T6RowsMap', 'uint32_t bank'),
                         ('T6RowsAdvance', 'int32_t step'),
                         ('T6RowsRelated', 'uint32_t bank')]:
        h = replace_once(h, f'{name}(uint32_t address, {second})',
                         f'{name}(uint32_t address, {second}, uint32_t owner)', name + ' declaration')
    c = replace_once(c, 'bool locate(uint32_t address, uint32_t& owner, Storage& storage,',
                     'bool locate(uint32_t address, uint32_t expectedOwner, uint32_t& owner, Storage& storage,', 'locate signature')
    c = replace_once(c, '  for (const auto& entry : windows) {\n    for (uint32_t k = 0; k < 3; ++k) {',
                     '  for (const auto& entry : windows) {\n    if (entry.first != expectedOwner) continue;\n    for (uint32_t k = 0; k < 3; ++k) {', 'locate owner filter')
    for name, second in [('T6RowsMap', 'uint32_t bank'),
                         ('T6RowsAdvance', 'int32_t step'),
                         ('T6RowsRelated', 'uint32_t targetBank')]:
        c = replace_once(c, f'{name}(uint32_t address, {second})',
                         f'{name}(uint32_t address, {second}, uint32_t expectedOwner)', name + ' definition')
    c = replace_once(c, '  for (const auto& entry : windows) {\n    const uint32_t delta = address - entry.first - offsets[bank];',
                     '  for (const auto& entry : windows) {\n    if (entry.first != expectedOwner) continue;\n    const uint32_t delta = address - entry.first - offsets[bank];', 'map owner filter')
    if c.count('locate(address, owner, s, bank, index)') != 2:
        raise SystemExit('Unexpected locate calls; no files changed')
    c = c.replace('locate(address, owner, s, bank, index)', 'locate(address, expectedOwner, owner, s, bank, index)')
    needle = '    if name not in TARGETS: return text, 0\n'
    a = replace_once(a, needle, needle + '''    prologue = '\\tREX_FUNC_PROLOGUE();\\n'
    if text.count(prologue) != 1: raise ValueError('Unexpected owner capture in sub_' + name)
    text = text.replace(prologue, prologue + '\\t[[maybe_unused]] const uint32_t t6RowsOwner = ctx.r3.u32; // OWNER-SCOPED MENU ROWS FIX\\n', 1)
''', 'adapter owner capture')
    substitutions = [
        ('T6RowsMap(ctx.{dest}.u32, {BANK[n]})', 'T6RowsMap(ctx.{dest}.u32, {BANK[n]}, t6RowsOwner)'),
        ('T6RowsAdvance(ctx.{src}.u32, {n})', 'T6RowsAdvance(ctx.{src}.u32, {n}, t6RowsOwner)'),
        ('T6RowsRelated(ctx.{src}.u32, {0 if n < 0 else 1})', 'T6RowsRelated(ctx.{src}.u32, {0 if n < 0 else 1}, t6RowsOwner)'),
        ('T6RowsMap(ctx.{src}.u32 + {off}, {BANK[off]})', 'T6RowsMap(ctx.{src}.u32 + {off}, {BANK[off]}, t6RowsOwner)'),
        ('T6RowsRelated(ctx.{src}.u32, {0 if off<0 else 1})', 'T6RowsRelated(ctx.{src}.u32, {0 if off<0 else 1}, t6RowsOwner)'),
        ('T6RowsMap(ctx.r11.u32 + ctx.r7.u32, 2)', 'T6RowsMap(ctx.r11.u32 + ctx.r7.u32, 2, t6RowsOwner)'),
    ]
    for old, new in substitutions:
        a = replace_once(a, old, new, 'adapter call ' + old)
    h = '// ' + MARKER + '\n' + h
    c = '// ' + MARKER + '\n' + c
    compile(a, str(adapter), 'exec')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in zip(files, original, [h, c, a]):
        shutil.copy2(path, path.with_name(path.name + '.before-owner-fix-' + stamp))
        path.write_text(after, encoding='utf-8', newline='\n')
    print('Installed owner-scoped row mapping. Rebuild and package.')

if __name__ == '__main__':
    main()
