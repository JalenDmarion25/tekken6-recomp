#pragma once
namespace tekken_stance_rules {
// sub_82286188 reads 32-byte transition records from command+20;
// sub_82287168 schedules their execution using record+24 (not +16).
// Recognize only the observed coherent direct-input prefix. Other layouts,
// shared-table instructions and conflicting execution times remain unsupported.
template<class Word>
uint32_t LegacyBoundary(Word word,uint32_t command,uint32_t animation,int32_t timingOffset) {
 auto valid=[](uint32_t p,uint32_t bytes){return p>=0x90000000u && p<=0xC0000000u-bytes && !(p&3u);};
 if(timingOffset<0 || !valid(command,88))return 0;
 const uint32_t table=word(command+20),duration=word(command+36);
 if(!valid(table,160) || duration>600 || !duration)return 0;
 uint32_t boundary=0,start=0,end=0,buttons=0;
 for(unsigned i=0;i<5;++i) {
   const uint32_t r=table+i*32,kind=word(r),input=word(r+4);
   const uint32_t begin=word(r+16),last=word(r+20),execute=word(r+24),target=word(r+28);
   if(kind>0xFu || (input&0xFFFFFFF0u)!=0x40000000u || !(input&0xFu) ||
      (target&0xFFFFu)!=0x50u || !(target>>16) ||
      !valid(word(r+8),4) || !valid(word(r+12),4) ||
      !execute || begin>execute || execute>last || last>duration ||
      animation<begin || animation>execute)return 0;
   if(i && (execute!=boundary || begin!=start || last!=end))return 0;
   boundary=execute;start=begin;end=last;
   if(!kind && (input&0xFu)==1)buttons|=1;
   if(!kind && (input&0xFu)==2)buttons|=2;
 }
 return buttons==3?boundary:0;
}

struct Result {uint32_t frame=0,records=0,buttons=0,source=0,reason=0;};
// source: 1 established prefix, 2 terminated direct list, 3 shared list.
// reason: 1 pointer, 2 offset/duration, 3 structure/budget, 4 conditions,
// 5 conflicting timings, 6 insufficient supported inputs.
inline bool Valid(uint32_t p,uint32_t bytes){return p>=0x90000000u && p<=0xC0000000u-bytes && !(p&3u);}
template<class Word>
Result Read(Word word,uint32_t command,uint32_t animation,int32_t timingOffset,uint32_t root) {
 Result out{};
 if(!Valid(command,88)){out.reason=1;return out;}
 if(timingOffset<0){out.reason=2;return out;}
 if(const uint32_t legacy=LegacyBoundary(word,command,animation,timingOffset)) {
   out.frame=legacy;out.records=5;out.buttons=3;out.source=1;return out;
 }
 const uint32_t duration=word(command+36);
 if(!duration || duration>600){out.reason=2;return out;}
 uint32_t cursor=word(command+20),resume=0,boundary=0;
 bool shared=false,ended=false;
 for(unsigned budget=0;budget<64;++budget) {
   if(!Valid(cursor,32)){out.reason=1;return out;}
   ++out.records;
   const uint32_t kind=word(cursor);
   if(kind==0x8000u){ended=true;break;}
   if(kind==0x800Cu) {
     if(!resume){out.reason=3;return out;}
     cursor=resume;resume=0;continue;
   }
   if(kind==0x800Bu) {
     // Native scanner has one saved return pointer: do not invent recursion.
     if(resume || !Valid(root,424)){out.reason=3;return out;}
     const uint32_t pool=word(root+420),index=word(cursor+28)>>16;
     if(!Valid(pool,32) || index>(0xC0000000u-pool-32u)/32u){out.reason=1;return out;}
     resume=cursor+32;cursor=pool+index*32;shared=true;continue;
   }
   if(kind>=0x8000u){out.reason=3;return out;}
   const uint32_t begin=word(cursor+16),end=word(cursor+20),execute=word(cursor+24);
   const uint32_t input=word(cursor+4),target=word(cursor+28);
   if(begin>animation || end<animation){cursor+=32;continue;}
   // Only ordinary direct-input rules are interpreted. An active unknown
   // rule could be an earlier cancel; refusing avoids a misleading number.
   if(kind>15 || (input&0xFFFFFFF0u)!=0x40000000u || !(input&15u) ||
      (target&65535u)!=0x50u || !(target>>16)) {out.reason=3;return out;}
   const uint32_t conditions=word(cursor+8),effects=word(cursor+12);
   // sub_82285FC0: 397 is the empty predicate-list terminator.
   // Other predicate programs need separate verification, not an assumed pass.
   if(!Valid(conditions,4) || !Valid(effects,4)){out.reason=1;return out;}
   if(word(conditions)!=397u || word(effects)==16383u){out.reason=4;return out;}
   if(!execute || begin>execute || execute>end || execute<animation ||
      execute>duration || (end>duration && end!=0x7FFFu)){out.reason=2;return out;}
   if(boundary && boundary!=execute){out.reason=5;return out;}
   boundary=execute;
   const uint32_t buttons=input&15u;
   if(!kind && !(buttons&(buttons-1u)))out.buttons|=buttons;
   cursor+=32;
 }
 if(!ended){out.reason=3;return out;}
 if(!boundary || !((out.buttons&3u)==3u || (out.buttons&12u)==12u)){out.reason=6;return out;}
 out.frame=boundary;out.source=shared?3:2;return out;
}
}
