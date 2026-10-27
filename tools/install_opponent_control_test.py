#!/usr/bin/env python3
"""Install a reversible, opt-in opponent control experiment."""
import argparse,re,shutil
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');p.add_argument('--verify-generated',action='store_true');a=p.parse_args();root=a.root
if a.verify_generated:
 for f in (root/'generated/default').glob('tekken6_recomp.*.cpp'):
  s=f.read_text(encoding='utf-8-sig')
  if 'OpponentControlSelectInput(ctx.r29, ctx.r30);' in s: print('PASS: opponent control hook emitted');raise SystemExit(0)
 raise SystemExit('Opponent control hook missing; regenerate first.')
cfg=root/'tekken6_config.toml';src=root/'src/tekken6_guest_hooks.cpp';c=cfg.read_text(encoding='utf-8-sig');s=src.read_text(encoding='utf-8-sig')
cs='# BEGIN OPPONENT CONTROL EXPERIMENT V1\n';ce='# END OPPONENT CONTROL EXPERIMENT V1\n';ss='// BEGIN OPPONENT CONTROL EXPERIMENT V1\n';se='// END OPPONENT CONTROL EXPERIMENT V1\n';ls='  // BEGIN OPPONENT CONTROL RETURN V1\n';le='  // END OPPONENT CONTROL RETURN V1\n'
def strip(x,start,end):
 if x.count(start)!=1 or x.count(end)!=1:raise SystemExit('Missing or inconsistent markers; no changes made.')
 i=x.index(start);j=x.index(end,i)+len(end);return x[:i]+x[j:]
if a.remove:c2=strip(c,cs,ce);s2=strip(strip(s,ss,se),ls,le)
else:
 if cs in c or ss in s or ls in s:raise SystemExit('Already installed or partial installation; no changes made.')
 if re.search(r'(?im)^\s*address\s*=\s*0x0*822a45c4\b',c):raise SystemExit('Hook address already used; no changes made.')
 needle='void TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)\n{\n'
 if s.count(needle)!=1 or c.count('[functions]')!=1 or '#include "tekken6_quick_select_apply.inc"' not in s or 'address = 0x82268168' not in c:raise SystemExit('Unsupported source/config; no changes made.')
 decl='''// BEGIN OPPONENT CONTROL EXPERIMENT V1
thread_local bool opponentControlSuppressP1 = false;
// END OPPONENT CONTROL EXPERIMENT V1
'''
 ret='''  // BEGIN OPPONENT CONTROL RETURN V1
  if (opponentControlSuppressP1 &&
      (object.u32 == 0x822A45CCu || object.u32 == 0x822A45E0u)) {
    buttons.u64 = 0;
  }
  // END OPPONENT CONTROL RETURN V1
'''
 s2=s.replace(needle,decl+needle+ret,1)
 impl='''
// BEGIN OPPONENT CONTROL IMPLEMENTATION V1
// Deliberately limited to the observed fighter objects and practice context.
void OpponentControlSelectInput(PPCRegister &index, PPCRegister &fighter) {
  using namespace quick_select_apply_detail;
  opponentControlSuppressP1 = false;
  const char *enabled = std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");
  if (!enabled || std::strcmp(enabled, "1") != 0) return;
  std::lock_guard<std::mutex> lock(mutex);
  uint8_t *b = memory();
  if (!b) return;
  const uint32_t c = context(b);
  if (!c || read(b,c) != 0x8207D3E4u || active()) return;
  static std::FILE *f = std::fopen("opponent-control-test.txt", "w");
  static unsigned logged = 0;
  if (logged < 50 && (fighter.u32 == 0x82900C00u || fighter.u32 == 0x82901840u)) {
    if (f) { std::fprintf(f,"fighter=%08X index=%u\\n",fighter.u32,index.u32); std::fflush(f); }
    ++logged;
  }
  if (fighter.u32 == 0x82900C00u && index.u32 == 8) opponentControlSuppressP1 = true;
  else if (fighter.u32 == 0x82901840u && index.u32 == 9) index.u64 = 8;
}
// END OPPONENT CONTROL IMPLEMENTATION V1
'''
 marker='#include "tekken6_quick_select_apply.inc"\n';assert s2.count(marker)==1;s2=s2.replace(marker,marker+impl,1)
 hook=cs+'[[midasm_hook]]\naddress = 0x822A45C4\nname = "OpponentControlSelectInput"\nregisters = ["r29", "r30"]\n'+ce
 c2=c.replace('[functions]',hook+'[functions]',1)
if a.remove:s2=strip(s2,'\n// BEGIN OPPONENT CONTROL IMPLEMENTATION V1\n','// END OPPONENT CONTROL IMPLEMENTATION V1\n')
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path,content in [(cfg,c2),(src,s2)]:shutil.copy2(path,path.with_name(path.name+'.before-opponent-control-'+stamp));path.write_text(content,encoding='utf-8',newline='\n')
print('Removed.' if a.remove else 'Installed.');print('Regenerate, verify hook, build and package.')
