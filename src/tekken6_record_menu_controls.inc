// RECORD MENU CONTROLS V1: native actions and shared Rage values.
#pragma once
void SyncRecordPlaybackRage(uint8_t* b,uint32_t c,uint32_t object,uint32_t records) {
 using namespace quick_select_apply_detail;
 const char* flag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
 if(!flag || std::strcmp(flag,"1")!=0 || !records || !c ||
    read(b,c)!=0x8207D3E4u || object!=c+116 || active())return;
 for(uint32_t mode=0;mode<3;++mode) {
   const uint32_t first=quick_select_roster::recordExtrasBase+mode*quick_select_roster::recordExtrasStride;
   const uint32_t nativeResetRows[]={332,364,397}; // RECORD RESET TOGGLE V1
   write(b,records+first*96+80,read(b,records+nativeResetRows[mode]*96+80));
   write(b,records+(first+1)*96+80,read(b,records+496*96+80));
   write(b,records+(first+4)*96+80,read(b,records+499*96+80));
 }
}
void TrackRecordPlaybackRage(PPCRegister& record,PPCRegister& value) {
 using namespace quick_select_apply_detail;
 if(value.u32>1)return;
 const char* flag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
 if(!flag || std::strcmp(flag,"1")!=0)return;
 std::lock_guard<std::mutex> lock(mutex);auto* b=memory();if(!b)return;
 const uint32_t c=context(b),records=practice_rage_menu_detail::menuRecords.load(std::memory_order_acquire);
 if(!c || !records || read(b,c)!=0x8207D3E4u || active())return;
 for(uint32_t mode=0;mode<3;++mode) {
   const uint32_t first=quick_select_roster::recordExtrasBase+mode*quick_select_roster::recordExtrasStride;
   // RECORD RESET TOGGLE V1: write the same setting consumed by native practice.
   if(record.u32==records+first*96) {
     const uint32_t nativeResetRows[]={332,364,397};
     write(b,records+nativeResetRows[mode]*96+80,value.u32);
     return;
   }
   for(uint32_t side=0;side<2;++side) {
     if(record.u32!=records+(first+(side?4:1))*96)continue;
     write(b,records+(side?499:496)*96+80,value.u32);
     if(side)practiceP2Rage.store(value.u32==1,std::memory_order_relaxed);
     else practiceP1Rage.store(value.u32==1,std::memory_order_relaxed);
     return;
   }
 }
}
void RouteRecordPlaybackControlAction(PPCRegister& object,PPCRegister& id) {
 using namespace quick_select_apply_detail;
 const char* flag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
 if(!flag || std::strcmp(flag,"1")!=0)return;
 if(id.u32<quick_select_roster::recordExtrasBase ||
    id.u32>=quick_select_roster::totalCount)return;
 const uint32_t choice=(id.u32-quick_select_roster::recordExtrasBase)%quick_select_roster::recordExtrasStride;
 if(choice!=7 && choice!=8)return; // RECORD RESET TOGGLE V1: reset is a selector.
 std::lock_guard<std::mutex> lock(mutex);auto* b=memory();if(!b)return;
 const uint32_t c=context(b);
 if(!c || read(b,c)!=0x8207D3E4u || active() || object.u32!=0x827BF0D0u ||
    !recordPlaybackModeActive.load(std::memory_order_acquire))return;
 // Reuse the native Free Style callbacks: POSITION RESET, CHARACTER SELECT,
 // and RETURN TO MAIN MENU, including the native confirmation/teardown.
 id.u64=choice==7?346u:347u; // Only native exit actions are dispatched.
}
