#!/usr/bin/env python3
"""Install an opt-in recording prompt overlay; leaves native controller prompt untouched."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_app.h';s=f.read_text(encoding='utf-8-sig')
b='// BEGIN RECORD HUD TEST V1\n';e='// END RECORD HUD TEST V1\n';b2='    // BEGIN RECORD HUD CREATE V1\n';e2='    // END RECORD HUD CREATE V1\n';b3='  // BEGIN RECORD HUD MEMBER V1\n';e3='  // END RECORD HUD MEMBER V1\n'
def strip(s,b,e):
 if s.count(b)!=1 or s.count(e)!=1:raise SystemExit('HUD markers missing or inconsistent; no changes made.')
 i=s.index(b);return s[:i]+s[s.index(e,i)+len(e):]
if a.remove:
 for x,y in [(b,e),(b2,e2),(b3,e3)]:s=strip(s,x,y)
else:
 if b in s or b2 in s or b3 in s:raise SystemExit('HUD already installed or partial; no changes made.')
 anchor='class Tekken6App final : public rex::ReXApp {';create='    rex::ReXApp::OnCreateDialogs(drawer);\n';member=' private:\n'
 if s.count(anchor)!=1 or s.count(create)!=1 or s.count(member)!=1:raise SystemExit('Unexpected app layout; no changes made.')
 header='''// BEGIN RECORD HUD TEST V1
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <rex/ui/imgui_dialog.h>
#include <imgui.h>
extern std::atomic<int> selectedRecordSlot;
extern std::atomic<bool> recordSlotActive;
extern std::atomic<bool> recordSlotRecording;
extern std::atomic<bool> opponentToggleTest;
extern std::atomic<unsigned> firstPlaybackState;

class TekkenRecordHud final : public rex::ui::ImGuiDialog {
 public:
  explicit TekkenRecordHud(rex::ui::ImGuiDrawer* drawer) : ImGuiDialog(drawer) {}
 protected:
  void OnDraw(ImGuiIO& io) override {
    const int slot=selectedRecordSlot.load(std::memory_order_acquire);
    if(slot<0 || slot>=3 || !recordSlotActive.load(std::memory_order_acquire)) return;
    const bool recording=recordSlotRecording.load(std::memory_order_acquire);
    const bool controlling=opponentToggleTest.load(std::memory_order_relaxed);
    const bool playing=firstPlaybackState.load(std::memory_order_acquire)==1;
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x*0.5f,io.DisplaySize.y*0.82f),ImGuiCond_Always,ImVec2(0.5f,0.5f));
    ImGui::SetNextWindowBgAlpha(0.80f);
    ImGuiWindowFlags flags=ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_AlwaysAutoResize|
      ImGuiWindowFlags_NoNav|ImGuiWindowFlags_NoMove|ImGuiWindowFlags_NoSavedSettings|ImGuiWindowFlags_NoInputs;
    if(ImGui::Begin("##tekken_record_hud",nullptr,flags)) {
      ImGui::Text("SLOT %d",slot+1);
      if(recording) ImGui::TextUnformatted("Select + X: Finish recording");
      else if(playing) ImGui::TextUnformatted("Playing recording");
      else if(controlling) ImGui::TextUnformatted("Select + X: Start recording");
      else ImGui::TextUnformatted("Select + B: Play recording");
    }
    ImGui::End();
  }
};
// END RECORD HUD TEST V1
'''
 createblock='''    // BEGIN RECORD HUD CREATE V1
    const char* recordHudTest=std::getenv("TEKKEN6_TEST_RECORD_HUD");
    if(drawer && recordHudTest && std::strcmp(recordHudTest,"1")==0)
      recordHud_=std::make_unique<TekkenRecordHud>(drawer);
    // END RECORD HUD CREATE V1
'''
 memberblock='''  // BEGIN RECORD HUD MEMBER V1
  std::unique_ptr<TekkenRecordHud> recordHud_;
  // END RECORD HUD MEMBER V1
'''
 s=s.replace(anchor,header+anchor,1).replace(create,create+createblock,1).replace(member,member+memberblock,1)
backup=f.with_name(f.name+'.before-record-hud-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(s,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Rebuild and package.')
