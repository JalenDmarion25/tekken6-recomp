#!/usr/bin/env python3
"""Install an opt-in, read-only trace of native practice menu command events."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--remove',action='store_true');a=p.parse_args()
names=['src/tekken6_quick_select_trace.inc','src/tekken6_quick_select_apply.inc'];root=a.root
files={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
b='// BEGIN DEFENSE COMMAND TRACE V1\n';e='// END DEFENSE COMMAND TRACE V1\n';b2=' // BEGIN DEFENSE COMMAND ACTION TRACE V1\n';e2=' // END DEFENSE COMMAND ACTION TRACE V1\n'
def remove(s,b,e):
 if s.count(b)!=1 or s.count(e)!=1:raise SystemExit('Trace markers missing or inconsistent; no changes made.')
 i=s.index(b);j=s.index(e,i)+len(e);return s[:i]+s[j:]
if a.remove:
 files[names[0]]=remove(files[names[0]],b,e);files[names[1]]=remove(files[names[1]],b2,e2)
else:
 if b in files[names[0]] or b2 in files[names[1]]:raise SystemExit('Trace already installed or partially installed; no changes made.')
 helper='''// BEGIN DEFENSE COMMAND TRACE V1
void TraceDefenseCommandEvent(const char* kind, uint32_t object, uint32_t id,
                              uint32_t action, uint32_t value) {
  const char* enabled=std::getenv("TEKKEN6_TRACE_DEFENSE_COMMAND");
  if (!enabled || std::strcmp(enabled,"1") != 0) return;
  using namespace quick_select_trace_detail;
  std::lock_guard<std::mutex> lock(mutex);
  auto* runtime=rex::Runtime::instance();
  if(!runtime) return;
  const uint8_t* base=runtime->virtual_membase(); if(!base) return;
  static std::FILE* f=std::fopen("defense-command-trace.txt","w");
  static unsigned events=0;
  if(!f || events>=1000) return;
  const uint32_t root=read(base,0x82735C80u);
  uint32_t service=0,ctx=0;
  if(span(root,912) && read(base,root+12)==read(base,0x82735C84u) &&
      (read(base,root+60)&read(base,0x82007560u))) {
    service=read(base,root+908);
    if(span(service,320)) {
      const uint32_t candidate=read(base,service+312);
      if(span(candidate,420) && read(base,candidate+12)==read(base,service+316) &&
          (read(base,candidate+60)&read(base,0x82007560u))) ctx=candidate;
    }
  }
  std::fprintf(f,"EVENT %u %s object=%08X id=%u action=%08X value=%08X context=%08X\\n",
               ++events,kind,object,id,action,value,ctx);
  if(ctx) dump(f,base,"practice-context",ctx,420);
  if(span(object,4)) {
    uint32_t vt=read(base,object);
    if(span(vt,2000)) dump(f,base,"menu-vtable",vt+1880,120);
  }
  std::fflush(f);
}
// END DEFENSE COMMAND TRACE V1
'''
 anchor='void TraceQuickSelectMenu(PPCRegister& object, PPCRegister& id,\n'
 s=files[names[0]]
 if s.count(anchor)!=1:raise SystemExit('Expected menu trace differs; no changes made.')
 s=s.replace(anchor,helper+anchor,1)
 # Invoke in the existing diagnostic hook, without changing any guest register.
 call='''// BEGIN DEFENSE COMMAND TRACE V1
  TraceDefenseCommandEvent("menu",object.u32,id.u32,action.u32,value.u32);
// END DEFENSE COMMAND TRACE V1
'''
 # distinct helper marker required for reversible removal: embed call into helper-owned marker separately
 s=s.replace('  // Record action rows associated with practice menus; avoid per-frame rows.','  TraceDefenseCommandEvent("menu",object.u32,id.u32,action.u32,value.u32); // DEFENSE COMMAND TRACE CALL V1\n  // Record action rows associated with practice menus; avoid per-frame rows.',1)
 files[names[0]]=s
 needle=' using namespace quick_select_apply_detail;\n // RECORD SLOTS MENU TEST V1:'
 if files[names[1]].count(needle)!=1:raise SystemExit('Expected slot menu dispatcher differs; no changes made.')
 files[names[1]]=files[names[1]].replace(needle,' using namespace quick_select_apply_detail;\n'+b2+' TraceDefenseCommandEvent("apply",object.u32,id.u32,0,0);\n'+e2+' // RECORD SLOTS MENU TEST V1:',1)
# Remove the separately marked call when uninstalling.
if a.remove:
 call='  TraceDefenseCommandEvent("menu",object.u32,id.u32,action.u32,value.u32); // DEFENSE COMMAND TRACE CALL V1\n'
 if files[names[0]].count(call)!=1:raise SystemExit('Trace call missing; no changes made.')
 files[names[0]]=files[names[0]].replace(call,'',1)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-defense-command-trace-'+stamp));f.write_text(files[n],encoding='utf-8',newline='\n')
print('Updated command trace. Rebuild and package.')
