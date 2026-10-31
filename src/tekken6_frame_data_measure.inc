#pragma once
// Isolated-contact pilot. All offsets/outcomes are grounded in the V2 trace.
namespace tekken_frame_measure {
struct Fighter {uint32_t frame,animation,attack,contact,reaction,state;};
struct Sample {Fighter p[2];};
struct Meter {
 Sample previous{};bool initialized=false,pending=false,blocked=false;
 unsigned attacker=0,age=0;int readyAttack=-1,readyDefend=-1;
 uint64_t tick=0,result=0;
 void Reset(){*this=Meter{};}
 bool Step(const Sample& s) {
  const uint64_t before=result;
  if(!initialized){previous=s;initialized=true;return false;}
  bool changed=false,continuous=true;unsigned advance=0;
  for(unsigned i=0;i<2;++i) {
    const auto& a=previous.p[i];const auto& b=s.p[i];
    if(a.frame!=b.frame || a.animation!=b.animation)changed=true;
    if(b.frame>a.frame){const auto delta=b.frame-a.frame;if(delta>1)continuous=false;else advance=1;}
    else if(b.frame<a.frame){if(b.frame!=1)continuous=false;else advance=1;}
  }
  if(changed && !advance)continuous=false;
  if(!continuous){pending=false;result=0;previous=s;return before!=result;}
  tick+=advance;
  // Only a fresh contact latches startup. No input-poll or wall-clock counting.
  for(unsigned i=0;i<2;++i) {
    const auto& p=s.p[i];
    if(p.attack && (p.contact==6 || p.contact==8) && previous.p[i].contact==0) {
      if(p.animation==0 || p.animation>120){pending=false;result=0;continue;}
      result=p.animation; // Startup observed at the actual contact frame.
      attacker=i;pending=p.contact==8;blocked=false;age=0;
      readyAttack=-1;readyDefend=-1;
    }
  }
  if(pending) {
    age+=advance;
    const auto& a=s.p[attacker];const auto& d=s.p[1-attacker];
    if(d.reaction==1 && (d.state==226 || d.state==228))blocked=true;
    // These are the neutral transitions verified in the isolated jab trace.
    if(a.attack==0 && a.state==128 && readyAttack<0)readyAttack=int(tick);
    if(blocked && d.reaction==0 && d.state==128 && readyDefend<0)readyDefend=int(tick);
    if(readyAttack>=0 && readyDefend>=0) {
      const int advantage=readyDefend-readyAttack;
      if(advantage>=-120 && advantage<=120)
        result=(result&0xFFFFu)|(uint64_t(uint16_t(int16_t(advantage)))<<16)|(uint64_t(1)<<32);
      pending=false;
    }
    if(age>180)pending=false;
  }
  previous=s;return result!=before;
 }
};
}
