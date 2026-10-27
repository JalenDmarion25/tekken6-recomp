#!/usr/bin/env python3
"""Install a reversible, opt-in trace of input lookup indices and callers."""
from pathlib import Path
from datetime import datetime
import argparse, shutil, re
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');p.add_argument('--verify-generated',action='store_true');a=p.parse_args();root=a.root
call='TraceFighterInputLookup(ctx.r3);'
if a.verify_generated:
 for f in (root/'generated/default').glob('tekken6_recomp.*.cpp'):
  s=f.read_text(encoding='utf-8-sig');m=re.search(r'DEFINE_REX_FUNC\(sub_82267F90\)\s*\{(.*?)(?=\nDEFINE_REX_FUNC|\Z)',s,re.S)
  if m and call in m.group(1): print('PASS: input lookup hook emitted');raise SystemExit(0)
 raise SystemExit('Hook absent from generated code; regenerate before building.')
cfg=root/'tekken6_config.toml';src=root/'src/tekken6_guest_hooks.cpp';c=cfg.read_text(encoding='utf-8-sig');s=src.read_text(encoding='utf-8-sig')
cs='# BEGIN FIGHTER INPUT LOOKUP TRACE V1\n';ce='# END FIGHTER INPUT LOOKUP TRACE V1\n';ss='// BEGIN FIGHTER INPUT LOOKUP TRACE V1\n';se='// END FIGHTER INPUT LOOKUP TRACE V1\n'
def strip(x,start,end):
 if x.count(start)!=1 or x.count(end)!=1:raise SystemExit('Trace markers missing or inconsistent; no files changed.')
 i=x.index(start);j=x.index(end,i)+len(end);return x[:i]+x[j:]
if a.remove: c2=strip(c,cs,ce);s2=strip(s,ss,se);s2=strip(s2,'  // BEGIN FIGHTER INPUT LOG V1\n','  // END FIGHTER INPUT LOG V1\n')
else:
 if cs in c or ss in s: raise SystemExit('Already installed or partial installation; no files changed.')
 if re.search(r'(?im)^\s*address\s*=\s*0x0*82267f90\b',c):raise SystemExit('Hook address already in use; no files changed.')
 needle='void TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)\n{\n'
 if s.count(needle)!=1 or c.count('[functions]')!=1: raise SystemExit('Unexpected project layout; no files changed.')
 block='''// BEGIN FIGHTER INPUT LOOKUP TRACE V1
thread_local uint32_t fighterInputLookupIndex = 0xFFFFFFFFu;
void TraceFighterInputLookup(PPCRegister &index) {
  fighterInputLookupIndex = index.u32;
}
// END FIGHTER INPUT LOOKUP TRACE V1
'''
 log='''  // BEGIN FIGHTER INPUT LOG V1
  if (const char *tracePath = std::getenv("TEKKEN6_FIGHTER_INPUT_TRACE")) {
    if (*tracePath && object.u32 >= 0x82000000u && object.u32 < 0x83000000u) {
      static std::mutex traceMutex;
      std::lock_guard<std::mutex> lock(traceMutex);
      static std::FILE *file = std::fopen(tracePath, "w");
      static unsigned count = 0;
      static std::map<uint64_t, uint32_t> previous;
      const uint64_t key = (uint64_t(fighterInputLookupIndex) << 32) | object.u32;
      const auto entry = previous.find(key);
      const bool changed = entry == previous.end() || entry->second != buttons.u32;
      if (changed) previous[key] = buttons.u32;
      if (file && changed && count < 20000) {
        std::fprintf(file, "%u index=%u caller=%08X input=%08X\\n", ++count,
                     fighterInputLookupIndex, object.u32, buttons.u32);
        std::fflush(file);
      }
    }
  }
  // END FIGHTER INPUT LOG V1
'''
 s2=s.replace(needle,block+needle+log,1)
 hook=cs+'[[midasm_hook]]\naddress = 0x82267F90\nname = "TraceFighterInputLookup"\nregisters = ["r3"]\n'+ce
 c2=c.replace('[functions]',hook+'[functions]',1)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path,content in [(cfg,c2),(src,s2)]:
 shutil.copy2(path,path.with_name(path.name+'.before-fighter-input-trace-'+stamp));path.write_text(content,encoding='utf-8',newline='\n')
print('Removed' if a.remove else 'Installed');print('Regenerate, verify generated hook, build and package.')
