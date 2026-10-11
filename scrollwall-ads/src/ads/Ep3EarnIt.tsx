import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Caption} from '../components/Caption';
import {clamp, Flash, SFX} from '../components/fx';
import {AppClip, Bubble, Chip, PhoneCloseup, Shield, Watermark} from '../components/ui';
import {CoinRain, DeskSet} from '../three/sets';
import {Cam, Stage, StudioLights} from '../three/Stage';
import {Doug3D, Doug3DProps} from '../three/Doug3D';
import {Wally3D, Wally3DProps} from '../three/Wally3D';
import {BedScene} from '../three/BedScene';
import {FOOTAGE} from '../footage';

// EP3 — "Earn it"
// Phone face down, very disciplined, for four minutes. Then Wally makes him
// earn it, and the payoff is the FocusCard tap.

export const EP3_DURATION = 600;

const DESK_CAM = {pos: [0.7, 2.35, 4.4] as [number, number, number], look: [0.15, 1.55, 0.2] as [number, number, number], fov: 38};

const DeskScene: React.FC<{
  doug?: Doug3DProps;
  wally?: Wally3DProps | null;
  daylight?: number;
  coinsFrame?: number;
  cam?: {pos: [number, number, number]; look: [number, number, number]; fov?: number};
}> = ({doug, wally, daylight = 1, coinsFrame, cam = DESK_CAM}) => (
  <Stage bg="#2A2440">
    <Cam {...cam} />
    <StudioLights key_={1.8} ambient={0.6} />
    <DeskSet daylight={daylight} phoneDown={!wally} />
    <Doug3D position={[0, 0.2, -0.1]} legs="sit" arms="book" scrolling={false} {...doug} />
    {wally && <Wally3D {...wally} />}
    {coinsFrame !== undefined && <CoinRain frame={coinsFrame} />}
  </Stage>
);

const ShotA: React.FC = () => (
  <AbsoluteFill>
    <DeskScene doug={{expr: 'focus', look: [0, -1]}} />
    <Caption variant="pill" text={'studying 📚\n(phone face down. very disciplined.)'} at={4} y={300} size={54} />
  </AbsoluteFill>
);

const ShotB: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <DeskScene
        doug={{expr: 'sneaky', arms: f > 10 ? 'reach' : 'book', look: [1, -0.5]}}
        cam={{pos: [0.9, 2.2, 3.4], look: [0.35, 1.45, 0.4], fov: 36}}
      />
      <Caption variant="pill" text="...for 4 minutes" at={6} y={300} size={62} />
    </AbsoluteFill>
  );
};

const ShotC: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <PhoneCloseup enter={-20}>
      <Shield />
    </PhoneCloseup>
    <Caption variant="pill" text="hi wall 🙂" at={10} y={300} size={62} />
    <SFX at={0} s="slam" volume={0.35} />
  </AbsoluteFill>
);

const ShotD: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const drop = spring({frame: f - 4, fps, config: {damping: 10, mass: 0.6}});
  const y = interpolate(drop, [0, 1], [4, 1.02]);
  const land = f - 12;
  const squash = land >= 0 && land < 12 ? 1 + Math.sin((land / 12) * Math.PI) * 0.25 : 1;
  return (
    <AbsoluteFill>
      <DeskScene
        doug={{expr: f > 20 ? 'sad' : 'shock', arms: 'book', look: [1, 0]}}
        wally={{position: [0.85, y, 0.85], rotationY: -0.7, scale: 0.42, squash, expr: 'angry', mouth: 'flat', arms: f > 20 ? 'point' : 'stop'}}
      />
      <Flash at={12} dur={5} />
      <Bubble text="earn it." at={22} x={760} y={820} tail="right" size={64} />
      <SFX at={4} s="whoosh" />
      <SFX at={12} s="slam" volume={0.6} />
      <SFX at={22} s="pop" />
    </AbsoluteFill>
  );
};

const LAPSE = 130;
const ShotE: React.FC = () => {
  const f = useCurrentFrame();
  const k = interpolate(f, [0, 90], [0, 1], clamp);
  const secs = Math.round((1 - k) * 30 * 60);
  const timer = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
  const nod = Math.abs(Math.sin(f / 5)) * 0.05;
  return (
    <AbsoluteFill>
      <DeskScene
        daylight={1 - k * 0.8}
        doug={{expr: k >= 1 ? 'happy' : 'focus', look: [0, -1], arms: k >= 1 ? 'up' : 'book'}}
        wally={{position: [0.85, 1.02, 0.85], rotationY: -0.7, scale: 0.42, squash: 1 + nod, expr: 'happy', mouth: 'smile', arms: k >= 1 ? 'up' : 'cross'}}
        coinsFrame={f - 90}
        cam={{pos: [0.7 - k * 0.2, 2.45, 4.6 - k * 0.3], look: DESK_CAM.look, fov: 38}}
      />
      <Chip text={k >= 1 ? '+50 🪙' : `📚 ${timer}`} y={1250} size={64} color={k >= 1 ? '#F0B55C' : '#fff'} at={0} />
      <Caption variant="pill" text="30 min of actual focus later" at={4} out={88} y={300} size={58} />
      <Caption variant="giant" text="*+50* focuscoins" at={96} y={300} size={76} />
      {new Array(14).fill(0).map((_, i) => (
        <SFX key={i} at={90 + i * 3 + 8} s="coin" volume={0.35} />
      ))}
    </AbsoluteFill>
  );
};

// The real app: unlock 5 min for 40 coins, tilt to spend, paid.
const ShotF: React.FC = () => {
  const c = FOOTAGE.tiltToSpend;
  return (
    <AbsoluteFill style={{background: '#0B0A0F'}}>
      <PhoneCloseup enter={-20}>
        <AppClip src={c.file} from={c.from} to={c.to} />
      </PhoneCloseup>
      <Caption variant="pill" text="paying for tiktok with *focus* 💳" at={6} y={300} size={58} />
      <SFX at={c.chimeAt} s="chime" />
    </AbsoluteFill>
  );
};

const ShotG: React.FC = () => {
  const f = useCurrentFrame();
  const left = 5 * 60 - Math.floor(f / 30) - 2;
  return (
    <AbsoluteFill>
      <BedScene
        clock="6:12"
        lamp={1}
        doug={{expr: 'happy', look: [0, -1]}}
        wally={{position: [1.2, 0, 0.3], rotationY: -0.5, scale: 0.85, expr: 'neutral', mouth: 'smirk', arms: 'cross', shades: true}}
        cam={{pos: [0.9, 2.6, 5.6], look: [0.4, 1.6, -0.6], fov: 38}}
      />
      <Chip text={`🔓 ${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`} y={1250} size={60} />
      <Caption variant="pill" text="guilt-free scrolling hits different" at={8} y={300} size={58} />
    </AbsoluteFill>
  );
};

export const Ep3EarnIt: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <Sequence durationInFrames={80}>
      <ShotA />
    </Sequence>
    <Sequence from={80} durationInFrames={50}>
      <ShotB />
    </Sequence>
    <Sequence from={130} durationInFrames={50}>
      <ShotC />
    </Sequence>
    <Sequence from={180} durationInFrames={80}>
      <ShotD />
    </Sequence>
    <Sequence from={260} durationInFrames={LAPSE}>
      <ShotE />
    </Sequence>
    <Sequence from={390} durationInFrames={100}>
      <ShotF />
    </Sequence>
    <Sequence from={490} durationInFrames={110}>
      <ShotG />
    </Sequence>
    <Watermark />
  </AbsoluteFill>
);
