import React from 'react';
import * as THREE from 'three';

export const Limb: React.FC<{from: THREE.Vector3; to: THREE.Vector3; r?: number; mat: THREE.Material; handMat: THREE.Material; hand?: number}> = ({
  from,
  to,
  r = 0.075,
  mat,
  handMat,
  hand = 0.11,
}) => {
  const dir = new THREE.Vector3().subVectors(to, from);
  const len = dir.length();
  const mid = new THREE.Vector3().addVectors(from, to).multiplyScalar(0.5);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  return (
    <group>
      <mesh position={mid} quaternion={q} material={mat} castShadow>
        <capsuleGeometry args={[r, Math.max(0.01, len), 6, 16]} />
      </mesh>
      <mesh position={to} material={handMat} castShadow>
        <sphereGeometry args={[hand, 24, 24]} />
      </mesh>
    </group>
  );
};

export const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);


export type ScreenMode = 'feed' | 'shield' | 'limit' | 'off' | 'declined';

const FEED_COLORS = ['#FF5C8A', '#7DE3F4', '#F0B55C', '#8E6BD4', '#4CD98B', '#FF8A4C', '#5C7CFF'];

// Draws the phone screen for a frame. Low detail on purpose: in wide shots
// the screen only needs to read as "glowing feed" / "wall" / "warning".
const drawScreen = (ctx: CanvasRenderingContext2D, mode: ScreenMode, frame: number) => {
  const w = 180;
  const h = 360;
  ctx.clearRect(0, 0, w, h);
  if (mode === 'off') {
    ctx.fillStyle = '#050407';
    ctx.fillRect(0, 0, w, h);
    return;
  }
  if (mode === 'feed') {
    // A video feed that keeps snapping to the next clip.
    const clip = Math.floor(frame / 9);
    const t = (frame % 9) / 9;
    const ease = t < 0.35 ? 1 - Math.pow(1 - t / 0.35, 3) : 1;
    for (let k = 0; k < 2; k++) {
      const idx = clip + k;
      const y = (k - ease) * h;
      ctx.fillStyle = FEED_COLORS[idx % FEED_COLORS.length];
      ctx.fillRect(0, y, w, h);
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.beginPath();
      ctx.arc(w / 2, y + h * 0.42, 38 + (idx % 3) * 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fillRect(14, y + h - 70, 110, 12);
      ctx.fillRect(14, y + h - 50, 80, 10);
    }
    return;
  }
  if (mode === 'shield' || mode === 'declined') {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, mode === 'declined' ? '#4A1020' : '#2A1B52');
    g.addColorStop(1, '#0B0A0F');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = mode === 'declined' ? '#FF6B5E' : '#F3EEFD';
    const r = 22;
    ctx.beginPath();
    ctx.roundRect(w / 2 - r, h * 0.28, r * 2, 110, r);
    ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.beginPath();
    ctx.roundRect(30, h - 70, w - 60, 26, 13);
    ctx.fill();
    return;
  }
  if (mode === 'limit') {
    ctx.fillStyle = '#1C1B22';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = '#F2F2F7';
    ctx.beginPath();
    ctx.roundRect(14, h * 0.3, w - 28, 150, 16);
    ctx.fill();
    ctx.fillStyle = '#5E5CE6';
    ctx.beginPath();
    ctx.arc(w / 2, h * 0.3 + 34, 16, 0, Math.PI * 2);
    ctx.fill();
  }
};

export const Phone3D: React.FC<{
  frame: number;
  mode?: ScreenMode;
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
  glow?: number;
}> = ({frame, mode = 'feed', position = [0, 0, 0], rotation = [0, 0, 0], scale = 1, glow = 1}) => {
  const {canvas, tex} = React.useMemo(() => {
    const c = document.createElement('canvas');
    c.width = 180;
    c.height = 360;
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return {canvas: c, tex: t};
  }, []);
  const ctx = canvas.getContext('2d')!;
  drawScreen(ctx, mode, frame);
  tex.needsUpdate = true;
  const glowColor = mode === 'feed' ? '#A9DDFF' : mode === 'declined' ? '#FF6B5E' : mode === 'limit' ? '#DADAF5' : '#A98BDF';
  return (
    <group position={position} rotation={rotation} scale={scale}>
      <mesh castShadow>
        <boxGeometry args={[0.36, 0.72, 0.035]} />
        <meshPhysicalMaterial color="#111014" roughness={0.3} clearcoat={1} />
      </mesh>
      <mesh position={[0, 0, 0.019]}>
        <planeGeometry args={[0.33, 0.68]} />
        <meshBasicMaterial map={tex} toneMapped={false} />
      </mesh>
      {mode !== 'off' && glow > 0 && <pointLight position={[0, 0.25, 0.6]} intensity={1.1 * glow} distance={1.6} decay={2} color={glowColor} />}
    </group>
  );
};
