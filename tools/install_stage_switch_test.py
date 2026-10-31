"""Install, upgrade, verify, or remove the one-time stage switch test."""
import argparse
import datetime
from pathlib import Path
import re
import shutil

BEGIN = '# BEGIN QUICK SELECT STAGE SWITCH TEST'
END = '# END QUICK SELECT STAGE SWITCH TEST'
INCLUDE = '#include "tekken6_quick_select_stage_test.inc"'
CALL = '  ArmQuickSelectStageTest(n, action.u32, practiceRageOwner.load(std::memory_order_acquire));'
HOOK = '''[[midasm_hook]]
address = 0x82269868
name = "ApplyQuickSelectStageRequest"
registers = ["r3", "r4"]
'''
OLD_HOOK = '''[[midasm_hook]]
address = 0x823943C0
name = "ApplyQuickSelectStageTest"
registers = ["r3", "r31"]
'''


def generated_body(root):
    for path in (root / 'generated/default').glob('tekken6_recomp.*.cpp'):
        text = path.read_text(encoding='utf-8-sig')
        match = re.search(r'DEFINE_REX_FUNC\(sub_82269868\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)', text, re.S)
        if match:
            return path, match[1]
    raise SystemExit('Missing generated shared stage-request routine sub_82269868.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--remove', action='store_true')
    mode.add_argument('--verify-generated', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.verify_generated:
        path, body = generated_body(root)
        if not re.search(r'ApplyQuickSelectStageRequest\(ctx\.r3,\s*ctx\.r4\);', body):
            raise SystemExit('FAIL: v2 hook is not emitted. Regenerate/build before packaging or launching.')
        print('PASS: v2 shared-stage hook is emitted in ' + str(path))
        return
    config = root / 'tekken6_config.toml'
    trace = root / 'src/tekken6_quick_select_trace.inc'
    cfg = config.read_text(encoding='utf-8-sig')
    cpp = trace.read_text(encoding='utf-8-sig')
    pattern = r'(?m)^' + re.escape(BEGIN) + r'\n.*?^' + re.escape(END) + r'\n?'
    match = re.search(pattern, cfg, re.S)
    if args.remove:
        cfg2 = re.sub(pattern, '', cfg, flags=re.S)
        cpp2 = cpp.replace(INCLUDE + '\n', '').replace(CALL + '\n', '')
    else:
        if '[functions]' not in cfg or 'TraceQuickSelectPractice' not in cfg:
            raise SystemExit('The installed QUICK SELECT trace configuration is required.')
        if not (root / 'src/tekken6_quick_select_stage_test.inc').is_file():
            raise SystemExit('Missing stage test include; extract the complete ZIP.')
        if 'practiceRageOwner' not in (root / 'src/tekken6_guest_hooks.cpp').read_text():
            raise SystemExit('Practice owner tracking is required.')
        needle = '  const uint32_t n = id.u32;'
        if cpp.count(needle) != 1 or '#pragma once\n' not in cpp:
            raise SystemExit('Expected QUICK SELECT trace implementation was not found.')
        if match:
            content = match[0].replace(BEGIN + '\n', '', 1).replace(END, '').strip()
            if content not in [HOOK.strip(), OLD_HOOK.strip()]:
                raise SystemExit('The owned stage-test block differs; no edits made.')
            if INCLUDE not in cpp or CALL not in cpp:
                raise SystemExit('Partial installation; run --remove, then reinstall.')
            base_cfg = cfg[:match.start()] + cfg[match.end():]
        else:
            if BEGIN in cfg or END in cfg or INCLUDE in cpp or CALL in cpp:
                raise SystemExit('Partial installation; run --remove, then reinstall.')
            base_cfg = cfg
        if re.search(r'(?im)^address\s*=\s*0x0*82269868\b', base_cfg):
            raise SystemExit('An unrelated hook already uses 0x82269868.')
        _, body = generated_body(root)
        comments = re.findall(r'^\s*// (.*)', body, re.M)
        if not {'mflr r12', 'stw r5,276(r31)', 'bl 0x8226c368'}.issubset(comments):
            raise SystemExit('The expected shared stage-request instructions differ.')
        block = BEGIN + '\n' + HOOK + END + '\n\n'
        if match:
            cfg2 = cfg[:match.start()] + block.rstrip('\n') + '\n' + cfg[match.end():]
            cpp2 = cpp
        else:
            cfg2 = cfg.replace('[functions]', block + '[functions]', 1)
            cpp2 = cpp.replace('#pragma once\n', '#pragma once\n' + INCLUDE + '\n', 1)
            cpp2 = cpp2.replace(needle, needle + '\n' + CALL, 1)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in [(config, cfg, cfg2), (trace, cpp, cpp2)]:
        if before != after:
            shutil.copy2(path, path.with_name(path.name + '.before-stage-switch-' + stamp))
            with path.open('w', encoding='utf-8', newline='\n') as output:
                output.write(after)
    print('Stage switch test removed.' if args.remove else
          'Stage switch v2 installed/upgraded. Regenerate, build, verify, and package.')


if __name__ == '__main__':
    main()
