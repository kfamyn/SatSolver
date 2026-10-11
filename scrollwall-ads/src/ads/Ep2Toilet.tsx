import React from 'react';
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Caption} from '../components/Caption';
import {clamp, SFX, Shake} from '../components/fx';
import {Bubble, Chip, PhoneCloseup, Shield, Tap, Watermark} from '../components/ui';
import {Bathroom} from '../three/sets';
import {Cam, Stage, StudioLights} from '../three/Stage';
import {Doug3D, Doug3DProps} from '../three/Doug3D';
import {Wally3D, Wally3DProps} from '../three/Wally3D';

// EP2 — "Quick bathroom break"
// 2 minutes becomes 47. The wall comes back. Doug's legs don't.

export const EP2_DURATION = 420;

const BathScene: React.FC<{
  doug?: Doug3DProps;
  wally?: Wally3DProps | null;
  cam?: {pos: [number, number, number]; look: [number, number, number]; fov?: number};
}> = ({doug, wally, cam = {pos: [0.9, 2.3, 4.6], look: [0.2, 1.45, -0.6], fov: 38}}) => (
  <Stage bg="#DDEFF2">
    <Cam {...cam} />
    <StudioLights key_={2.2} ambient={0.75} keyColor="#FFFFFF" rim="#A98BDF" />
    <Bathroom />
    <Doug3D position={[0, 0.27, -0.5]} legs="sit" {...doug} />
    {wally && <Wally3D {...wally} />}
  </Stage>
);

const ShotA: React.FC = () => {
  const f = useCurrentFrame();
  const k = interpolate(f, [0, 75], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <BathScene doug={{expr: 'tired', look: [0, -1]}} cam={{pos: [0.9 - k * 0.2, 2.3, 4.6 - k * 0.6], look: [0.2, 1.45, -0.6], fov: 38}} />
      <Caption variant="pill" text={'pov: "quick" bathroom break 🚽'} at={4} y={300} size={60} />
      <Chip text="⏱ 2 min" y={1250} at={20} />
      <SFX at={20} s="pop" volume={0.5} />
    </AbsoluteFill>
  );
};

const ShotB: React.FC = () => {
  const f = useCurrentFrame();
  const k = interpolate(f, [0, 45], [0, 1], {...clamp, easing: (t) => t * t});
  const mins = Math.round(2 + k * 45);
  return (
    <AbsoluteFill>
      <BathScene doug={{expr: k > 0.7 ? 'dead' : 'tired', look: [0, -1], headTilt: -k * 0.15}} cam={{pos: [0.5, 2.1, 3.0], look: [0.05, 1.6, -0.6], fov: 36}} />
      <Chip text={`⏱ ${mins} min`} y={1250} color={mins > 30 ? '#FF6B5E' : '#fff'} />
      <Caption variant="giant" text="*47 min* later" at={46} y={300} size={80} />
      {new Array(8).fill(0).map((_, i) => (
        <SFX key={i} at={i * 5} s="tick" volume={0.5} />
      ))}
    </AbsoluteFill>
  );
};

const ShotC: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <PhoneCloseup enter={-20}>
      <Shield app="Instagram" />
      <Tap at={30} x={195} y={709} />
    </PhoneCloseup>
    <Caption variant="pill" text={"the wall's back.\n3 coins left 💀"} at={8} y={300} size={60} />
    <SFX at={0} s="slam" volume={0.4} />
    <SFX at={30} s="decline" volume={0.6} />
  </AbsoluteFill>
);

const ShotD: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const slide = spring({frame: f - 4, fps, config: {damping: 12, mass: 0.6}});
  const wx = interpolate(slide, [0, 1], [3.2, 1.25]);
  const standing = f > 40;
  const fall = f > 70 ? spring({frame: f - 70, fps, config: {damping: 8}}) : 0;
  return (
    <AbsoluteFill>
      <Shake hits={[72]} amount={14}>
        <BathScene
          doug={{
            expr: standing ? 'shock' : 'tired',
            legs: standing ? 'stand' : 'sit',
            arms: standing ? 'shrug' : 'phone',
            screen: 'shield',
            wobble: standing ? 1 : 0,
            look: standing ? [0, 0] : [1, 0],
            squash: 1 + fall * 0.12,
          }}
          wally={{position: [wx, 0, -0.2], rotationY: -0.6, tilt: 0.12, expr: 'smug', mouth: 'smirk', arms: f > 40 ? 'point' : 'cross', scale: 0.9}}
          cam={{pos: [0.8, 2.2, 5.0], look: [0.45, 1.4, -0.5], fov: 38}}
        />
      </Shake>
      <Bubble text={'legs still\nwork? 🙂'} at={14} out={60} x={780} y={760} tail="right" size={58} />
      <Caption variant="giant" text="legs: *offline*" at={66} y={320} size={78} highlight="#FF6B5E" />
      <SFX at={6} s="whoosh" />
      <SFX at={14} s="pop" />
      <SFX at={44} s="boing" />
      <SFX at={72} s="slam" volume={0.4} />
    </AbsoluteFill>
  );
};

const ShotE: React.FC = () => {
  const f = useCurrentFrame();
  const x = interpolate(f, [0, 110], [0, -2.6], clamp);
  return (
    <AbsoluteFill>
      <BathScene
        doug={{expr: 'sad', legs: 'walk', arms: 'down', wobble: 1, position: [x, 0, 0.2]} as Doug3DProps}
        wally={{position: [1.2, 0, -0.2], rotationY: -0.3, expr: 'happy', mouth: 'grin', arms: 'wave', scale: 0.9}}
        cam={{pos: [0.4, 2.2, 5.4], look: [0, 1.35, -0.4], fov: 38}}
      />
      <Caption variant="pill" text="the toilet scroll era is over 🫡" at={10} y={300} size={58} />
    </AbsoluteFill>
  );
};

export const Ep2Toilet: React.FC = () => (
  <AbsoluteFill style={{background: '#0B0A0F'}}>
    <Sequence durationInFrames={75}>
      <ShotA />
    </Sequence>
    <Sequence from={75} durationInFrames={65}>
      <ShotB />
    </Sequence>
    <Sequence from={140} durationInFrames={60}>
      <ShotC />
    </Sequence>
    <Sequence from={200} durationInFrames={110}>
      <ShotD />
    </Sequence>
    <Sequence from={310} durationInFrames={110}>
      <ShotE />
    </Sequence>
    <Watermark />
  </AbsoluteFill>
);
