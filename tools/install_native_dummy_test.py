#!/usr/bin/env python3
"""Test native dummy-control setup using the existing opponent-control experiment."""
from pathlib import Path
from datetime import datetime
import argparse, re, shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');p.add_argument('--verify-generated',action='store_true');a=p.parse_args();root=a.root
if a.verify_generated:
 for f in (root/'generated/default').glob('tekken6_recomp.*.cpp'):
  s=f.read_text(encoding='utf-8-sig')
  if 'NativeDummyControlTest(ctx.r4, ctx.r30);' in s: print('PASS: native dummy setup hook emitted');raise SystemExit(0)
 raise SystemExit('Hook missing from generated files; regenerate first.')
cfg=root/'tekken6_config.toml';src=root/'src/tekken6_guest_hooks.cpp';c=cfg.read_text(encoding='utf-8-sig');s=src.read_text(encoding='utf-8-sig')
cs='# BEGIN NATIVE DUMMY CONTROL TEST V1\n';ce='# END NATIVE DUMMY CONTROL TEST V1\n';ss='// BEGIN NATIVE DUMMY CONTROL TEST V1\n';se='// END NATIVE DUMMY CONTROL TEST V1\n'
def strip(x,start,end):
 if x.count(start)!=1 or x.count(end)!=1:raise SystemExit('Missing or inconsistent markers; no changes made.')
 i=x.index(start);return x[:i]+x[x.index(end,i)+len(end):]
if a.remove:c2=strip(c,cs,ce);s2=strip(s,ss,se)
else:
 if cs in c or ss in s:raise SystemExit('Already installed or partially installed; no changes made.')
 if re.search(r'(?im)^\s*address\s*=\s*0x0*823928a8\b',c):raise SystemExit('Hook address already used; no changes made.')
 marker='#include "tekken6_quick_select_apply.inc"\n'
 if s.count(marker)!=1 or c.count('[functions]')!=1 or 'BEGIN OPPONENT CONTROL IMPLEMENTATION V1' not in s:raise SystemExit('Expected opponent-control experiment not installed; no changes made.')
 # Remove the failed direct-field experiment, if present, preserving input redirection.
 ab='  // BEGIN AUTO DUMMY TEST V1\n';ae='  // END AUTO DUMMY TEST V1\n'
 if ab in s or ae in s:
  if s.count(ab)!=1 or s.count(ae)!=1:raise SystemExit('Incomplete prior experiment; no changes made.')
  i=s.index(ab);j=s.index(ae,i)+len(ae);s=s[:i]+'  else if (fighter.u32 == 0x82901840u && index.u32 == 9) index.u64 = 8;\n'+s[j:]
 impl='''// BEGIN NATIVE DUMMY CONTROL TEST V1
void NativeDummyControlTest(PPCRegister &selected, PPCRegister &owner) {
  using namespace quick_select_apply_detail;
  const char *enabled=std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");
  if (!enabled || std::strcmp(enabled,"1") != 0) return;
  std::lock_guard<std::mutex> lock(mutex);
  uint8_t *b=memory(); if(!b) return;
  const uint32_t c=context(b);
  if (!c || owner.u32!=c || read(b,c)!=0x8207D3E4u || active()) return;
  static std::FILE *f=std::fopen("native-control-apply.txt","w");
  static unsigned count=0;
  if(f && count++<50) {std::fprintf(f,"owner=%08X native=%u override=7\\n",owner.u32,selected.u32);std::fflush(f);}
  selected.u64=7;
}
// END NATIVE DUMMY CONTROL TEST V1
'''
 s2=s.replace(marker,marker+impl,1)
 hook=cs+'[[midasm_hook]]\naddress = 0x823928A8\nname = "NativeDummyControlTest"\nregisters = ["r4", "r30"]\n'+ce
 c2=c.replace('[functions]',hook+'[functions]',1)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path,content in [(cfg,c2),(src,s2)]:shutil.copy2(path,path.with_name(path.name+'.before-native-dummy-test-'+stamp));path.write_text(content,encoding='utf-8',newline='\n')
print('Removed.' if a.remove else 'Installed.');print('Regenerate, verify hook, build and package.')
