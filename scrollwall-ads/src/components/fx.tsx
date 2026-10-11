import React from 'react';
import {AbsoluteFill, Audio, interpolate, random, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../brand';

export const sp = (frame: number, fps: number, delay = 0, damping = 12, mass = 0.6) =>
  spring({frame: frame - delay, fps, config: {damping, mass, stiffness: 170}});

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Camera shake that decays after each hit frame.
export const Shake: React.FC<{hits: number[]; amount?: number; children: React.ReactNode}> = ({
  hits,
  amount = 34,
  children,
}) => {
  const frame = useCurrentFrame();
  let x = 0;
  let y = 0;
  let r = 0;
  for (const h of hits) {
    const t = frame - h;
    if (t >= 0 && t < 14) {
      const k = Math.pow(1 - t / 14, 2) * amount;
      x += (random(`sx${h}-${t}`) - 0.5) * 2 * k;
      y += (random(`sy${h}-${t}`) - 0.5) * 2 * k;
      r += (random(`sr${h}-${t}`) - 0.5) * 0.08 * k;
    }
  }
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px) rotate(${r}deg)`}}>{children}</AbsoluteFill>;
};

// Quick zoom punch on beat frames — the "jump cut" feel.
export const Punch: React.FC<{at: number[]; amount?: number; children: React.ReactNode}> = ({at, amount = 0.08, children}) => {
  const frame = useCurrentFrame();
  let s = 1;
  for (const a of at) {
    const t = frame - a;
    if (t >= 0 && t < 10) s += amount * Math.pow(1 - t / 10, 2);
  }
  return <AbsoluteFill style={{transform: `scale(${s})`}}>{children}</AbsoluteFill>;
};

export const Flash: React.FC<{at: number; color?: string; dur?: number}> = ({at, color = '#fff', dur = 8}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at, at + 1, at + dur], [0, 0.85, 0], clamp);
  return <AbsoluteFill style={{background: color, opacity: o, pointerEvents: 'none'}} />;
};

// Dust / debris burst for impacts.
export const Burst: React.FC<{at: number; x: number; y: number; count?: number; color?: string; spread?: number}> = ({
  at,
  x,
  y,
  count = 18,
  color = C.violetLift,
  spread = 520,
}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > 30) return null;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {new Array(count).fill(0).map((_, i) => {
        const a = (i / count) * Math.PI * 2 + random(`a${at}${i}`) * 0.5;
        const v = spread * (0.5 + random(`v${at}${i}`) * 0.6);
        const p = 1 - Math.pow(1 - t / 30, 3);
        const px = x + Math.cos(a) * v * p;
        const py = y + Math.sin(a) * v * p * 0.45 + t * t * 0.25;
        const size = (10 + random(`s${at}${i}`) * 22) * (1 - t / 30);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: px - size / 2,
              top: py - size / 2,
              width: size,
              height: size,
              borderRadius: size,
              background: color,
              opacity: 1 - t / 30,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// Speed lines radiating from a point, for impacts and reveals.
export const SpeedLines: React.FC<{at: number; dur?: number; x?: number; y?: number}> = ({at, dur = 12, x = 540, y = 900}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > dur) return null;
  const o = 1 - t / dur;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: o}}>
      <svg width={1080} height={1920}>
        {new Array(28).fill(0).map((_, i) => {
          const a = (i / 28) * Math.PI * 2;
          const r1 = 420 + t * 30;
          const r2 = r1 + 260 + random(`sl${i}`) * 300;
          return (
            <line
              key={i}
              x1={x + Math.cos(a) * r1}
              y1={y + Math.sin(a) * r1}
              x2={x + Math.cos(a) * r2}
              y2={y + Math.sin(a) * r2}
              stroke="#fff"
              strokeWidth={6}
              strokeLinecap="round"
              opacity={0.6}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

export type Sfx = 'slam' | 'whoosh' | 'pop' | 'coin' | 'chime' | 'decline' | 'tick' | 'riser' | 'boing';

// Fire-and-forget sound effect at a frame.
export const SFX: React.FC<{at: number; s: Sfx; volume?: number}> = ({at, s, volume = 0.8}) => (
  <Sequence from={at} durationInFrames={60} layout="none">
    <Audio src={staticFile(`sfx/${s}.wav`)} volume={volume} />
  </Sequence>
);

// Slow-moving violet/orange light pools — mirrors the app's AmbientBackdrop.
export const Backdrop: React.FC<{tint?: 'violet' | 'warm' | 'night' | 'red'}> = ({tint = 'violet'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const t = frame / Math.max(durationInFrames, 1);
  const pools =
    tint === 'warm'
      ? [C.orange, C.gold, C.orchid]
      : tint === 'night'
        ? ['#2B2A6B', '#3A2470', '#151438']
        : tint === 'red'
          ? ['#7A1F2A', '#4A1530', '#2A0F1F']
          : [C.violet, C.accent, C.orange];
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      {pools.map((col, i) => {
        const x = 540 + Math.sin(t * 6 + i * 2.1) * 360;
        const y = 500 + i * 520 + Math.cos(t * 5 + i) * 160;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x - 520,
              top: y - 520,
              width: 1040,
              height: 1040,
              borderRadius: 1040,
              background: `radial-gradient(circle, ${col} 0%, transparent 65%)`,
              opacity: i === 2 && tint === 'violet' ? 0.28 : 0.45,
              filter: 'blur(40px)',
            }}
          />
        );
      })}
      <Grain />
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: 0.08, mixBlendMode: 'overlay'}}>
      <svg width="100%" height="100%">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 8} />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};
