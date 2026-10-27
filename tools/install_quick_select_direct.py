"""Add stage auto-confirmation and a scoped selection-UI render guard to working v4."""
import argparse
import datetime
from pathlib import Path
import re
import shutil
BEGIN='# BEGIN QUICK SELECT DIRECT V5'
END='# END QUICK SELECT DIRECT V5'
UI_BEGIN='    # BEGIN QUICK SELECT UI GUARD V5'
UI_END='    # END QUICK SELECT UI GUARD V5'
NAME='QuickSelectAutoConfirmStage'
CALL=NAME+'(ctx.r29, ctx.r27, ctx.r31, ctx.r28);'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--verify-generated',action='store_true')
 p.add_argument('--verify-build',type=Path)
 p.add_argument('--remove',action='store_true')
 a=p.parse_args();root=a.root.resolve()
 if a.verify_generated or a.verify_build:
  emitted=False;guarded=False
  folder=a.verify_build/'expanded-menu-rows' if a.verify_build else root/'generated/default'
  for path in folder.glob('tekken6_recomp.*.cpp'):
   s=path.read_text(encoding='utf-8-sig')
   m=re.search(r'DEFINE_REX_FUNC\(sub_822F16D8\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)',s,re.S)
   if m and CALL in m[1]:emitted=True
   m=re.search(r'DEFINE_REX_FUNC\(sub_822FA058\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)',s,re.S)
   if m and 'if (QuickSelectHideSelectionUI(base, ctx.r3.u32)) return;' in m[1]:guarded=True
  if not emitted:raise SystemExit('Missing stage-confirm hook; regenerate/build first.')
  if a.verify_build and not guarded:raise SystemExit('Missing build-copy render guard; check expanded-row adapter.')
  print('PASS: stage-confirm hook emitted'+('; render guard present in build copies' if a.verify_build else ''))
  return
 cfgpath=root/'tekken6_config.toml';adapter=root/'tools/expand_menu_rows.py'
 cfg=cfgpath.read_text(encoding='utf-8-sig');src=adapter.read_text(encoding='utf-8-sig')
 pattern=r'(?m)^'+re.escape(BEGIN)+r'\n.*?^'+re.escape(END)+r'\n?'
 ui_pattern=r'(?m)^'+re.escape(UI_BEGIN)+r'\n.*?^'+re.escape(UI_END)+r'\n?'
 if a.remove:
  cfg2=re.sub(pattern,'',cfg,flags=re.S);src2=re.sub(ui_pattern,'',src,flags=re.S)
  file=root/'src/tekken6_quick_select_apply.inc'
  fallback=Path(__file__).resolve().parent/'quick_select_auto_v4.inc'
  edits=[(cfgpath,cfg,cfg2),(adapter,src,src2),(file,file.read_text(encoding='utf-8-sig'),fallback.read_text())]
 else:
  if BEGIN in cfg or UI_BEGIN in src:
   if BEGIN in cfg and END in cfg and UI_BEGIN in src and UI_END in src:print('Direct test already installed.');return
   raise SystemExit('Partial v5 installation; restore backups.')
  if 'QuickSelectAutoConfirmCharacter'not in cfg:raise SystemExit('Working v4 auto-character installation required.')
  if re.search(r'(?im)^address\s*=\s*0x0*822f17cc\b',cfg):raise SystemExit('Conflicting stage hook address; no edits made.')
  if 'QuickSelectHideSelectionUI'not in (root/'src/tekken6_quick_select_apply.inc').read_text(encoding='utf-8-sig'):raise SystemExit('Extract complete v5 ZIP first.')
  needle='def patch_function(name, text):\n'
  if src.count(needle)!=1 or cfg.count('[functions]')!=1:raise SystemExit('Expected adapter/config structure differs; no edits made.')
  branch=(Path(__file__).resolve().parent/'quick_select_ui_guard.txt').read_text()
  src2=src.replace(needle,needle+branch,1)
  compile(src2,str(adapter),'exec')
  block=BEGIN+'\n[[midasm_hook]]\naddress = 0x822F17CC\nname = "'+NAME+'"\nregisters = ["r29", "r27", "r31", "r28"]\n'+END+'\n\n'
  cfg2=cfg.replace('[functions]',block+'[functions]',1)
  edits=[(cfgpath,cfg,cfg2),(adapter,src,src2)]
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 for path,before,after in edits:
  if before!=after:
   shutil.copy2(path,path.with_name(path.name+'.before-direct-v5-'+stamp))
   with path.open('w',encoding='utf-8',newline='\n')as out:out.write(after)
 print('Restored v4; regenerate/build/package.' if a.remove else 'Installed v5. Regenerate, build, verify, and package.')
if __name__=='__main__':main()
