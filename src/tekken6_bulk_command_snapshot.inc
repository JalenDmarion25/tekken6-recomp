#pragma once
#include <set>
namespace tekken_bulk_snapshot {
// Native sub_822979C0: root+460 commands, root+464 count, 88-byte stride.
// Capture loaded tables once, without selecting/executing any attacks.
inline bool Valid(uint32_t p,unsigned bytes){return p>=0x90000000u && p<=0xC0000000u-bytes && !(p&3u);}
inline void Capture(const uint8_t* b,uint32_t fighter) {
 static const bool enabled=[](){const char* f=std::getenv("TEKKEN6_SNAPSHOT_COMMANDS");return f && !std::strcmp(f,"1");}();
 if(!enabled)return;
 static std::set<uint32_t> roots;
 static unsigned words=0;
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 for(unsigned off:{128u,256u}) {
   const uint32_t root=word(fighter+off);
   if(roots.size()>=4 || roots.count(root) || !Valid(root,512))continue;
   const uint32_t table=word(root+460),count=word(root+464),shared=word(root+420);
   if(!count || count>4096 || !Valid(table,count*88) || word(table)!=0x8200ED68u)continue;
   auto* f=std::fopen("practice-command-snapshot.txt",roots.empty()?"w":"a");if(!f)return;
   roots.insert(root);std::fprintf(f,"ROOT %08X fighter=%08X offset=%u table=%08X count=%u shared=%08X\n",root,fighter,off,table,count,shared);
   std::set<std::pair<uint32_t,unsigned>> dumped;std::set<uint32_t> rules;
   auto dump=[&](uint32_t a,unsigned bytes){
     if(words+bytes/4>500000 || !Valid(a,bytes) || !dumped.insert({a,bytes}).second)return;
     std::fprintf(f,"B %08X %u",a,bytes);
     for(unsigned j=0;j<bytes;j+=4)std::fprintf(f," %08X",word(a+j));
     words+=bytes/4;std::fputc('\n',f);
   };
   dump(root,512);
   for(unsigned i=0;i<count && words<490000;++i){
     const uint32_t command=table+i*88;dump(command,88);
     uint32_t cursor=word(command+20),resume=0;
     for(unsigned n=0;n<256 && words<490000;++n){
       if(!Valid(cursor,32))break;
       if(!rules.insert(cursor).second){if(resume){cursor=resume;resume=0;continue;}break;}
       dump(cursor,32);const uint32_t kind=word(cursor);
       if(kind==0x8000u)break;
       if(kind==0x800Cu){if(!resume)break;cursor=resume;resume=0;continue;}
       if(kind==0x800Bu){
         const uint32_t index=word(cursor+28)>>16;
         if(resume || !Valid(shared,32) || index>(0xC0000000u-shared-32u)/32u)break;
         resume=cursor+32;cursor=shared+index*32;continue;
       }
       const uint32_t cond=word(cursor+8),effect=word(cursor+12);
       if(Valid(cond,8))for(unsigned k=0;k<64;++k){
         const uint32_t p=cond+k*8;if(!Valid(p,8))break;
         dump(p,8);if(word(p)==397)break;
       }
       dump(effect,64);cursor+=32;
     }
   }
   std::fprintf(f,"END root=%08X cumulative_words=%u cap=%u\n",root,words,unsigned(words>=490000));
   std::fclose(f);
 }
}
}
