import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../brand';
import {UI, WORDMARK} from '../fonts';
import {clamp, sp} from './fx';

// ---------- phone close-up --------------------------------------------------

// A big phone held in Doug's hoodie-sleeved hands. Content is laid out at
// 390x844 (iPhone points) and scaled up, so UI copy matches the real thing.
export const PhoneCloseup: React.FC<{children: React.ReactNode; enter?: number; tilt?: number; shake?: number}> = ({
  children,
  enter = 0,
  tilt = 0,
  shake = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = sp(frame, fps, enter, 14, 0.7);
  const float = Math.sin(frame / 18) * 6;
  const sx = shake ? Math.sin(frame * 2.7) * shake : 0;
  const scale = 2.05;
  const w = 390 * scale;
  const h = 844 * scale;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div
        style={{
          position: 'absolute',
          top: 230 + (1 - s) * 900 + float,
          left: (1080 - w - 36) / 2 + sx,
          transform: `rotate(${tilt + (1 - s) * 8}deg)`,
          width: w + 36,
          height: h + 36,
          borderRadius: 64 * scale * 0.9,
          background: '#0E0D12',
          boxShadow: '0 40px 120px rgba(0,0,0,0.6), inset 0 0 0 4px #2A2833',
          padding: 18,
        }}
      >
        <div style={{width: w, height: h, borderRadius: 55 * scale * 0.9, overflow: 'hidden', position: 'relative', background: '#000'}}>
          <div style={{width: 390, height: 844, transform: `scale(${scale})`, transformOrigin: '0 0', position: 'relative'}}>
            {children}
            <div style={{position: 'absolute', top: 11, left: 390 / 2 - 62, width: 124, height: 36, borderRadius: 20, background: '#000'}} />
          </div>
        </div>
        {/* hoodie sleeves + hands gripping the bottom corners */}
        {[-1, 1].map((side) => (
          <div key={side} style={{position: 'absolute', bottom: -170, [side < 0 ? 'left' : 'right']: -120, width: 300, height: 420}}>
            <div style={{position: 'absolute', bottom: 0, left: side < 0 ? 0 : 60, width: 240, height: 260, borderRadius: 120, background: '#4B4563'}} />
            <div
              style={{
                position: 'absolute',
                top: 40,
                left: side < 0 ? 120 : 30,
                width: 150,
                height: 190,
                borderRadius: 90,
                background: 'radial-gradient(circle at 40% 30%, #F8D2B5, #E9AE8C)',
                boxShadow: 'inset -10px -14px 24px rgba(160,90,60,0.25)',
              }}
            />
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// A finger tap: ripple ring that expands where the user taps.
export const Tap: React.FC<{at: number; x: number; y: number}> = ({at, x, y}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < -6 || t > 14) return null;
  const approach = interpolate(t, [-6, 0], [0, 1], clamp);
  const r = t < 0 ? 26 : 26 + t * 4;
  const o = t < 0 ? approach * 0.8 : interpolate(t, [0, 14], [0.8, 0], clamp);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - r,
        top: y - r,
        width: r * 2,
        height: r * 2,
        borderRadius: r,
        background: t < 0 ? 'rgba(255,255,255,0.55)' : 'transparent',
        border: '3px solid rgba(255,255,255,0.9)',
        opacity: o,
      }}
    />
  );
};

// A dimmed, blurry feed behind sheets (stands in for the app underneath).
export const FeedUnderlay: React.FC<{dim?: number}> = ({dim = 0.55}) => {
  const frame = useCurrentFrame();
  const cols = ['#FF5C8A', '#7DE3F4', '#F0B55C', '#8E6BD4'];
  const c = cols[Math.floor(frame / 40) % cols.length];
  return (
    <AbsoluteFill style={{background: `linear-gradient(160deg, ${c}, #1A1424)`}}>
      <div style={{position: 'absolute', left: 120, top: 300, width: 160, height: 160, borderRadius: 80, background: 'rgba(255,255,255,0.3)', filter: 'blur(12px)'}} />
      <AbsoluteFill style={{background: `rgba(0,0,0,${dim})`, backdropFilter: 'blur(10px)'}} />
    </AbsoluteFill>
  );
};

// ---------- Apple Screen Time (the thing everyone ignores) -------------------

export const ScreenTimeLimit: React.FC<{sheetAt?: number; app?: string}> = ({sheetAt, app = 'TikTok'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sheet = sheetAt !== undefined ? sp(frame, fps, sheetAt, 16, 0.6) : 0;
  return (
    <AbsoluteFill style={{background: '#0D0D10', fontFamily: UI, color: '#fff'}}>
      <div style={{position: 'absolute', top: 250, width: '100%', textAlign: 'center'}}>
        <svg width={64} height={64} viewBox="0 0 64 64" style={{margin: '0 auto', display: 'block'}}>
          <circle cx={32} cy={32} r={32} fill="#5E5CE6" />
          <path d="M22 16 H42 M22 48 H42 M24 16 Q24 30 32 32 Q40 30 40 16 M24 48 Q24 34 32 32 Q40 34 40 48" stroke="#fff" strokeWidth={3.5} fill="none" strokeLinecap="round" />
        </svg>
        <div style={{fontSize: 28, fontWeight: 800, marginTop: 18}}>Time Limit</div>
        <div style={{fontSize: 16, color: '#A1A1AA', marginTop: 8, padding: '0 50px', lineHeight: 1.35}}>
          You&apos;ve reached your limit on {app}.
        </div>
      </div>
      <div style={{position: 'absolute', bottom: 120, left: 24, right: 24, textAlign: 'center'}}>
        <div style={{background: '#fff', color: '#000', borderRadius: 14, padding: '15px 0', fontSize: 17, fontWeight: 600}}>OK</div>
        <div style={{color: '#0A84FF', fontSize: 17, marginTop: 22, fontWeight: 600}}>Ignore Limit</div>
      </div>
      {sheetAt !== undefined && frame >= sheetAt && (
        <>
          <AbsoluteFill style={{background: `rgba(0,0,0,${0.45 * sheet})`}} />
          <div style={{position: 'absolute', left: 10, right: 10, bottom: 30 - (1 - sheet) * 400, fontSize: 19}}>
            <div style={{background: 'rgba(44,44,48,0.97)', borderRadius: 14, overflow: 'hidden', textAlign: 'center', color: '#0A84FF'}}>
              {['One More Minute', 'Remind Me in 15 Minutes', 'Ignore Limit For Today'].map((t, i) => (
                <div key={t} style={{padding: '17px 0', borderTop: i ? '1px solid rgba(255,255,255,0.1)' : 'none'}}>
                  {t}
                </div>
              ))}
            </div>
            <div style={{background: 'rgba(44,44,48,0.97)', borderRadius: 14, textAlign: 'center', color: '#0A84FF', padding: '17px 0', marginTop: 8, fontWeight: 700}}>
              Cancel
            </div>
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};
// Tap targets in phone (390x844) coordinates.
export const ST_IGNORE = {x: 195, y: 714};
export const ST_IGNORE_TODAY = {x: 195, y: 693};

// ---------- Scrollwall shield --------------------------------------------------

export const CoinGlyph: React.FC<{size?: number}> = ({size = 16}) => (
  <span
    style={{
      display: 'inline-block',
      width: size,
      height: size,
      borderRadius: size,
      verticalAlign: '-0.12em',
      background: 'radial-gradient(circle at 35% 30%, #FFE3A3, #E8914A 75%)',
      boxShadow: `inset 0 0 0 ${size * 0.12}px rgba(255,255,255,0.35)`,
      margin: '0 2px',
    }}
  />
);

export const MiniCard: React.FC<{w?: number; declined?: number; approved?: number}> = ({w = 120, declined = 0, approved = 0}) => (
  <div
    style={{
      width: w,
      height: w / 1.586,
      borderRadius: w * 0.08,
      position: 'relative',
      overflow: 'hidden',
      background: '#131118',
      boxShadow: '0 10px 30px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.12)',
      fontFamily: UI,
    }}
  >
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background:
          'radial-gradient(circle at 2% 86%, #8E6BD4cc, transparent 60%), radial-gradient(circle at 56% 20%, #E8914Acc, transparent 55%), radial-gradient(circle at 96% 46%, #F0B55Ccc, transparent 55%), radial-gradient(circle at 30% 60%, #C98BD0aa, transparent 50%)',
        opacity: 0.85,
      }}
    />
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.55) 1px, transparent 1.4px)',
        backgroundSize: `${w / 26}px ${w / 26}px`,
        maskImage: 'radial-gradient(circle at 60% 55%, black 20%, transparent 62%)',
        WebkitMaskImage: 'radial-gradient(circle at 60% 55%, black 20%, transparent 62%)',
      }}
    />
    <div style={{position: 'absolute', top: w * 0.07, left: w * 0.08, color: '#fff', fontWeight: 700, fontSize: w * 0.1}}>FocusCard</div>
    <div style={{position: 'absolute', bottom: w * 0.06, left: w * 0.08, color: 'rgba(255,255,255,0.7)', fontWeight: 600, fontSize: w * 0.07}}>Doug</div>
    {declined > 0 && <div style={{position: 'absolute', inset: 0, background: C.red, opacity: declined * 0.55}} />}
    {approved > 0 && <div style={{position: 'absolute', inset: 0, background: C.green, opacity: approved * 0.35}} />}
  </div>
);

export const Shield: React.FC<{app?: string; coins?: number}> = ({app = 'TikTok', coins = 10}) => (
  <AbsoluteFill style={{background: 'linear-gradient(180deg, #17121F 0%, #0B0A0F 70%)', fontFamily: UI, color: '#fff'}}>
    <div style={{position: 'absolute', top: 230, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <MiniCard w={110} />
      <div style={{fontSize: 22, fontWeight: 800, marginTop: 26}}>You hit a scrollwall.</div>
      <div style={{fontSize: 17, color: '#A39DB0', marginTop: 8, textAlign: 'center', lineHeight: 1.4, padding: '0 40px'}}>
        Spend {coins} FocusCoins <CoinGlyph /> to unlock {app} for 1 minute.
      </div>
    </div>
    <div style={{position: 'absolute', bottom: 110, left: 60, right: 60, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12}}>
      <div style={{background: '#fff', color: '#000', borderRadius: 30, padding: '14px 0', width: 190, textAlign: 'center', fontSize: 16, fontWeight: 700}}>
        Unlock 1 min
      </div>
      <div style={{background: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: 30, padding: '12px 0', width: 190, textAlign: 'center', fontSize: 15, fontWeight: 600}}>
        Other durations
      </div>
    </div>
  </AbsoluteFill>
);
export const SHIELD_UNLOCK = {x: 195, y: 709};

// ---------- FocusCard payment ----------------------------------------------------

export const PaySheet: React.FC<{
  at?: number;
  result?: 'declined' | 'approved';
  resultAt?: number;
  coins?: number;
  balance?: number;
  minutes?: number;
}> = ({at = 0, result, resultAt = 30, coins = 10, balance = 0, minutes = 1}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = sp(frame, fps, at, 15, 0.6);
  const r = result ? interpolate(frame, [resultAt, resultAt + 6], [0, 1], clamp) : 0;
  const shake = result === 'declined' && frame >= resultAt && frame < resultAt + 14 ? Math.sin((frame - resultAt) * 2.4) * 14 * (1 - (frame - resultAt) / 14) : 0;
  const tilt = result === 'approved' ? interpolate(frame, [resultAt - 18, resultAt], [0, 1], clamp) : 0;
  return (
    <AbsoluteFill style={{fontFamily: UI, color: '#fff'}}>
      <Shield />
      <AbsoluteFill style={{background: `rgba(0,0,0,${0.55 * s})`}} />
      <div
        style={{
          position: 'absolute',
          left: 8,
          right: 8,
          bottom: 8 - (1 - s) * 520,
          height: 470,
          borderRadius: 38,
          background: '#16141C',
          boxShadow: '0 -10px 40px rgba(0,0,0,0.5)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 34,
        }}
      >
        <div style={{width: 40, height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.2)', position: 'absolute', top: 10}} />
        <div style={{fontSize: 22, fontWeight: 800}}>Unlock {minutes} min</div>
        <div style={{marginTop: 26, transform: `translateX(${shake}px) perspective(600px) rotateX(${tilt * 28}deg)`}}>
          <MiniCard w={250} declined={result === 'declined' ? r : 0} approved={result === 'approved' ? r : 0} />
        </div>
        <div style={{fontSize: 15, color: '#9C96A8', marginTop: 22}}>
          Balance: <b style={{color: result === 'declined' && r > 0 ? C.red : '#fff'}}>{balance}</b> <CoinGlyph size={14} />
        </div>
        <div
          style={{
            position: 'absolute',
            bottom: 34,
            left: 26,
            right: 26,
            borderRadius: 30,
            padding: '15px 0',
            textAlign: 'center',
            fontSize: 17,
            fontWeight: 800,
            background: result === 'declined' && r > 0 ? C.red : result === 'approved' && r > 0 ? C.green : '#fff',
            color: r > 0 ? '#fff' : '#000',
          }}
        >
          {result === 'declined' && r > 0
            ? 'Not enough FocusCoins'
            : result === 'approved' && r > 0
              ? `✓ ${minutes} min unlocked`
              : <>Spend {coins} <CoinGlyph size={15} /> with FocusCard</>}
        </div>
      </div>
    </AbsoluteFill>
  );
};
export const PAY_BUTTON = {x: 195, y: 785};

// ---------- real app footage in the phone ----------------------------------------

// Plays a slice of a recording (seconds) inside the phone close-up.
export const AppClip: React.FC<{src: string; from: number; to: number; rate?: number}> = ({src, from, to, rate = 1}) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <OffthreadVideo
        src={staticFile(src)}
        trimBefore={Math.round(from * fps)}
        trimAfter={Math.round(to * fps)}
        playbackRate={rate}
        muted
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />
    </AbsoluteFill>
  );
};

// ---------- comic bits -----------------------------------------------------------------

export const Bubble: React.FC<{text: string; at: number; out?: number; x: number; y: number; tail?: 'left' | 'right' | 'down'; size?: number}> = ({
  text,
  at,
  out,
  x,
  y,
  tail = 'down',
  size = 64,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < at || (out !== undefined && frame > out)) return null;
  const s = sp(frame, fps, at, 10, 0.5);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, -100%) scale(${s})`,
        transformOrigin: tail === 'left' ? '10% 100%' : tail === 'right' ? '90% 100%' : '50% 100%',
        fontFamily: UI,
      }}
    >
      <div
        style={{
          background: '#fff',
          color: '#0B0A0F',
          fontWeight: 900,
          fontSize: size,
          letterSpacing: -size * 0.02,
          padding: `${size * 0.28}px ${size * 0.45}px`,
          borderRadius: size * 0.6,
          whiteSpace: 'pre',
          lineHeight: 1.05,
          boxShadow: '0 12px 0 rgba(0,0,0,0.25)',
          textAlign: 'center',
        }}
      >
        {text}
      </div>
      <div
        style={{
          position: 'absolute',
          bottom: -size * 0.32,
          left: tail === 'left' ? '18%' : tail === 'right' ? '74%' : '46%',
          width: 0,
          height: 0,
          borderLeft: `${size * 0.28}px solid transparent`,
          borderRight: `${size * 0.28}px solid transparent`,
          borderTop: `${size * 0.4}px solid #fff`,
          transform: tail === 'left' ? 'skewX(25deg)' : tail === 'right' ? 'skewX(-25deg)' : 'none',
        }}
      />
    </div>
  );
};

// Little "creator watermark" — the only branding in the videos.
export const Watermark: React.FC<{opacity?: number}> = ({opacity = 0.75}) => (
  <div style={{position: 'absolute', top: 252, right: 170, fontFamily: WORDMARK, fontSize: 40, color: '#fff', opacity, textShadow: '0 2px 10px rgba(0,0,0,0.5)'}}>
    Scrollwall
  </div>
);

// Floating chip for clocks / timers ("11:58 PM", "47 min").
export const Chip: React.FC<{text: string; x?: number; y?: number; at?: number; color?: string; size?: number}> = ({
  text,
  x = 540,
  y = 1180,
  at = 0,
  color = '#fff',
  size = 56,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < at) return null;
  const s = sp(frame, fps, at, 12, 0.5);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, 0) scale(${s})`,
        background: 'rgba(11,10,15,0.78)',
        border: '2px solid rgba(255,255,255,0.12)',
        color,
        fontFamily: UI,
        fontWeight: 900,
        fontSize: size,
        padding: `${size * 0.18}px ${size * 0.45}px`,
        borderRadius: size,
        fontVariantNumeric: 'tabular-nums',
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </div>
  );
};

export const Zzz: React.FC<{x: number; y: number}> = ({x, y}) => {
  const frame = useCurrentFrame();
  return (
    <>
      {[0, 1, 2].map((i) => {
        const t = ((frame + i * 20) % 60) / 60;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x + t * 90 + i * 10,
              top: y - t * 220,
              fontFamily: UI,
              fontWeight: 900,
              fontSize: 50 + i * 16,
              color: '#fff',
              opacity: Math.sin(t * Math.PI),
            }}
          >
            z
          </div>
        );
      })}
    </>
  );
};
