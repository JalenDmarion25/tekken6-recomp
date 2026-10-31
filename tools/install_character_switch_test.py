"""Install/verify/remove the P1 then P2 character loading experiment."""
import argparse
import datetime
from pathlib import Path
import re
import shutil

BEGIN = '# BEGIN QUICK SELECT CHARACTER SWITCH TEST'
END = '# END QUICK SELECT CHARACTER SWITCH TEST'
INCLUDE = '#include "tekken6_quick_select_character_test.inc"'
CALL = '  ArmQuickSelectCharacterTest(n, action.u32, practiceRageOwner.load(std::memory_order_acquire));'
STAGE_INCLUDE = '#include "tekken6_quick_select_stage_test.inc"'
STAGE_CALL = '  ArmQuickSelectStageTest(n, action.u32, practiceRageOwner.load(std::memory_order_acquire));'
HOOKS = [
    ('82245090', 'ApplyQuickSelectCharacterRequest', ['r3', 'r4', 'r5'],
     ['mr r27,r5', 'bl 0x8223f730', 'bl 0x82231158']),
    ('82231158', 'TraceQuickSelectCharacterAsset', ['r3', 'r4', 'r5'],
     ['mr r23,r4', 'mr r31,r5', 'stw r25,148(r3)']),
]


def body(root, function):
    for path in (root / 'generated/default').glob('tekken6_recomp.*.cpp'):
        text = path.read_text(encoding='utf-8-sig')
        match = re.search(r'DEFINE_REX_FUNC\(sub_' + function + r'\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)', text, re.S)
        if match:
            return path, match[1]
    raise SystemExit('Missing generated routine sub_' + function)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--remove', action='store_true')
    group.add_argument('--verify-generated', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.verify_generated:
        for function, name, registers, _ in HOOKS:
            path, text = body(root, function)
            expected = name + '(' + ', '.join('ctx.' + r for r in registers) + ');'
            if expected not in text:
                raise SystemExit('FAIL: missing emitted call ' + name + '; regenerate and build.')
            print('PASS: ' + name + ' emitted in ' + str(path))
        return
    config = root / 'tekken6_config.toml'
    trace = root / 'src/tekken6_quick_select_trace.inc'
    cfg = config.read_text(encoding='utf-8-sig')
    cpp = trace.read_text(encoding='utf-8-sig')
    pattern = r'(?m)^' + re.escape(BEGIN) + r'\n.*?^' + re.escape(END) + r'\n?'
    if args.remove:
        cfg2 = re.sub(pattern, '', cfg, flags=re.S)
        cpp2 = cpp.replace(INCLUDE + '\n', '').replace(CALL + '\n', '')
    else:
        if BEGIN in cfg:
            if END not in cfg or INCLUDE not in cpp or CALL not in cpp:
                raise SystemExit('Partial installation; run --remove, then reinstall.')
            print('Character switch test is already installed.')
            return
        if INCLUDE in cpp or CALL in cpp:
            raise SystemExit('Partial installation; run --remove, then reinstall.')
        if '[functions]' not in cfg or 'TraceQuickSelectPractice' not in cfg:
            raise SystemExit('The existing QUICK SELECT trace is required.')
        if 'practiceRageOwner' not in (root / 'src/tekken6_guest_hooks.cpp').read_text():
            raise SystemExit('Practice owner tracking is required.')
        if not (root / 'src/tekken6_quick_select_character_test.inc').is_file():
            raise SystemExit('Missing character test include; extract the complete ZIP.')
        needle = '  const uint32_t n = id.u32;'
        if cpp.count(needle) != 1 or '#pragma once\n' not in cpp:
            raise SystemExit('Expected QUICK SELECT trace source was not found.')
        # Disable the earlier one-time stage override, preserving passive stage diagnostics.
        stage_pattern = r'(?m)^# BEGIN QUICK SELECT STAGE SWITCH TEST\n.*?^# END QUICK SELECT STAGE SWITCH TEST\n?'
        stage = re.search(stage_pattern, cfg, re.S)
        cfg2, cpp2 = cfg, cpp
        if stage:
            old = stage[0]
            if not (('name = "ApplyQuickSelectStageRequest"' in old and '0x82269868' in old) or
                    ('name = "ApplyQuickSelectStageTest"' in old and '0x823943C0' in old)):
                raise SystemExit('Unrecognized stage experiment block; no edits made.')
            cfg2 = cfg[:stage.start()] + cfg[stage.end():]
            cpp2 = cpp2.replace(STAGE_INCLUDE + '\n', '').replace(STAGE_CALL + '\n', '')
        elif STAGE_INCLUDE in cpp or STAGE_CALL in cpp:
            raise SystemExit('Partial stage experiment; remove it before installing the character test.')
        block = BEGIN + '\n'
        for function, name, registers, expected in HOOKS:
            if re.search(r'(?im)^address\s*=\s*0x0*' + function + r'\b', cfg2):
                raise SystemExit('An existing hook already uses 0x' + function)
            _, text = body(root, function)
            comments = re.findall(r'^\s*// (.*)', text, re.M)
            if not set(expected).issubset(comments):
                raise SystemExit('Unexpected generated instructions in sub_' + function)
            block += ('[[midasm_hook]]\naddress = 0x%s\nname = "%s"\nregisters = [%s]\n\n' %
                      (function, name, ', '.join('"%s"' % r for r in registers)))
        block += END + '\n\n'
        cfg2 = cfg2.replace('[functions]', block + '[functions]', 1)
        cpp2 = cpp2.replace('#pragma once\n', '#pragma once\n' + INCLUDE + '\n', 1)
        cpp2 = cpp2.replace(needle, needle + '\n' + CALL, 1)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in [(config, cfg, cfg2), (trace, cpp, cpp2)]:
        if before != after:
            shutil.copy2(path, path.with_name(path.name + '.before-character-switch-' + stamp))
            with path.open('w', encoding='utf-8', newline='\n') as output:
                output.write(after)
    print('Character test removed (stage override remains disabled).' if args.remove else
          'Character test installed; stage override disabled. Regenerate, build, verify, and package.')


if __name__ == '__main__':
    main()
