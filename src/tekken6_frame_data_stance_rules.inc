#pragma once
namespace tekken_stance_rules {
// sub_82286188 reads 32-byte transition records from command+20;
// sub_82287168 schedules their execution using record+24 (not +16).
// Recognize only the observed coherent direct-input prefix. Other layouts,
// shared-table instructions and conflicting execution times remain unsupported.
template<class Word>
uint32_t Boundary(Word word,uint32_t command,uint32_t animation,int32_t timingOffset) {
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
}
