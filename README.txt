Airborne recovery and delayed-contact correction

Close the game, extract into C:\Users\Jalen\tekken6-recomp, and run:
 powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\apply_frame_data_air.ps1
This installs, rebuilds, packages and launches. It backs up the active include.
Previous stance/basic readiness logic remains; no HUD/menu/recording changes.

What the supplied four-case capture showed:
- Neutral3~4 has two contacts, with internal script changes. The final contact
  is at animation30; the native reported recovery is54. The reader incorrectly
  classified its airborne flag as requiring a stance input boundary.
- RFF3~4 posts its contact pulse before its final reaction kind is established.
  The former detector ignored that pulse when kind was0, or restarted the
  measurement when kind1 arrived later. Its reported recovery is47.

Changes:
- Accept the early native contact pulse tentatively, retaining the contact
  frame. Still require a settled, matching hit/block reaction before measuring.
- Avoid treating delayed guard classification as a second contact.
- For airborne contacts without basic-input routes across observed pending
  phases, permit the normal recovery endpoint only after the native scheduler
  gate pair agrees at that endpoint and reported recovery stays consistent.
- Cache settled defender readiness while waiting. Native gate bytes by
  themselves are NOT a universal readiness signal. Missing/unknown metadata
  blocks this fallback; observed basic-input routes keep the stance path.
- Retain the earlier common/partial basic-action recognizers for u4,RFFf3,etc.
- Extend the bounded pending window to120 animation frames for slower recovery.

Replay evidence, using actual contact timing in the uploaded trace:
 Neutral3~4 final contact: startup30, block-5, hit+26.
 RFF3~4 contact: startup28, block+6, hit+47.
These are dynamic observed-contact/reaction differences, not a static frame
chart or a promise for other contact timings. On-hit long recovery is measured
from the captured reaction timer, not separately proven for every knockdown,
tech/get-up option or defensive action. Values are not hardcoded for these moves.

Validation:
- All4 captured trials now produce advantage.
- All30 earlier confirmed jab/u4/ws4,4/RFFf3 replay results remain unchanged.
- C++ tests for parser consensus, unsupported predicates, shared tables,
  transient guard timing, preserved startup, pause repeats, premature gate
  refusal, and refusal when basic input routes are possible.
- Wrapper compiles/runs under stub runtime; installer backup/repeat/layout
  checks pass. Windows build and live gameplay still need user validation.

Some unsupported moves may still be unknown or inaccurate. This does not solve
all cancel routes, all animation/action resets or all special hit reactions.
For these delayed airborne results, advantage may appear only after the
attacker reaches recovery. The last hit of the neutral string supplies its
final value; this does not separately validate every intermediate hit.

Please retest neutral3~4 and RFF3~4 on hit/block, then check u4 and RFFf3 once.
No new capture requested. Small event output: practice-frame-air-result.txt.
Rollback: restore src\tekken6_frame_data_trace.inc.before-air-recovery-...
then rebuild and package.
