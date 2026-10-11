import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Caption} from '../components/Caption';
import {clamp, Flash, SFX, Shake} from '../components/fx';
import {Bubble, PAY_BUTTON, PaySheet, PhoneCloseup, Shield, ST_IGNORE, ST_IGNORE_TODAY, ScreenTimeLimit, Tap, Watermark, Zzz} from '../components/ui';
import {BED_CAM, BedScene} from '../three/BedScene';

// EP1 — "Ignore Limit"
// Doug ignores Apple Screen Time every night. Then he meets a wall with no
// ignore button.

export const EP1_DURATION = 640;

const pushIn = (frame: number, dur: number, amount = 1.2) => {
  const k = interpolate(frame, [0, dur], [0, 1], clamp);
  return {
    pos: [BED_CAM.pos[0] - k * amount * 0.3, BED_CAM.pos[1] - k * amount * 0.25, BED_CAM.pos[2] - k * amount] as [number, number, number],
    look: BED_CAM.look,
    fov: BED_CAM.fov,
  };
};

const ShotA: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <BedScene clock="11:58" cam={pushIn(f, 80)} doug={{expr: 'tired', look: [0, -1]}} />
      <Caption variant="pill" text={'me at 11:58pm:\n"5 more minutes"'} at={4} y={330} size={66} />
    </AbsoluteFill>
  );
};

const ShotB: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <PhoneCloseup enter={-20}>
      <ScreenTimeLimit sheetAt={34} />
      <Tap at={22} {...ST_IGNORE} />
      <Tap at={62} {...ST_IGNORE_TODAY} />
    </PhoneCloseup>
    <Caption variant="pill" text="screen time trying its best 🥲" at={4} y={300} size={58} />
    <SFX at={22} s="pop" />
    <SFX at={34} s="whoosh" volume={0.4} />
    <SFX at={62} s="pop" />
  </AbsoluteFill>
);

const TIMELAPSE = 80;
const ShotC: React.FC = () => {
  const f = useCurrentFrame();
  // 23:58 -> 03:47, ticking faster as it goes
  const k = interpolate(f, [0, 50], [0, 1], {...clamp, easing: (t) => t * t});
  const mins = Math.round(23 * 60 + 58 + k * (3 * 60 + 49));
  const h = Math.floor(mins / 60) % 24;
  const m = mins % 60;
  const clock = `${h % 12 === 0 ? 12 : h % 12}:${String(m).padStart(2, '0')}`;
  return (
    <AbsoluteFill>
      <Shake hits={[52]} amount={18}>
        <BedScene
          clock={clock}
          moonY={0.25 - k * 0.5}
          cam={{pos: [0.3, 2.0, 2.3], look: [0, 1.55, -1.0], fov: 36}}
          doug={{expr: k > 0.6 ? 'dead' : 'tired', look: [0, -1], headTilt: k * 0.12}}
        />
      </Shake>
      <Caption variant="giant" text="*3:47* AM 💀" at={52} y={330} size={84} />
      {new Array(8).fill(0).map((_, i) => (
        <SFX key={i} at={i * 6} s="tick" volume={0.5} />
      ))}
      <SFX at={52} s="slam" volume={0.35} />
    </AbsoluteFill>
  );
};

const ShotD: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <BedScene clock="11:58" cam={pushIn(f, 60, 0.8)} doug={{expr: 'sneaky', look: [0, -1]}} />
      <Caption variant="pill" text={"so i got an app\nthat *can't* be ignored 😈"} at={3} y={330} size={64} />
    </AbsoluteFill>
  );
};

const ShotE: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: '#0B0A0F'}}>
      <PhoneCloseup enter={-20} shake={f > 40 ? 3 : 0}>
        <Shield />
        {/* frantic searching taps */}
        <Tap at={30} x={330} y={790} />
        <Tap at={40} x={60} y={790} />
        <Tap at={48} x={340} y={90} />
        <Tap at={56} x={70} y={120} />
        <Tap at={64} x={200} y={600} />
      </PhoneCloseup>
      <Caption variant="pill" text="wait. where's the ignore button?? 🤨" at={22} y={300} size={56} />
      {[30, 40, 48, 56, 64].map((a) => (
        <SFX key={a} at={a} s="pop" volume={0.5} />
      ))}
    </AbsoluteFill>
  );
};

const ShotF: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rise = spring({frame: f - 6, fps, config: {damping: 9, mass: 0.7, stiffness: 140}});
  const y = interpolate(rise, [0, 1], [-2.8, 0]);
  const land = f - 14;
  const squash = land >= 0 && land < 14 ? 1 + Math.sin((land / 14) * Math.PI) * 0.18 * (1 - land / 14) : 1;
  return (
    <AbsoluteFill>
      <Shake hits={[14]} amount={26}>
        <BedScene
          clock="11:59"
          cam={{pos: [1.0, 2.6, 6.2], look: [0.45, 1.65, -0.4], fov: 38}}
          doug={{expr: 'shock', look: [1, 0], screen: 'shield', scrolling: false}}
          wally={{position: [1.35, y, 0.6], rotationY: -0.5, scale: 0.9, expr: f > 30 ? 'smug' : 'angry', mouth: f > 30 ? 'smirk' : 'flat', arms: 'cross', squash}}
        />
      </Shake>
      <Flash at={14} dur={6} />
      <Bubble text={"there isn't one."} at={32} x={760} y={700} tail="right" size={60} />
      <SFX at={4} s="whoosh" />
      <SFX at={14} s="slam" volume={0.9} />
      <SFX at={16} s="boing" volume={0.5} />
      <SFX at={32} s="pop" />
    </AbsoluteFill>
  );
};

const ShotG: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <PhoneCloseup enter={-20}>
      <PaySheet at={2} result="declined" resultAt={34} coins={10} balance={0} />
      <Tap at={30} {...PAY_BUTTON} />
    </PhoneCloseup>
    <Caption variant="pill" text="balance: 0 coins 💀" at={40} y={300} size={60} />
    <SFX at={2} s="whoosh" volume={0.4} />
    <SFX at={30} s="pop" />
    <SFX at={34} s="decline" />
  </AbsoluteFill>
);

const ShotH: React.FC = () => {
  const f = useCurrentFrame();
  const drift = interpolate(f, [0, 90], [0, 0.4], clamp);
  return (
    <AbsoluteFill>
      <BedScene
        clock="12:00"
        asleep
        cam={{pos: [1.0 - drift, 4.0, 5.4], look: [0.35, 1.25, -0.4], fov: 38}}
        wally={{position: [0.85, 0, 0.95], rotationY: -0.5, scale: 0.85, expr: 'happy', mouth: 'smile', arms: f > 18 ? 'wave' : 'down', nightcap: true}}
      />
      <Zzz x={330} y={900} />
      <Bubble text={'earn it\ntomorrow ✌️'} at={22} x={700} y={640} tail="right" size={56} />
      <SFX at={22} s="pop" />
    </AbsoluteFill>
  );
};

export const Ep1IgnoreLimit: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <Sequence durationInFrames={80}>
      <ShotA />
    </Sequence>
    <Sequence from={80} durationInFrames={90}>
      <ShotB />
    </Sequence>
    <Sequence from={170} durationInFrames={TIMELAPSE}>
      <ShotC />
    </Sequence>
    <Sequence from={250} durationInFrames={60}>
      <ShotD />
    </Sequence>
    <Sequence from={310} durationInFrames={80}>
      <ShotE />
    </Sequence>
    <Sequence from={390} durationInFrames={90}>
      <ShotF />
    </Sequence>
    <Sequence from={480} durationInFrames={70}>
      <ShotG />
    </Sequence>
    <Sequence from={550} durationInFrames={90}>
      <ShotH />
    </Sequence>
    <Watermark />
  </AbsoluteFill>
);
