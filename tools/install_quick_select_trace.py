"""Install/remove passive diagnostics while retaining existing practice patches."""
import argparse
import datetime
from pathlib import Path
import re
import shutil

BEGIN = '# BEGIN QUICK SELECT TRACE'
END = '# END QUICK SELECT TRACE'
INCLUDE = '#include "tekken6_quick_select_trace.inc"'
HOOKS = [
    (0x8242E2F8, 'TraceQuickSelectMenu', ['r3', 'r4', 'r5', 'r6'],
     '8242E2F8', 'addi r11,r4,-4'),
    (0x8239FA20, 'TraceQuickSelectCharacterScreen', ['r3'],
     '8239FA20', 'mflr r12'),
    (0x8238EDB0, 'TraceQuickSelectMenuClose', ['r3'],
     '8238EDB0', 'mflr r12'),
    (0x82392714, 'TraceQuickSelectPractice', ['r3', 'r4', 'r5'],
     '82392710', 'mflr r12'),
    (0x822A24C8, 'TraceQuickSelectFighterSetting', ['r3', 'r4', 'r5'],
     '822A24C8', 'stw r4,88(r3)'),
    (0x822A24D8, 'TraceQuickSelectFighterId', ['r3', 'r4'],
     '822A24D8', 'stw r4,88(r3)'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    config = root / 'tekken6_config.toml'
    guest = root / 'src/tekken6_guest_hooks.cpp'
    cfg = config.read_text(encoding='utf-8-sig')
    cpp = guest.read_text(encoding='utf-8-sig')
    if args.remove:
        cfg2 = re.sub(r'(?m)^# BEGIN QUICK SELECT TRACE\n.*?^# END QUICK SELECT TRACE\n?',
                      '', cfg, flags=re.S)
        cpp2 = re.sub(r'(?m)^' + re.escape(INCLUDE) + r'\s*\n?', '', cpp)
    else:
        if BEGIN in cfg:
            if END not in cfg or INCLUDE not in cpp:
                raise SystemExit('Partial installation found; run --remove, then reinstall.')
            print('Quick Select tracing is already installed.')
            return
        if INCLUDE in cpp:
            raise SystemExit('Trace include already exists without its config block; run --remove.')
        if not (root / 'src/tekken6_quick_select_trace.inc').is_file():
            raise SystemExit('Missing src/tekken6_quick_select_trace.inc; extract the complete patch.')
        if 'name = "BeginPracticeRage"' not in cfg or '[functions]' not in cfg:
            raise SystemExit('Expected current practice configuration was not found.')
        sources = list((root / 'generated/default').glob('tekken6_recomp.*.cpp'))
        if not sources:
            raise SystemExit('Missing generated/default/tekken6_recomp.*.cpp')
        needed = {h[3]: h[4] for h in HOOKS}
        found = set()
        for path in sources:
            text = path.read_text(encoding='utf-8-sig')
            for func, instruction in needed.items():
                match = re.search(r'DEFINE_REX_FUNC\(sub_' + func +
                                  r'\) \{\s*REX_FUNC_PROLOGUE\(\);(.*?)(?=\nDEFINE_REX_FUNC|\Z)',
                                  text, re.S)
                if match:
                    comments = re.findall(r'^\s*// (.*)', match[1], re.M)
                    if not comments or comments[0] != instruction:
                        raise SystemExit('Unexpected generated instructions in ' + func)
                    if func == '82392710' and comments[1] != 'bl 0x826a0298':
                        raise SystemExit('Unexpected practice entry hook instruction')
                    found.add(func)
        if found != set(needed):
            raise SystemExit('Missing generated routines: ' + ', '.join(sorted(set(needed) - found)))
        # Detect hook address collisions before writing either source file.
        for address, name, registers, _, _ in HOOKS:
            if re.search(r'(?im)^address\s*=\s*0x0*' + format(address, 'x') + r'\b', cfg):
                raise SystemExit('An existing hook uses ' + hex(address))
        block = BEGIN + '\n'
        for address, name, registers, _, _ in HOOKS:
            block += ('[[midasm_hook]]\naddress = 0x%08X\nname = "%s"\nregisters = [%s]\n\n' %
                      (address, name, ', '.join('"%s"' % r for r in registers)))
        block += END + '\n\n'
        cfg2 = cfg.replace('[functions]', block + '[functions]', 1)
        cpp2 = cpp.rstrip() + '\n' + INCLUDE + '\n'
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path, before, after in [(config, cfg, cfg2), (guest, cpp, cpp2)]:
        if before != after:
            shutil.copy2(path, path.with_name(path.name + '.before-quick-select-' + stamp))
            with path.open('w', encoding='utf-8', newline='\n') as output:
                output.write(after)
    print('Quick Select tracing removed.' if args.remove else
          'Quick Select tracing installed. Regenerate, build, and package as usual.')


if __name__ == '__main__':
    main()
