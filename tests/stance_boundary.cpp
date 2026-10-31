#include <cstdint>
#include <cassert>
#include <map>
#include "../src/tekken6_frame_data_stance_measure.inc"
#include "../src/tekken6_frame_data_stance_rules.inc"
using namespace tekken_contacts_measure;
int main(){
 std::map<uint32_t,uint32_t> words;
 const uint32_t c=0xA0000000,t=c+0x100;
 words[c+20]=t;words[c+36]=57;
 for(unsigned i=0;i<5;++i){auto r=t+32*i;words[r]=0;words[r+4]=0x40000000u+(i==0?1:i==1?2:3);words[r+8]=c+0x300;words[r+12]=c+0x400;words[r+16]=20;words[r+20]=55;words[r+24]=35;words[r+28]=0x10050;}
 auto read=[&](uint32_t a){return words[a];};
 assert(tekken_stance_rules::Boundary(read,c,20,0)==35);
 assert(!tekken_stance_rules::Boundary(read,c,19,0));
 assert(!tekken_stance_rules::Boundary(read,c,36,0));
 assert(!tekken_stance_rules::Boundary(read,c,20,-1));
 assert(!tekken_stance_rules::Boundary(read,0,20,0));
 words[t+24]=34;assert(!tekken_stance_rules::Boundary(read,c,20,0));words[t+24]=35;
 words[t]=0x800B;assert(!tekken_stance_rules::Boundary(read,c,20,0));words[t]=0;
 words[t+28]=0x10041;assert(!tekken_stance_rules::Boundary(read,c,20,0));words[t+28]=0x10050;
 for(unsigned side=0;side<2;++side)for(bool hit:{false,true}){
   Meter m;Sample s{};auto& a=s.p[side];auto& d=s.p[1-side];
   a.action=111;a.animation=15;a.state=0x403;a.attack=1;a.recovery=53;d.health=180;d.animation=99;
   m.Step(s);
   a.animation=16;d.pulse=1;d.kind=hit?12:1;d.state=hit?226:94;
   a.dealt=d.taken=hit?21:0;if(hit)d.health-=21;
   m.Step(s);assert(m.result==16);
   a.animation=17;d.pulse=0;d.animation=1;d.recovery=hit?30:19;m.Step(s);assert(m.pending);
   // Pause repeats do not advance the measurement.
   for(unsigned k=0;k<100;++k)m.Step(s);
   a.animation=20;a.frame=1;a.attack=0;a.recovery=57;a.dealt=d.taken=0;a.stanceBoundary=35;d.animation=4;
   m.Step(s);assert(m.result&(uint64_t(1)<<32));assert(int16_t(m.result>>16)==(hit?11:0));
   assert(!m.pending);
   m.Reset();assert(!m.result && !m.pending);
 }
 // Missing stance metadata remains unknown, rather than using animation length.
 Meter m;Sample s{};s.p[0].action=4;s.p[0].attack=1;s.p[0].state=0x400;s.p[0].animation=15;s.p[1].health=100;m.Step(s);
 s.p[0].animation=16;s.p[1].kind=1;s.p[1].state=94;s.p[1].pulse=1;m.Step(s);
 s.p[0].animation=17;s.p[1].animation=1;s.p[1].recovery=19;s.p[1].pulse=0;m.Step(s);
 s.p[0].animation=47;m.Step(s);assert(m.result==16 && !m.pending);
}
