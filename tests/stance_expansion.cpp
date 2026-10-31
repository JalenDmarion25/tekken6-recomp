#include <cstdint>
#include <cassert>
#include <map>
#include "../src/tekken6_frame_data_stance_expand_measure.inc"
#include "../src/tekken6_frame_data_stance_expand_rules.inc"
using namespace tekken_contacts_measure;
int main(){
 std::map<uint32_t,uint32_t> words;
 const uint32_t c=0xA0000000,t=c+0x100;
 words[c+20]=t;words[c+36]=57;
 for(unsigned i=0;i<5;++i){auto r=t+32*i;words[r]=0;words[r+4]=0x40000000u+(i==0?1:i==1?2:3);words[r+8]=c+0x300;words[r+12]=c+0x400;words[r+16]=20;words[r+20]=55;words[r+24]=35;words[r+28]=0x10050;}
 auto read=[&](uint32_t a){return words[a];};
 assert(tekken_stance_rules::LegacyBoundary(read,c,20,0)==35);
 assert(!tekken_stance_rules::LegacyBoundary(read,c,19,0));
 assert(!tekken_stance_rules::LegacyBoundary(read,c,36,0));
 assert(!tekken_stance_rules::LegacyBoundary(read,c,20,-1));
 assert(!tekken_stance_rules::LegacyBoundary(read,0,20,0));
 words[t+24]=34;assert(!tekken_stance_rules::LegacyBoundary(read,c,20,0));words[t+24]=35;
 words[t]=0x800B;assert(!tekken_stance_rules::LegacyBoundary(read,c,20,0));words[t]=0;
 words[t+28]=0x10041;assert(!tekken_stance_rules::LegacyBoundary(read,c,20,0));words[t+28]=0x10050;
 for(unsigned side=0;side<2;++side)for(bool hit:{false,true})for(bool marked:{false,true}){
   Meter m;Sample s{};auto& a=s.p[side];auto& d=s.p[1-side];
   a.action=111;a.animation=15;a.state=marked?0x403:128;a.stanceBoundary=marked?0:35;a.attack=1;a.recovery=53;d.health=180;d.animation=99;
   m.Step(s);
   a.animation=16;d.pulse=1;d.kind=hit?12:1;d.state=hit?226:94;
   a.dealt=d.taken=hit?21:0;if(hit)d.health-=21;
   m.Step(s);assert(m.result==16);
   a.animation=17;d.pulse=0;d.animation=1;d.recovery=hit?30:19;m.Step(s);assert(m.pending || (m.result&(uint64_t(1)<<32)));
   // Pause repeats do not advance the measurement.
   for(unsigned k=0;k<100;++k)m.Step(s);
   a.animation=20;a.frame=1;a.attack=0;a.recovery=57;a.dealt=d.taken=0;a.stanceBoundary=35;d.animation=4;
   m.Step(s);assert(m.result&(uint64_t(1)<<32));assert(int16_t(m.result>>16)==(hit?11:0));
   assert(!m.pending);
   m.Reset();assert(!m.result && !m.pending);
 }
 // Variable-size terminated direct list, not the legacy five-entry prefix.
 words[t+64]=0x8000;
 words[c+0x300]=397;words[c+0x400]=0;
 auto result=tekken_stance_rules::Read(read,c,20,0,0);
 assert(result.frame==35 && result.source==2 && result.records==3);
 // Kick inputs also qualify; the original recognizer requires punch inputs.
 words[t+4]=0x40000004;words[t+36]=0x40000008;
 result=tekken_stance_rules::Read(read,c,20,0,0);
 assert(result.frame==35 && result.buttons==12);
 words[t+56]=36;result=tekken_stance_rules::Read(read,c,20,0,0);
 assert(!result.frame && result.reason==5);words[t+56]=35;
 words[c+0x300]=99;result=tekken_stance_rules::Read(read,c,20,0,0);
 assert(!result.frame && result.reason==4);words[c+0x300]=397;
 // A shared block returns with 0x800C to its parent, as the native scanner does.
 const uint32_t parent=c+0x1000,pool=c+0x2000,root=c+0x3000;
 words[c+20]=parent;words[root+420]=pool;
 words[parent]=0x800B;words[parent+28]=0x00010050;words[parent+32]=0x8000;
 for(unsigned i=0;i<16;++i)words[pool+32+i*4]=words[t+i*4];
 words[pool+96]=0x800C;
 result=tekken_stance_rules::Read(read,c,20,0,root);
 assert(result.frame==35 && result.source==3 && result.records==5);
 words[pool+32]=0x800B;
 result=tekken_stance_rules::Read(read,c,20,0,root);
 assert(!result.frame && result.reason==3);
 // Cycles/nested shared blocks cannot cause an unbounded scan.
 words[pool+60]=0x00010050;
 result=tekken_stance_rules::Read(read,c,20,0,root);assert(!result.frame);
 // Invalid pointers are rejected before invoking the reader on that pointer.
 auto checked=[&](uint32_t addr){assert(addr>=0x90000000u && addr<0xC0000000u);return words[addr];};
 words[c+20]=0xFFFFFFF0u;result=tekken_stance_rules::Read(checked,c,20,0,root);assert(!result.frame);
 // Missing stance metadata remains unknown, rather than using animation length.
 Meter m;Sample s{};s.p[0].action=4;s.p[0].attack=1;s.p[0].state=0x400;s.p[0].animation=15;s.p[1].health=100;m.Step(s);
 s.p[0].animation=16;s.p[1].kind=1;s.p[1].state=94;s.p[1].pulse=1;m.Step(s);
 s.p[0].animation=17;s.p[1].animation=1;s.p[1].recovery=19;s.p[1].pulse=0;m.Step(s);
 s.p[0].animation=47;m.Step(s);assert(m.result==16 && !m.pending);
}
