import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, SAFE} from '../brand';
import {UI} from '../fonts';
import {clamp, sp} from './fx';

type Variant = 'bold' | 'pill' | 'pillDark' | 'giant';

type Props = {
  text: string; // wrap words in *asterisks* to highlight them
  at?: number; // frame the first word lands
  out?: number; // frame it disappears (optional)
  y?: number; // top of the text block
  size?: number;
  variant?: Variant;
  wordDelay?: number;
  highlight?: string;
  align?: 'center' | 'left';
};

// Word-by-word kinetic captions in the style people actually read on
// TikTok/Reels: heavy weight, outlined, popped in on the beat. Kept inside the
// safe area so no platform UI covers them.
export const Caption: React.FC<Props> = ({
  text,
  at = 0,
  out,
  y = 360,
  size = 84,
  variant = 'bold',
  wordDelay = 3,
  highlight = C.gold,
  align = 'center',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < at) return null;
  const exit = out !== undefined ? interpolate(frame, [out - 5, out], [1, 0], clamp) : 1;
  if (exit <= 0) return null;

  const lines = text.split('\n');
  let wi = 0;
  const isPill = variant === 'pill' || variant === 'pillDark';
  const fontSize = variant === 'giant' ? size * 1.6 : size;

  return (
    <div
      style={{
        position: 'absolute',
        left: SAFE.left,
        width: 1080 - SAFE.left - SAFE.right,
        top: y,
        display: 'flex',
        flexDirection: 'column',
        alignItems: align === 'center' ? 'center' : 'flex-start',
        gap: isPill ? 0 : fontSize * 0.04,
        opacity: exit,
        transform: `scale(${0.9 + exit * 0.1})`,
        fontFamily: UI,
      }}
    >
      {lines.map((line, li) => (
        <div
          key={li}
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: align === 'center' ? 'center' : 'flex-start',
            ...(isPill
              ? {
                  background: variant === 'pill' ? '#fff' : 'rgba(10,9,14,0.92)',
                  borderRadius: fontSize * 0.28,
                  padding: `${fontSize * 0.1}px ${fontSize * 0.3}px`,
                  marginTop: li === 0 ? 0 : -fontSize * 0.08,
                }
              : {}),
          }}
        >
          {line.split(' ').map((raw, i) => {
            const hl = raw.startsWith('*') && raw.replace(/[.,!?:]+$/, '').endsWith('*');
            const word = raw.replace(/\*/g, '');
            const d = at + wi * wordDelay;
            wi++;
            const s = sp(frame, fps, d, 11, 0.5);
            if (frame < d) return <span key={i} style={{opacity: 0, fontSize, marginRight: fontSize * 0.26}}>{word}</span>;
            const color = isPill ? (variant === 'pill' ? (hl ? C.accent : '#0B0A0F') : hl ? highlight : '#fff') : hl ? highlight : '#fff';
            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  fontSize,
                  fontWeight: 900,
                  lineHeight: 1.08,
                  letterSpacing: -fontSize * 0.02,
                  color,
                  marginRight: fontSize * 0.26,
                  transform: `translateY(${(1 - s) * fontSize * 0.35}px) scale(${0.6 + s * 0.4})`,
                  ...(isPill
                    ? {}
                    : {
                        WebkitTextStroke: `${Math.max(6, fontSize * 0.11)}px #0B0A0F`,
                        paintOrder: 'stroke fill',
                        textShadow: `0 ${fontSize * 0.06}px 0 #0B0A0F, 0 0 ${fontSize * 0.4}px rgba(0,0,0,0.45)`,
                      }),
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};
