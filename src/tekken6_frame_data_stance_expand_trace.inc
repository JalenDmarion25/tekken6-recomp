#pragma once
#include <cstdio>
#include <cstdlib>
#include <cstring>
namespace tekken_stance_expand_trace {
template<class Word>
void Capture(Word word,uint32_t owner,uint32_t held,const tekken_contacts_measure::Sample& s,
             const tekken_contacts_measure::Meter& meter,const tekken_stance_rules::Result* rules,bool changed) {
 const char* flag=std::getenv("TEKKEN6_TRACE_STANCE_EXPAND");
 if(!flag || std::strcmp(flag,"1"))return;
 static std::FILE* f=nullptr;static unsigned total=0,number=0,left=0,phases=0;
 static uint32_t lastOwner=0,lastCommand[2]={};
 if(total>=6000 || number>=80)return;
 if(owner!=lastOwner){left=0;lastCommand[0]=lastCommand[1]=0;lastOwner=owner;}
 if(changed && meter.result && !(meter.result&(uint64_t(1)<<32))) {
   ++number;left=120;lastCommand[0]=lastCommand[1]=0;
 }
 if(!left)return;
 if(!f){f=std::fopen("practice-stance-expanded-trace.txt","w");if(!f)return;
   std::fputs("STANCE EXPANSION TRACE V1; input-hook samples, not assumed simulation frames\n"
     "Fields: segment animation attack dealt taken kind state recovery health pulse action command sequence boundary offset root\n",f);}
 --left;++total;
 std::fprintf(f,"sample=%u contact=%u held=%08X result=%016llX outcome=%u pending=%u ready=%u\n",
   total,number,held,static_cast<unsigned long long>(meter.result),meter.outcome,unsigned(meter.pending),meter.readyFrame);
 for(unsigned i=0;i<2;++i){const auto& p=s.p[i];const uint32_t a=i?0x82901840u:0x82900C00u;
   const uint32_t root=word(a+0x84);
   const uint32_t fields[]={p.frame,p.animation,p.attack,p.dealt,p.taken,p.kind,p.state,p.recovery,p.health,p.pulse,p.action,p.command,p.sequence,p.stanceBoundary,word(a+0x19C),root};
   std::fprintf(f,"P%u",i+1);for(auto v:fields)std::fprintf(f," %08X",v);
   std::fprintf(f," source=%u reason=%u records=%u buttons=%X\n",rules[i].source,rules[i].reason,rules[i].records,rules[i].buttons);
   if(p.command!=lastCommand[i] && phases<512 && tekken_stance_rules::Valid(p.command,88)) {
     ++phases;std::fprintf(f,"COMMAND side=%u address=%08X",i+1,p.command);
     for(unsigned j=0;j<88;j+=4){std::fprintf(f," %08X",word(p.command+j));}
     std::fputc('\n',f);
     uint32_t cursor=word(p.command+20),resume=0;
     for(unsigned j=0;j<64;++j) {
       if(!tekken_stance_rules::Valid(cursor,32)){std::fputs("RULE INVALID\n",f);break;}
       const uint32_t kind=word(cursor);
       std::fprintf(f,"RULE side=%u address=%08X",i+1,cursor);
       for(unsigned k=0;k<32;k+=4){std::fprintf(f," %08X",word(cursor+k));}
       std::fputc('\n',f);
       if(kind==0x8000u)break;
       if(kind==0x800Cu){if(!resume)break;cursor=resume;resume=0;continue;}
       if(kind==0x800Bu){
         if(resume || !tekken_stance_rules::Valid(root,424))break;
         const uint32_t pool=word(root+420),index=word(cursor+28)>>16;
         if(!tekken_stance_rules::Valid(pool,32) || index>(0xC0000000u-pool-32u)/32u)break;
         resume=cursor+32;cursor=pool+index*32;continue;
       }
       const uint32_t cond=word(cursor+8),effect=word(cursor+12);
       if(tekken_stance_rules::Valid(cond,64)) {
         std::fprintf(f,"CONDITIONS address=%08X",cond);
         for(unsigned k=0;k<64;k+=8){const auto op=word(cond+k);std::fprintf(f," %08X %08X",op,word(cond+k+4));if(op==397)break;}
         std::fputc('\n',f);
       }
       if(tekken_stance_rules::Valid(effect,4))std::fprintf(f,"EFFECT address=%08X word=%08X\n",effect,word(effect));
       cursor+=32;
     }
   }
   lastCommand[i]=p.command;
 }
 std::fflush(f);
}
}
