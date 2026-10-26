// Experimental native practice reload. Include after the Rage menu include.
#pragma once
#include <rex/runtime.h>
#include <cstdint>
#include <cstdio>
#include <mutex>
#include <chrono>
namespace quick_select_apply_detail {
std::mutex mutex;
struct Selection { uint32_t p1=0, p2=0, stage=0; } current, pending;
uint32_t syncedContext=0;
unsigned phase=0, characterMask=0;
bool stageSeen=false;
bool nativeLoadReady=false;
bool needsSync=false;
unsigned confirmMask=0;
std::chrono::steady_clock::time_point started;
bool span(uint32_t a, uint32_t size) {
 return !(a&3) && a>=0x82000000u && size<=0x3E000000u && a<=0xC0000000u-size;
}
uint32_t read(const uint8_t* b,uint32_t a) { return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3]; }
void write(uint8_t* b,uint32_t a,uint32_t v) { for(int i=3;i>=0;--i){b[a+i]=uint8_t(v);v>>=8;} }
uint8_t* memory() { auto* r=rex::Runtime::instance(); return r?r->virtual_membase():nullptr; }
uint32_t context(const uint8_t* b) {
 const uint32_t root=read(b,0x82735C80u), mask=read(b,0x82007560u);
 if(!span(root,912)||read(b,root+12)!=read(b,0x82735C84u)||!(read(b,root+60)&mask))return 0;
 const uint32_t service=read(b,root+908);
 if(!span(service,320))return 0;
 const uint32_t c=read(b,service+312);
 if(!span(c,420)||read(b,c+12)!=read(b,service+316)||!(read(b,c+60)&mask))return 0;
 return c;
}
void log(const char* tag,uint32_t a=0,uint32_t b=0,uint32_t c=0) {
 static std::FILE* f=std::fopen("quick-select-apply-test.txt","w");
 if(f){std::fprintf(f,"%s phase=%u a=%08X b=%u c=%u chars=%u stage=%u\n",tag,phase,a,b,c,characterMask,unsigned(stageSeen));std::fflush(f);}
}
bool active() {
 if(phase && std::chrono::steady_clock::now()-started>std::chrono::seconds(120)) {log("expired");phase=0;}
 return phase!=0;
}
uint32_t index(const uint8_t* b,uint32_t choice) {
 if(choice>=102)return 4;
 const uint32_t fighter=read(b,0x82744AA8u+choice*108);
 const uint32_t ids[]={6,40,9,14};
 for(uint32_t i=0;i<4;++i)if(fighter==ids[i])return i;
 return 4;
}
uint32_t choice(const uint8_t* b,uint32_t selected,uint32_t old) {
 if(selected==4)return old;
 const uint32_t choices[]={12,78,20,30};
 if(selected>=4||old>=102)return 0xFFFFFFFFu;
 if(index(b,old)==selected)return old;
 const uint32_t variant=read(b,0x82744AA8u+old*108+4);
 return choices[selected]+(variant==1?1:0);
}
void store(uint8_t* b,uint32_t c,const Selection& s) {write(b,c+356,s.p1);write(b,c+360,s.p2);write(b,c+352,s.stage);}
void completeOnMenu(uint8_t* b,uint32_t c) {
 if(phase!=2||!nativeLoadReady||characterMask!=3||!stageSeen)return;
 if(read(b,c+356)!=pending.p1||read(b,c+360)!=pending.p2||read(b,c+352)!=pending.stage)return;
 if(read(b,0x82900C00u+88)!=read(b,0x82744AA8u+pending.p1*108)||
    read(b,0x82901840u+88)!=read(b,0x82744AA8u+pending.p2*108))return;
 log("apply-complete-on-menu",c,pending.stage);phase=0;syncedContext=0;
}

}
void QuickSelectMenuOpening(PPCRegister& object) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);auto* b=memory();if(!b)return;
 const uint32_t c=context(b);
 if(c&&read(b,c)==0x8207D3E4u&&object.u32==c+116){completeOnMenu(b,c);needsSync=true;}
}
void QuickSelectSyncMenu(PPCRegister& object) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!needsSync)return;auto* b=memory();if(!b)return;
 const uint32_t c=context(b), records=practice_rage_menu_detail::menuRecords.load(std::memory_order_acquire);
 if(!c||read(b,c)!=0x8207D3E4u||object.u32!=c+116||!records)return;
 if(active())return;
 current={read(b,c+356),read(b,c+360),read(b,c+352)};
 if(current.p1>=102||current.p2>=102||current.stage>=100){syncedContext=0;return;}
 write(b,records+503*96+80,index(b,current.p1));
 write(b,records+508*96+80,index(b,current.p2));
 write(b,records+513*96+80,current.stage==8?0:current.stage==9?1:2);
 needsSync=false;syncedContext=c;log("menu-synchronized",c,current.p1,current.p2);log("build-auto-character-v4");
}
void QuickSelectApplyAction(PPCRegister& object,PPCRegister& id) {
 using namespace quick_select_apply_detail;
 if(id.u32!=516)return;
 std::lock_guard<std::mutex> lock(mutex);auto* b=memory();if(!b)return;
 const uint32_t c=context(b), records=practice_rage_menu_detail::menuRecords.load(std::memory_order_acquire);
 if(active()||!c||c!=syncedContext||read(b,c)!=0x8207D3E4u||!records||object.u32!=0x827BF0D0u){log("apply-rejected",c);return;}
 const uint32_t p1=read(b,records+503*96+80),p2=read(b,records+508*96+80),stage=read(b,records+513*96+80);
 if(p1>4||p2>4||stage>2){log("invalid-selection");return;}
 pending={choice(b,p1,current.p1),choice(b,p2,current.p2),stage==2?current.stage:8+stage};
 if(pending.p1>=102||pending.p2>=102||pending.stage>=100){log("invalid-choice");return;}
 phase=1;characterMask=0;stageSeen=false;nativeLoadReady=false;confirmMask=0;started=std::chrono::steady_clock::now();
 log("apply-requested",c,pending.p1,pending.p2);log("desired-stage",c,pending.stage);
 // Reuse the live native Character Select callback (including its teardown).
 // This register is the dispatch argument, not the menu record's ID.
 id.u64=346;
}
void QuickSelectRedirectMode(PPCRegister& object,PPCRegister& mode) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!active())return;
 if(phase!=1||mode.u32!=4){log("unexpected-mode-cancel",object.u32,mode.u32);phase=0;return;}
 // Native wrapper 4 owns practice, including its character-selection screens.
 // Keep that wrapper and its complete native selection/setup flow.
 phase=2;log("practice-mode-request",object.u32,mode.u32);
}
// Retain the generated hook name so existing installs need only a rebuild.
// This diagnostic observes transitions; it does not bypass any native state.
void QuickSelectBypassScreen(PPCRegister& state,PPCRegister& target) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!active()||phase!=2)return;
 auto* b=memory();if(!b||state.u32<96||!span(state.u32-96,468))return;
 if(read(b,state.u32-96)!=0x8200B3DCu)return;
 const uint32_t next=uint32_t(target.u64>>32),c=context(b);
 static uint32_t lastObject=0,lastTarget=0;
 if(lastObject!=state.u32||lastTarget!=next) {
  lastObject=state.u32;lastTarget=next;
  log("native-state",state.u32-96,next,c);
 }
 if(next==0x82550298u && c && read(b,c)==0x8207D3E4u) {
  // Native slot164 is reached only after the original selection/setup states.
  // Commit after screen confirmation, before native fighter load requests.
  store(b,c,pending);nativeLoadReady=true;
  log("native-selection-complete",c,pending.p1,pending.p2);
 }
}
void QuickSelectLoadCharacter(PPCRegister& object,PPCRegister& side,PPCRegister& selected) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!active()||phase!=2||!nativeLoadReady||side.u32>1)return;
 auto* b=memory();if(!b)return;const uint32_t c=context(b);if(!c||read(b,c)!=0x8207D3E4u)return;
 const uint32_t desired=side.u32?pending.p2:pending.p1;
 selected.u64=desired;store(b,c,pending);characterMask|=1u<<side.u32;
 log("character-request",object.u32,side.u32,desired);
}
void QuickSelectLoadStage(PPCRegister& object,PPCRegister& selected) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!active()||phase!=2||!nativeLoadReady||selected.u32==0xFFFFFFFFu)return;
 // Keep preview/non-match stage requests separate from the tested final request.
 if(selected.u32!=current.stage&&selected.u32!=pending.stage){log("other-stage-request",object.u32,selected.u32);return;}
 auto* b=memory();if(!b)return;const uint32_t c=context(b);if(!c||read(b,c)!=0x8207D3E4u)return;
 selected.u64=pending.stage;store(b,c,pending);stageSeen=true;log("stage-request",object.u32,pending.stage);
}
void QuickSelectObservePractice(PPCRegister& owner,PPCRegister& p1,PPCRegister& p2) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);if(!active()||phase!=2)return;
 auto* b=memory();if(!b||context(b)!=owner.u32||!span(p1.u32,92)||!span(p2.u32,92))return;
 const uint32_t a=read(b,p1.u32+88),d=read(b,p2.u32+88);
 log("practice-setup",owner.u32,a,d);
 if(stageSeen&&a==read(b,0x82744AA8u+pending.p1*108)&&d==read(b,0x82744AA8u+pending.p2*108)) {
  log("apply-complete",owner.u32,pending.stage);phase=0;syncedContext=0;
 }
}

// Entry to the native ready-state character confirmation helper. The routine
// still performs eligibility, costume conversion, selection accounting, sound,
// and state advancement. We supply its hover fighter and normal confirm input.
void QuickSelectAutoConfirmCharacter(PPCRegister& manager,PPCRegister& selector,
                                    PPCRegister& buttons,PPCRegister& fighter) {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);
 if(!active()||phase!=2||nativeLoadReady)return;
 auto* b=memory();if(!b||!span(manager.u32,344)||!span(selector.u32,212))return;
 const uint32_t c=context(b);if(!c||read(b,c)!=0x8207D3E4u)return;
 const uint32_t side=read(b,selector.u32+104),state=read(b,selector.u32+96);
 if(side>1||(state!=2&&state!=5))return;
 // Verify that this ready selector belongs to the native two-side manager.
 const uint32_t ref=manager.u32+(side?124:100);
 if(read(b,ref)!=selector.u32||read(b,ref+4)!=read(b,selector.u32+12)||
    !(read(b,selector.u32+60)&read(b,0x82007560u)))return;
 const uint32_t desired=side?pending.p2:pending.p1;
 const uint32_t variant=read(b,0x82744AA8u+desired*108+4);
 if(variant>1)return; // special costumes stay manual in this focused test
 // A single-fighter practice selection; preserve multi-pick flows.
 if(read(b,selector.u32+120)!=1||read(b,selector.u32+124)!=0)return;
 fighter.u64=read(b,0x82744AA8u+desired*108);
 // Native 822F0F88 selects table[0] for bit 0x04000000 (costume0),
 // and table[2] for bit 0x08000000 (costume1). No global controller input changes.
 buttons.u64=variant?0x08000000u:0x04000000u;
 if(!(confirmMask&(1u<<side))) {
  confirmMask|=1u<<side;log("auto-character-confirm",selector.u32,side,desired);
 }
}
