"""Upgrade the installed Quick Select layout to the experimental native Apply test."""
import argparse
import datetime
from pathlib import Path
import re
import shutil
try:
    import tomllib
except ImportError:
    tomllib = None

BEGIN = '# BEGIN QUICK SELECT APPLY TEST'
END = '# END QUICK SELECT APPLY TEST'
INCLUDE = '#include "tekken6_quick_select_apply.inc"'
HOOKS = [
 ('82431F20','QuickSelectMenuOpening',['r3'],'82431F20'),
 ('82435DF0','QuickSelectSyncMenu',['r3'],'82435DF0'),
 ('8242BFD8','QuickSelectApplyAction',['r3','r4'],'8242BFD8'),
 ('82245018','QuickSelectRedirectMode',['r3','r4'],'82245018'),
 ('822518D8','QuickSelectBypassScreen',['r3','r4'],'822518D8'),
 ('82245090','QuickSelectLoadCharacter',['r3','r4','r5'],'82245090'),
 ('82269868','QuickSelectLoadStage',['r3','r4'],'82269868'),
 ('82392718','QuickSelectObservePractice',['r3','r4','r5'],'82392710'),
]

def generated(root):
    result={}
    for path in (root/'generated/default').glob('tekken6_recomp.*.cpp'):
        source=path.read_text(encoding='utf-8-sig')
        for match in re.finditer(r'DEFINE_REX_FUNC\(sub_([0-9A-F]+)\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)',source,re.S):
            if match[1] in {h[3] for h in HOOKS}: result[match[1]]=match[2]
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--verify-generated',action='store_true')
    p.add_argument('--remove',action='store_true')
    args=p.parse_args();root=args.root.resolve()
    if args.verify_generated:
        code=generated(root)
        for _,name,registers,fn in HOOKS:
            call=name+'('+', '.join('ctx.'+r for r in registers)+');'
            if call not in code.get(fn,''):raise SystemExit('Missing emitted hook '+name+'. Regenerate before building.')
            print('PASS: '+name)
        return
    cfgpath=root/'tekken6_config.toml';ragepath=root/'src/tekken6_practice_rage_menu.inc';cpppath=root/'src/tekken6_guest_hooks.cpp'
    cfg=cfgpath.read_text(encoding='utf-8-sig');rage=ragepath.read_text(encoding='utf-8-sig');cpp=cpppath.read_text(encoding='utf-8-sig')
    pattern=r'(?m)^'+re.escape(BEGIN)+r'\n.*?^'+re.escape(END)+r'\n?'
    if args.remove:
        cfg2=re.sub(pattern,'',cfg,flags=re.S)
        cpp2=cpp.replace(INCLUDE+'\n','')
        rage2=rage.replace('totalCount = 520;','totalCount = 516;')
        helper=root/'src/tekken6_quick_select_menu_records.inc'
        original_helper=Path(__file__).resolve().parent/'quick_select_layout_records_original.inc'
        edits=[(cfgpath,cfg,cfg2),(cpppath,cpp,cpp2),(ragepath,rage,rage2),
               (helper,helper.read_text(),original_helper.read_text())]
    else:
        if BEGIN in cfg:
            if END not in cfg or INCLUDE not in cpp or 'totalCount = 520;' not in rage:raise SystemExit('Partial Apply installation; restore backups.')
            print('Apply test is already installed.');return
        if INCLUDE in cpp:raise SystemExit('Partial Apply installation; restore backups.')
        if 'totalCount = 516;' not in rage or 'InstallPracticeQuickSelectRecords' not in rage:raise SystemExit('Install the previous Quick Select menu layout first.')
        for name in ['tekken6_quick_select_apply.inc','tekken6_quick_select_menu_records.inc']:
            if not (root/'src'/name).exists():raise SystemExit('Extract the complete test ZIP first.')
        used={int(a,16) for a in re.findall(r'(?im)^address\s*=\s*0x([0-9a-f]+)\s*$',cfg)}
        code=generated(root)
        block=BEGIN+'\n'
        for address,name,registers,fn in HOOKS:
            if int(address,16) in used:raise SystemExit('Conflicting hook at 0x'+address+'; no edits made.')
            if fn not in code:raise SystemExit('Missing generated function '+fn)
            block+='[[midasm_hook]]\naddress = 0x'+address+'\nname = "'+name+'"\nregisters = ['+', '.join('"'+r+'"' for r in registers)+']\n\n'
        block+=END+'\n\n'
        cfg2=cfg.replace('[functions]',block+'[functions]',1)
        if cfg2==cfg:raise SystemExit('Missing [functions] section.')
        if tomllib:tomllib.loads(cfg2)
        cpp2=cpp.rstrip()+'\n'+INCLUDE+'\n'
        rage2=rage.replace('totalCount = 516;','totalCount = 520;',1)
        edits=[(cfgpath,cfg,cfg2),(cpppath,cpp,cpp2),(ragepath,rage,rage2)]
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path,before,after in edits:
        if before!=after:
            shutil.copy2(path,path.with_name(path.name+'.before-quick-select-apply-'+stamp))
            with path.open('w',encoding='utf-8',newline='\n') as out:out.write(after)
    print('Apply test removed; rebuild to return to the layout prototype.' if args.remove else 'Apply test installed. Regenerate, verify emitted hooks, build, and package.')

if __name__=='__main__':main()
