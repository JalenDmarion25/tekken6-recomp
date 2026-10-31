#pragma once
#include "tekken6_frame_data_contacts_measure.inc"
// STANCE ACTION GATE TRACE V1
#include "tekken6_frame_data_stance_gate.inc"
namespace tekken_contacts_live {
std::atomic<uint64_t> result{0};std::mutex mutex;
tekken_contacts_measure::Meter meter;uint32_t owner=0;
}
bool TekkenFrameDataPracticeActive(){return practiceRageOwner.load(std::memory_order_acquire)!=0;}
uint64_t TekkenFrameDataResult(){return tekken_contacts_live::result.load(std::memory_order_acquire);}
void CaptureTekkenFrameDataCandidates(uint32_t held) {
 using namespace tekken_contacts_live;
 std::lock_guard<std::mutex> lock(mutex);
 const uint32_t currentOwner=practiceRageOwner.load(std::memory_order_acquire);
 if(owner!=currentOwner){owner=currentOwner;meter.Reset();result.store(0,std::memory_order_release);}
 if(!currentOwner)return;
 auto* runtime=rex::Runtime::instance();auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;
 tekken_stance_gate::Capture(b,currentOwner,held);
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 tekken_contacts_measure::Sample sample{};
 for(unsigned i=0;i<2;++i){const uint32_t a=i?0x82901840u:0x82900C00u;
   sample.p[i]={word(a+0xDC),word(a+0xC4),word(a+0x1AC),word(a+0x1D0),word(a+0x1D4),word(a+0x214),
     word(a+0x1C4),word(a+0x1E8),word(a+0x60),word(a+0x3CC),word(a+0x10C),word(a+0x108),word(a+0x1A8)};
 }
 // Small read-only metadata capture for the unresolved stance-action timing.
 // A command pointer change identifies the next script phase, not a new attack.
 static uint32_t lastCommand[2]={};static bool tracking[2]={};static unsigned metadata=0;
 for(unsigned i=0;i<2;++i) {
   const auto& p=sample.p[i];
   if(p.state&0x400u)tracking[i]=true;
   if(tracking[i] && p.command!=lastCommand[i] && metadata<160 &&
      p.command>=0x80000000u && p.command<=0xC0000000u-88u) {
     if(auto* f=std::fopen("practice-stance-action-metadata.txt","a")) {
       std::fprintf(f,"phase=%u side=%u command=%08X action=%08X animation=%u segment=%u state=%08X recovery=%u\n",
         ++metadata,i+1,p.command,p.action,p.animation,p.frame,p.state,p.recovery);
       std::fputs("command-words-000-to-054",f);
       for(unsigned off=0;off<88;off+=4)std::fprintf(f," %08X",word(p.command+off));
       std::fputc('\n',f);std::fclose(f);
     }
   }
   lastCommand[i]=p.command;
   if(!(p.state&0x400u) && p.state==128 && !p.attack)tracking[i]=false;
 }
 if(meter.Step(sample)) {
   result.store(meter.result,std::memory_order_release);
   static unsigned logged=0;
   if(meter.result && logged++<300)if(auto* f=std::fopen("practice-frame-contacts.txt","a")) {
     std::fprintf(f,"event=%u class=%s startup=%u",logged,meter.outcome==2?"guard":meter.outcome==1?"hit":meter.outcome==3?"unsupported":"pending",unsigned(meter.result&0xFFFFu));
     if(meter.result&(uint64_t(1)<<32))std::fprintf(f," advantage=%+d",int(int16_t((meter.result>>16)&0xFFFFu)));
     else std::fputs(" advantage=--",f);
     std::fputc('\n',f);std::fclose(f);
   }
 }
}
