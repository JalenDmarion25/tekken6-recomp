"""Add the native Quick Select layout below Mode Select / Defensive Training."""
import argparse
import datetime
from pathlib import Path
import re
import shutil

INCLUDE = '#include "tekken6_quick_select_menu_records.inc"'
CALL = '  InstallPracticeQuickSelectRecords(base, newRecords, newTexts, strings);'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    rage = root / 'src/tekken6_practice_rage_menu.inc'
    original = rage.read_text(encoding='utf-8-sig')
    if args.remove:
        if INCLUDE not in original and CALL not in original:
            print('Quick Select layout is not installed.')
            return
        for token in [INCLUDE, CALL, 'constexpr uint32_t totalCount = 516;',
                      'totalCount * (recordSize + textSize) + 768']:
            if original.count(token) != 1:
                raise SystemExit('The layout installer differs; restore its backup instead of removing automatically.')
        changed = original.replace(INCLUDE + '\n', '').replace(CALL + '\n', '')
        changed = changed.replace('constexpr uint32_t totalCount = 516;', 'constexpr uint32_t totalCount = 502;', 1)
        changed = changed.replace('totalCount * (recordSize + textSize) + 768',
                                  'totalCount * (recordSize + textSize) + 256', 1)
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        shutil.copy2(rage, rage.with_name(rage.name + '.before-layout-removal-' + stamp))
        with rage.open('w', encoding='utf-8', newline='\n') as output:
            output.write(changed)
        print('Quick Select layout removed; completed experiments remain disabled. Build/package again.')
        return
    if INCLUDE in original or CALL in original:
        if INCLUDE in original and CALL in original and 'totalCount = 516;' in original:
            print('Quick Select layout is already installed.')
            return
        raise SystemExit('Partial menu-layout installation; restore its backup before retrying.')
    if not (root / 'src/tekken6_quick_select_menu_records.inc').is_file():
        raise SystemExit('Missing menu-record include; extract the complete patch.')
    for token in ['constexpr uint32_t totalCount = 502;',
                  'totalCount * (recordSize + textSize) + 256',
                  '  menuText = newTexts;', '#pragma once\n']:
        if original.count(token) != 1:
            raise SystemExit('Expected current Rage table installer differs: ' + token)
    if not all(token in original for token in ['p1Row = 496', 'p2Row = 499', 'originalCount = 496']):
        raise SystemExit('Unexpected custom record IDs; no edits made.')
    changed = original.replace('#pragma once\n', '#pragma once\n' + INCLUDE + '\n', 1)
    changed = changed.replace('constexpr uint32_t totalCount = 502;', 'constexpr uint32_t totalCount = 516;', 1)
    changed = changed.replace('totalCount * (recordSize + textSize) + 256',
                              'totalCount * (recordSize + textSize) + 768', 1)
    changed = changed.replace('  menuText = newTexts;', CALL + '\n  menuText = newTexts;', 1)
    edits = [(rage, original, changed)]
    # Stop the now-successful character experiment from arming in layout testing.
    config = root / 'tekken6_config.toml'
    cfg = config.read_text(encoding='utf-8-sig')
    trace = root / 'src/tekken6_quick_select_trace.inc'
    cpp = trace.read_text(encoding='utf-8-sig') if trace.exists() else None
    for kind, functions, include, call in [
        ('CHARACTER', ['ApplyQuickSelectCharacterRequest', 'TraceQuickSelectCharacterAsset'],
         '#include "tekken6_quick_select_character_test.inc"',
         '  ArmQuickSelectCharacterTest(n, action.u32, practiceRageOwner.load(std::memory_order_acquire));'),
        ('STAGE', ['ApplyQuickSelectStageRequest', 'ApplyQuickSelectStageTest'],
         '#include "tekken6_quick_select_stage_test.inc"',
         '  ArmQuickSelectStageTest(n, action.u32, practiceRageOwner.load(std::memory_order_acquire));')]:
        pattern = r'(?m)^# BEGIN QUICK SELECT ' + kind + r' SWITCH TEST\n.*?^# END QUICK SELECT ' + kind + r' SWITCH TEST\n?'
        match = re.search(pattern, cfg, re.S)
        if match:
            if not any('name = "' + function + '"' in match[0] for function in functions):
                raise SystemExit('Unrecognized owned ' + kind.lower() + ' experiment block; no edits made.')
            cfg = cfg[:match.start()] + cfg[match.end():]
            if cpp is None or include not in cpp or call not in cpp:
                raise SystemExit('Partial ' + kind.lower() + ' experiment; remove it before installing the layout.')
            cpp = cpp.replace(include + '\n', '').replace(call + '\n', '')
    edits.append((config, config.read_text(encoding='utf-8-sig'), cfg))
    if cpp is not None:
        edits.append((trace, trace.read_text(encoding='utf-8-sig'), cpp))
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in edits:
        if before != after:
            shutil.copy2(path, path.with_name(path.name + '.before-quick-select-layout-' + stamp))
            with path.open('w', encoding='utf-8', newline='\n') as output:
                output.write(after)
    print('Quick Select layout installed; completed selection experiments disabled. Regenerate/build/package.')


if __name__ == '__main__':
    main()
