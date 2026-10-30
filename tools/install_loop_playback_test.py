#!/usr/bin/env python3
"""Loop recordings until Select+B and remove the command-list menu entry."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root
names=['src/tekken6_quick_select_menu_records.inc','src/tekken6_guest_hooks.cpp','src/tekken6_app.h'];s={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
if any('LOOP PLAYBACK TEST V1' in x for x in s.values()):raise SystemExit('Loop playback already installed or partial; no changes made.')
def replace(n,old,new):
 if s[n].count(old)!=1:raise SystemExit('Unexpected source in '+n+'; no changes made.')
 s[n]=s[n].replace(old,new,1)
m,c,h=names
replace(m,'''    const char* commandProbe=std::getenv("TEKKEN6_TEST_COMMAND_MENU");
    const bool commandEnabled=commandProbe && std::strcmp(commandProbe,"1")==0;''','''    // LOOP PLAYBACK TEST V1: do not add the command-list entry.
    const bool commandEnabled=false;''')
replace(c,'''      if (playCombo && !previousPlayCombo && !recording &&
          selectedRecordSlot.load(std::memory_order_acquire)>=0 &&
          firstPlaybackState.load(std::memory_order_acquire)!=1 &&
          (weighted ? PrepareWeightedPlayback() : firstPlaybackCount>0)) {''','''      // LOOP PLAYBACK TEST V1: a fresh Select+B edge stops active playback.
      const char* loopEnv=std::getenv("TEKKEN6_TEST_LOOP_PLAYBACK");
      const bool loopEnabled=loopEnv && std::strcmp(loopEnv,"1")==0;
      if (loopEnabled && playCombo && !previousPlayCombo && !recording &&
          firstPlaybackState.load(std::memory_order_acquire)==1) {
        firstPlaybackState.store(2,std::memory_order_release);
        firstPlaybackCurrent.store(0,std::memory_order_relaxed);
        weightedPlaybackActive=false;
        log("play-stopped",firstPlaybackPosition);
      } else if (playCombo && !previousPlayCombo && !recording &&
          selectedRecordSlot.load(std::memory_order_acquire)>=0 &&
          firstPlaybackState.load(std::memory_order_acquire)!=1 &&
          (weighted ? PrepareWeightedPlayback() : firstPlaybackCount>0)) {''')
replace(c,'''        } else {
          firstPlaybackState.store(2,std::memory_order_release); log("play-complete",firstPlaybackPosition);
        }
      }
    }
  } else {
  // BEGIN RECORD CAPTURE TEST V1''','''        } else if (loopEnabled && (!weighted || PrepareWeightedPlayback())) {
          // Pick again on each pass, retaining the current selected recording.
          firstPlaybackPosition=0;
          firstPlaybackCurrent.store(0,std::memory_order_relaxed);
          log("play-loop",weighted?weightedPlaybackCount:firstPlaybackCount);
        } else {
          firstPlaybackState.store(2,std::memory_order_release); log("play-complete",firstPlaybackPosition);
        }
      }
    }
  } else {
  // BEGIN RECORD CAPTURE TEST V1''')
replace(h,'else if(playing) ImGui::TextUnformatted("Playing recording");','else if(playing) ImGui::TextUnformatted("Select + B: Stop playback"); // LOOP PLAYBACK TEST V1')
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-loop-playback-'+stamp));f.write_text(s[n],encoding='utf-8',newline='\n')
print('Installed loop playback test. Backups use .before-loop-playback-'+stamp)
