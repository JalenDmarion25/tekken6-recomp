"""Add one native character-confirmation hook to an existing Quick Select Apply install."""
import argparse
import datetime
from pathlib import Path
import re
import shutil
BEGIN='# BEGIN QUICK SELECT AUTO CHARACTER V4'
END='# END QUICK SELECT AUTO CHARACTER V4'
NAME='QuickSelectAutoConfirmCharacter'
CALL=NAME+'(ctx.r3, ctx.r4, ctx.r5, ctx.r7);'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--verify-generated',action='store_true')
 p.add_argument('--remove',action='store_true')
 a=p.parse_args();root=a.root.resolve()
 if a.verify_generated:
  for path in (root/'generated/default').glob('tekken6_recomp.*.cpp'):
   s=path.read_text(encoding='utf-8-sig')
   m=re.search(r'DEFINE_REX_FUNC\(sub_822F0F88\) \{(.*?)(?=\nDEFINE_REX_FUNC|\Z)',s,re.S)
   if m and CALL in m[1]:print('PASS: '+NAME+' emitted');return
  raise SystemExit('Missing emitted auto-confirm hook. Regenerate and rebuild.')
 path=root/'tekken6_config.toml';s=path.read_text(encoding='utf-8-sig')
 pattern=r'(?m)^'+re.escape(BEGIN)+r'\n.*?^'+re.escape(END)+r'\n?'
 if a.remove:
  result=re.sub(pattern,'',s,flags=re.S)
  source=root/'src/tekken6_quick_select_apply.inc'
  fallback=Path(__file__).resolve().parent/'quick_select_native_flow_v3.inc'
  edits=[(path,s,result),(source,source.read_text(encoding='utf-8-sig'),fallback.read_text())]
 else:
  if BEGIN in s:
   if END not in s or NAME not in s:raise SystemExit('Partial installation; restore config backup.')
   print('Auto-character hook is already installed.');return
  if re.search(r'(?im)^address\s*=\s*0x0*822f0f88\b',s):raise SystemExit('Conflicting hook at 0x822F0F88; no edits made.')
  if 'QuickSelectBypassScreen'not in s:raise SystemExit('Install the existing Apply hooks first.')
  source=root/'src/tekken6_quick_select_apply.inc'
  if NAME not in source.read_text(encoding='utf-8-sig'):raise SystemExit('Extract the complete v4 ZIP first.')
  block=BEGIN+'\n[[midasm_hook]]\naddress = 0x822F0F88\nname = "'+NAME+'"\nregisters = ["r3", "r4", "r5", "r7"]\n'+END+'\n\n'
  if s.count('[functions]')!=1:raise SystemExit('Expected one [functions] section; no edits made.')
  result=s.replace('[functions]',block+'[functions]',1)
  edits=[(path,s,result)]
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 for path,before,after in edits:
  if before!=after:
   shutil.copy2(path,path.with_name(path.name+'.before-auto-character-'+stamp))
   with path.open('w',encoding='utf-8',newline='\n')as out:out.write(after)
 print('Restored v3. Regenerate/build/package.' if a.remove else 'Installed. Regenerate, verify the emitted hook, build, and package.')
if __name__=='__main__':main()
