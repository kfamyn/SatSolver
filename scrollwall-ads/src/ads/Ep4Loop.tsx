import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Caption} from '../components/Caption';
import {Flash, SFX, Shake, SpeedLines} from '../components/fx';
import {Bubble, Chip, PhoneCloseup, Shield, ST_IGNORE, ScreenTimeLimit, Tap, Watermark} from '../components/ui';
import {BedScene} from '../three/BedScene';

// EP4 — 8-second loop. "Me vs Screen Time" -> undefeated -> Wally. Cuts
// straight back to the start so it replays.

export const EP4_DURATION = 240;

const ShotA: React.FC = () => {
  const f = useCurrentFrame();
  const n = f >= 44 ? 3 : f >= 28 ? 2 : f >= 12 ? 1 : 0;
  return (
    <AbsoluteFill style={{background: '#0B0A0F'}}>
      <PhoneCloseup enter={-30}>
        <ScreenTimeLimit />
        <Tap at={12} {...ST_IGNORE} />
        <Tap at={28} {...ST_IGNORE} />
        <Tap at={44} {...ST_IGNORE} />
      </PhoneCloseup>
      <Caption variant="pill" text="me vs screen time" at={0} y={300} size={64} />
      {n > 0 && <Chip text={`ignored x${n}`} y={1250} size={60} color="#FF6B5E" />}
      {[12, 28, 44].map((a) => (
        <SFX key={a} at={a} s="pop" />
      ))}
    </AbsoluteFill>
  );
};

const ShotB: React.FC = () => (
  <AbsoluteFill>
    <BedScene clock="2:13" doug={{expr: 'sneaky', look: [0, -1]}} />
    <Caption variant="giant" text="undefeated 😎" at={2} y={300} size={78} />
  </AbsoluteFill>
);

const ShotC: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <PhoneCloseup enter={-30} shake={4}>
      <Shield />
      <Tap at={10} x={330} y={790} />
      <Tap at={20} x={60} y={110} />
      <Tap at={30} x={340} y={120} />
    </PhoneCloseup>
    <Caption variant="pill" text="wait what's this" at={0} y={300} size={62} />
    {[10, 20, 30].map((a) => (
      <SFX key={a} at={a} s="pop" volume={0.5} />
    ))}
  </AbsoluteFill>
);

const ShotD: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const drop = spring({frame: f - 2, fps, config: {damping: 9, mass: 0.6, stiffness: 160}});
  const y = interpolate(drop, [0, 1], [5, 0]);
  const land = f - 9;
  const squash = land >= 0 && land < 12 ? 1 + Math.sin((land / 12) * Math.PI) * 0.22 : 1;
  return (
    <AbsoluteFill>
      <Shake hits={[9]} amount={40}>
        <BedScene
          clock="2:14"
          doug={{expr: 'shock', look: [0, 0], screen: 'shield', scrolling: false}}
          wally={{position: [0, y, 2.6], expr: 'angry', mouth: 'flat', arms: 'stop', squash}}
          cam={{pos: [0.2, 2.3, 6.4], look: [0, 1.6, 0], fov: 40}}
        />
      </Shake>
      <SpeedLines at={9} x={540} y={900} />
      <Flash at={9} dur={6} />
      <Bubble text="nope." at={18} x={760} y={560} tail="left" size={80} />
      <SFX at={2} s="whoosh" />
      <SFX at={9} s="slam" volume={1} />
      <SFX at={18} s="pop" />
    </AbsoluteFill>
  );
};

export const Ep4Loop: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <Sequence durationInFrames={70}>
      <ShotA />
    </Sequence>
    <Sequence from={70} durationInFrames={50}>
      <ShotB />
    </Sequence>
    <Sequence from={120} durationInFrames={50}>
      <ShotC />
    </Sequence>
    <Sequence from={170} durationInFrames={70}>
      <ShotD />
    </Sequence>
    <Watermark />
  </AbsoluteFill>
);
