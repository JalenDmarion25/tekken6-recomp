#!/usr/bin/env python3
"""Add an opt-in experimental native command-list entry to the slot menu."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root
names=['src/tekken6_quick_select_roster.inc','src/tekken6_quick_select_menu_records.inc','src/tekken6_quick_select_apply.inc']
s={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
if any('COMMAND MENU PROBE V1' in x for x in s.values()):raise SystemExit('Command probe already installed or partial; no changes made.')
def sub(n,old,new):
 if s[n].count(old)!=1:raise SystemExit('Unexpected source in '+n+'; no changes made.')
 s[n]=s[n].replace(old,new,1)
r,m,f=names
sub(r,'constexpr uint32_t recordSlotStride=5;','constexpr uint32_t recordSlotStride=6; // COMMAND MENU PROBE V1')
sub(m,'    const uint32_t parent[] = {297,350,382};','''    // COMMAND MENU PROBE V1: preserve the normal slot layout unless opted in.
    const char* commandProbe=std::getenv("TEKKEN6_TEST_COMMAND_MENU");
    const bool commandEnabled=commandProbe && std::strcmp(commandProbe,"1")==0;
    const uint32_t parent[] = {297,350,382};''')
sub(m,'node(root,297,"Record/Playback",parent[mode],4,root+1,quick,0);','node(root,297,"Record/Playback",parent[mode],commandEnabled?5:4,root+1,quick,0);')
sub(m,'''             slot?root+slot:0,slot<3?root+2+slot:0);
    }
  }
}''','''             slot?root+slot:0,slot<3?root+2+slot:0);
      if(commandEnabled) {
        write(base,records+(root+4)*recordSize+24,root+5);
        node(root+5,346,"Opponent Command List",root,0,0,root+4,0);
      }
    }
  }
}''')
sub(f,'''   if(!c || read(b,c)!=0x8207D3E4u || active() || object.u32!=0x827BF0D0u ||
      recordSlotRecording.load(std::memory_order_acquire)) return;
   const int previous=selectedRecordSlot.load(std::memory_order_acquire);''','''   if(!c || read(b,c)!=0x8207D3E4u || active() || object.u32!=0x827BF0D0u ||
      recordSlotRecording.load(std::memory_order_acquire)) return;
   // COMMAND MENU PROBE V1: request the same native action used in Defensive Training.
   if(choice==5) {
     const char* commandProbe=std::getenv("TEKKEN6_TEST_COMMAND_MENU");
     if(commandProbe && std::strcmp(commandProbe,"1")==0) {
       if(std::FILE* trace=std::fopen("command-menu-probe.txt","a")) {
         std::fprintf(trace,"native-action=386 context=%08X slot=%d\\n",c,selectedRecordSlot.load());std::fclose(trace);
       }
       id.u64=386;
     }
     return;
   }
   const int previous=selectedRecordSlot.load(std::memory_order_acquire);''')
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-command-menu-probe-'+stamp));f.write_text(s[n],encoding='utf-8',newline='\n')
print('Installed command menu probe. Backups use .before-command-menu-probe-'+stamp)
