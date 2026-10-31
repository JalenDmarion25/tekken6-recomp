#pragma once
namespace tekken_advantage_measure {
struct Fighter {uint32_t frame,animation,attack,dealt,taken,kind,state,recovery,health;};
struct Sample {Fighter p[2];};
struct Meter {
 Sample previous{};bool initialized=false,pending=false;
 unsigned attacker=0,age=0,startup=0,pendingType=0;
 uint32_t health=0,attackRecovery=0;
 uint64_t result=0;unsigned outcome=0; // 0 pending/unknown, 1 confirmed normal hit, 2 confirmed standing guard
 void Reset(){*this=Meter{};}
 void Begin(unsigned side,const Fighter& a,const Fighter& d,unsigned type) {
   attacker=side;age=0;startup=a.animation;health=d.health;attackRecovery=a.recovery;
   pendingType=type;pending=true;result=startup;outcome=0;
 }
 bool Step(const Sample& s) {
   if(!initialized){previous=s;initialized=true;return false;}
   const auto before=result;bool event=false;
   for(unsigned i=0;i<2;++i) {
     const auto& a=s.p[i];const auto& d=s.p[1-i];const auto& pa=previous.p[i];const auto& pd=previous.p[1-i];
     if(!a.attack)continue;
     if(d.kind && d.kind!=pd.kind){result=0;outcome=0;pending=false;}
     if(a.dealt && !pa.dealt && a.animation>0 && a.animation<=120) {
       // A damaging contact supplies startup, regardless of damage amount.
       // Only the normal standing-hit response below supplies advantage.
       result=a.animation;outcome=0;pending=false;event=true;
       if(d.kind==12 && d.taken)Begin(i,a,d,1);
     }
     if(d.kind==1 && pd.kind!=1 && !a.dealt && !d.taken && d.health==pd.health &&
        a.animation>0 && a.animation<=120) {
       Begin(i,a,d,2);event=true;
     }
   }
   if(pending) {
     const auto& a=s.p[attacker];const auto& d=s.p[1-attacker];
     ++age;
     const bool damageMatches=pendingType==2?(!a.dealt && !d.taken):(a.dealt && d.taken);
     if(!a.attack || !damageMatches || d.health!=health || a.animation<startup ||
        a.animation>startup+4 || a.recovery!=attackRecovery || age>6)pending=false;
     else if((pendingType==2 && d.kind==1 && d.state==94) ||
             (pendingType==1 && d.kind==12 && d.state==226)) {
       // Both outcomes use the same signed, attacker-perspective recovery difference.
       // Values are engine counters, never elapsed host time or visual idle transitions.
       if(a.recovery>=a.animation && d.recovery>=d.animation &&
          a.recovery<=600 && d.recovery<=600 && d.animation>0) {
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
