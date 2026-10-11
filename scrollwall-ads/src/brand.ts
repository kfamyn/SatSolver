// Everything brand-specific lives here, so a rename or recolor is one edit.
export const APP_NAME = 'Scrollwall';
export const CTA_LINE = 'Free on the App Store';
export const MASCOT_NAME = 'Wally';

export const W = 1080;
export const H = 1920;
export const FPS = 30;

// Colours lifted from the redesign (HomeDesign.swift / CardAppearance.swift).
export const C = {
  bg: '#0B0A0F',
  surface: '#16141C',
  surface2: '#211E2A',
  hairline: 'rgba(255,255,255,0.08)',
  text: '#F7F5FA',
  sub: '#9C96A8',
  violet: '#8E6BD4',
  violetLift: '#A98BDF',
  violetText: '#A78AD9',
  accent: '#6B4EAA',
  orchid: '#C98BD0',
  orange: '#E8914A',
  gold: '#F0B55C',
  cream: '#F7D9A6',
  green: '#4CD98B',
  red: '#FF6B5E',
};

// Areas TikTok / Reels UI covers on a 1080x1920 frame. Keep text out of them.
export const SAFE = {top: 230, bottom: 500, left: 70, right: 160};

export const sec = (s: number) => Math.round(s * FPS);
