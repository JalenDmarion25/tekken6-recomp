#pragma once
namespace tekken_contacts_measure {
struct Fighter {uint32_t frame,animation,attack,dealt,taken,kind,state,recovery,health,pulse,action,command,sequence;};
struct Sample {Fighter p[2];};
struct Meter {
 Sample previous{};bool initialized=false,pending=false;
 unsigned attacker=0,startup=0,pendingType=0;uint32_t health=0,attackRecovery=0,action=0;
 uint64_t result=0;unsigned outcome=0; // 1 hit, 2 guard, 3 unsupported recovery
 void Reset(){*this=Meter{};}
 bool Step(const Sample& s) {
   if(!initialized){previous=s;initialized=true;return false;}
   const uint64_t before=result;bool event=false;
   for(unsigned i=0;i<2;++i) {
     const auto& a=s.p[i];const auto& d=s.p[1-i];const auto& pa=previous.p[i];const auto& pd=previous.p[1-i];
     if(!a.attack)continue;
     const bool pulse=d.kind && d.pulse && d.pulse!=pd.pulse;
     const bool hit=a.dealt && d.taken && (a.dealt!=pa.dealt || d.taken!=pd.taken || d.health<pd.health);
     const bool guard=d.kind==1 && pd.kind!=1 && !a.dealt && !d.taken;
     if(!(pulse || hit || guard))continue;
     pending=false;outcome=0;result=0;event=true;
     if(!a.animation || a.animation>120)continue;
     startup=a.animation;result=startup;
     // A stance/airborne command path can be actionable before animation end.
     // Do not reuse an ordinary standing recovery calculation for that path.
     if(a.state&0x400u){outcome=3;continue;}
     pendingType=d.kind==12 && a.dealt && d.taken?1:
       d.kind==1 && !a.dealt && !d.taken && d.health==pd.health?2:0;
     if(!pendingType){outcome=3;continue;}
     attacker=i;health=d.health;attackRecovery=a.recovery;action=a.action;pending=true;
   }
   if(pending) {
     const auto& a=s.p[attacker];const auto& d=s.p[1-attacker];
     const bool damageMatches=pendingType==2?(!a.dealt && !d.taken):(a.dealt && d.taken);
     if(!a.attack || !damageMatches || d.health!=health || a.animation<startup ||
        a.animation>startup+6 || a.recovery!=attackRecovery || a.action!=action || (a.state&0x400u)) {
       pending=false;outcome=3;
     } else if(a.animation>startup && !d.pulse && d.animation>0 && d.animation<=2 &&
               ((pendingType==2 && d.kind==1 && d.state==94) ||
                (pendingType==1 && d.kind==12 && d.state==226))) {
       // The contact notification may arrive while the preceding reaction is
       // still present. Wait for its animation counter to reset before pairing.
       if(a.recovery>=a.animation && d.recovery>=d.animation && a.recovery<=600 && d.recovery<=600) {
         const int advantage=int(d.recovery-d.animation)-int(a.recovery-a.animation);
         if(advantage>=-120 && advantage<=120) {
           result=uint64_t(startup)|(uint64_t(uint16_t(int16_t(advantage)))<<16)|(uint64_t(1)<<32);
           outcome=pendingType;event=true;
         }
       }
       pending=false;
     }
   }
   previous=s;return event || result!=before;
 }
};
}
