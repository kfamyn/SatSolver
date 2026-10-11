#!/usr/bin/env bash
# Synthesizes every sound effect used in the ads. All original, no licensing.
set -euo pipefail
cd "$(dirname "$0")/public/sfx"
R=48000
fx() { ffmpeg -v error -y -f lavfi -i "aevalsrc='$2':s=$R:d=$3" -af "$4" "$1.wav"; }

# Heavy wall slam: pitch-dropping sub + crunchy noise transient
fx slam "0.9*sin(2*PI*(38+140*exp(-t*18))*t)*exp(-t*5)+0.6*(random(0)*2-1)*exp(-t*28)" 0.9 "lowpass=f=2200,acompressor=threshold=-12dB:ratio=6,volume=1.6,afade=t=out:st=0.6:d=0.3"
# Whoosh: filtered noise swell
fx whoosh "(random(0)*2-1)*sin(PI*t/0.42)^2" 0.42 "bandpass=f=900:width_type=o:w=2.2,highpass=f=250,volume=2.2"
# Pop: quick pitched blip for text/cards
fx pop "sin(2*PI*(520+1100*exp(-t*45))*t)*exp(-t*22)" 0.16 "volume=0.9"
# Coin: two bright partials, the second slightly late
fx coin "0.5*sin(2*PI*1568*t)*exp(-t*9)+if(gt(t,0.075),0.55*sin(2*PI*2093*(t-0.075))*exp(-(t-0.075)*7),0)" 0.7 "volume=0.9"
# Payment success chime (original two-note rise)
fx chime "if(lt(t,0.16),0.5*sin(2*PI*1318.5*t)*exp(-t*4),0)+if(gt(t,0.13),0.55*(sin(2*PI*1760*(t-0.13))+0.25*sin(2*PI*3520*(t-0.13)))*exp(-(t-0.13)*3.2),0)" 1.3 "aecho=0.8:0.5:60:0.25,volume=0.9"
# Card declined: two low buzzes
fx decline "if(lt(mod(t,0.22),0.15),0.6*sgn(sin(2*PI*150*t))*(1-mod(t,0.22)/0.15),0)" 0.44 "lowpass=f=1400,volume=0.7"
# Tick for counters
fx tick "(random(0)*2-1)*exp(-t*300)" 0.03 "highpass=f=2500,volume=0.8"
# Riser into reveals
fx riser "(0.35*sin(2*PI*(200+900*t*t)*t)+0.25*(random(0)*2-1))*(t/0.9)^2" 0.9 "highpass=f=180,lowpass=f=5000,volume=1.2"
# Boing for Wally's bounce
fx boing "sin(2*PI*(180+120*sin(2*PI*9*t)*exp(-t*5))*t)*exp(-t*6)" 0.55 "volume=0.8"
echo "sfx ok"
