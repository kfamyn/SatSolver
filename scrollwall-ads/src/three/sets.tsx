import React, {useMemo} from 'react';
import * as THREE from 'three';
import {random} from 'remotion';

// Simple, toy-like sets built from primitives. Each set puts its "hero spot"
// (where Doug sits) at the origin, facing +z toward the camera.

const useCanvasTex = (w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void, deps: unknown[]) => {
  const {canvas, tex} = useMemo(() => {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return {canvas: c, tex: t};
  }, [w, h]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useMemo(() => {
    draw(canvas.getContext('2d')!);
    tex.needsUpdate = true;
  }, deps);
  return tex;
};

// Bedside alarm clock with glowing digits.
export const Clock3D: React.FC<{text: string; position: [number, number, number]; rotationY?: number}> = ({text, position, rotationY = 0}) => {
  const tex = useCanvasTex(
    256,
    112,
    (ctx) => {
      ctx.fillStyle = '#0A0508';
      ctx.fillRect(0, 0, 256, 112);
      ctx.fillStyle = '#FF4D4D';
      ctx.font = 'bold 76px Inter, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 128, 60);
    },
    [text],
  );
  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      <mesh castShadow>
        <boxGeometry args={[0.5, 0.24, 0.18]} />
        <meshPhysicalMaterial color="#2A2733" roughness={0.4} clearcoat={0.6} />
      </mesh>
      <mesh position={[0, 0, 0.091]}>
        <planeGeometry args={[0.44, 0.19]} />
        <meshBasicMaterial map={tex} toneMapped={false} />
      </mesh>
      <pointLight position={[0, 0, 0.3]} intensity={0.6} distance={1.2} color="#FF4D4D" />
    </group>
  );
};

const Floor: React.FC<{color: string; size?: number}> = ({color, size = 30}) => (
  <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
    <planeGeometry args={[size, size]} />
    <meshStandardMaterial color={color} roughness={0.9} />
  </mesh>
);

const Wall: React.FC<{color: string; z?: number; map?: THREE.Texture}> = ({color, z = -2.2, map}) => (
  <mesh position={[0, 5, z]} receiveShadow>
    <planeGeometry args={[30, 10]} />
    <meshStandardMaterial color={color} roughness={0.95} map={map ?? null} />
  </mesh>
);

const Window: React.FC<{position: [number, number, number]; sky: string; moon?: boolean; sun?: boolean; moonY?: number}> = ({
  position,
  sky,
  moon,
  sun,
  moonY = 0.25,
}) => (
  <group position={position}>
    <mesh>
      <planeGeometry args={[1.6, 1.9]} />
      <meshBasicMaterial color={sky} toneMapped={false} />
    </mesh>
    {moon && (
      <mesh position={[0.35, moonY, 0.01]}>
        <circleGeometry args={[0.22, 32]} />
        <meshBasicMaterial color="#FFF6D8" toneMapped={false} />
      </mesh>
    )}
    {sun && (
      <mesh position={[-0.3, moonY, 0.01]}>
        <circleGeometry args={[0.28, 32]} />
        <meshBasicMaterial color="#FFE3A3" toneMapped={false} />
      </mesh>
    )}
    {/* stars */}
    {moon &&
      new Array(12).fill(0).map((_, i) => (
        <mesh key={i} position={[(random(`wx${i}`) - 0.5) * 1.4, (random(`wy${i}`) - 0.5) * 1.7, 0.01]}>
          <circleGeometry args={[0.012 + random(`ws${i}`) * 0.012, 6]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      ))}
    {/* frame */}
    {[
      [0, 0.98, 1.76, 0.08],
      [0, -0.98, 1.76, 0.08],
      [0.84, 0, 0.08, 2.04],
      [-0.84, 0, 0.08, 2.04],
      [0, 0, 0.05, 1.9],
      [0, 0, 1.6, 0.05],
    ].map(([x, y, w, h], i) => (
      <mesh key={i} position={[x, y, 0.03]}>
        <boxGeometry args={[w, h, 0.06]} />
        <meshStandardMaterial color="#E9E4F2" roughness={0.6} />
      </mesh>
    ))}
  </group>
);

// ---------- bedroom --------------------------------------------------------------

export const Bedroom: React.FC<{clock: string; lamp?: number; night?: number; moonY?: number}> = ({clock, lamp = 0, night = 1, moonY}) => (
  <group>
    <Floor color="#231F2E" />
    <Wall color="#2C2745" />
    <Window position={[-1.9, 2.6, -2.18]} sky={night > 0.5 ? '#141A3D' : '#8EC9FF'} moon={night > 0.5} sun={night <= 0.5} moonY={moonY} />
    {/* bed: frame, mattress, headboard, pillow, blanket */}
    <group position={[0, 0, -0.55]}>
      <mesh position={[0, 0.22, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.3, 0.44, 3.2]} />
        <meshStandardMaterial color="#5A4A6E" roughness={0.8} />
      </mesh>
      <mesh position={[0, 0.54, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.2, 0.24, 3.1]} />
        <meshStandardMaterial color="#EDE8F6" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.95, -1.62]} castShadow receiveShadow>
        <boxGeometry args={[2.4, 1.5, 0.16]} />
        <meshStandardMaterial color="#5A4A6E" roughness={0.8} />
      </mesh>
      <mesh position={[0, 0.85, -1.25]} scale={[0.85, 0.24, 0.32]} castShadow>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial color="#F7F5FA" roughness={0.95} />
      </mesh>
    </group>
    {/* nightstand + lamp + clock */}
    <group position={[1.75, 0, -1.2]}>
      <mesh position={[0, 0.4, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.8, 0.8, 0.7]} />
        <meshStandardMaterial color="#6B5A80" roughness={0.7} />
      </mesh>
      <Clock3D text={clock} position={[-0.1, 0.92, 0.12]} rotationY={-0.35} />
      <mesh position={[0.22, 1.0, -0.1]} castShadow>
        <cylinderGeometry args={[0.04, 0.06, 0.4, 16]} />
        <meshStandardMaterial color="#D9D4E3" />
      </mesh>
      <mesh position={[0.22, 1.28, -0.1]}>
        <coneGeometry args={[0.2, 0.26, 24, 1, true]} />
        <meshStandardMaterial color="#F7E7C9" emissive="#FFCF8A" emissiveIntensity={lamp * 1.5} side={THREE.DoubleSide} />
      </mesh>
      {lamp > 0 && <pointLight position={[0.22, 1.2, 0.1]} intensity={6 * lamp} distance={4} color="#FFCF8A" />}
    </group>
    {/* moonlight */}
    <directionalLight position={[-3, 4, 1]} intensity={0.5 * night} color="#9FB4FF" />
  </group>
);

export const Blanket: React.FC<{position?: [number, number, number]; up?: number}> = ({position = [0, 0.75, 0.25], up = 0}) => (
  <mesh position={[position[0], position[1] + up, position[2]]} scale={[1.12, 0.22 + up * 0.5, 1.15]} castShadow receiveShadow>
    <sphereGeometry args={[1, 40, 24]} />
    <meshPhysicalMaterial color="#7B5FC0" roughness={0.85} sheen={1} sheenColor={new THREE.Color('#C9B8FF')} />
  </mesh>
);

// ---------- bathroom -----------------------------------------------------------------

export const Bathroom: React.FC = () => {
  const tiles = useCanvasTex(
    512,
    512,
    (ctx) => {
      ctx.fillStyle = '#CFE6EA';
      ctx.fillRect(0, 0, 512, 512);
      ctx.strokeStyle = '#A9C9CF';
      ctx.lineWidth = 6;
      for (let i = 0; i <= 512; i += 64) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, 512);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(512, i);
        ctx.stroke();
      }
    },
    [],
  );
  useMemo(() => {
    tiles.wrapS = tiles.wrapT = THREE.RepeatWrapping;
    tiles.repeat.set(10, 3.5);
  }, [tiles]);
  return (
    <group>
      <Floor color="#B8B2C4" />
      <Wall color="#ffffff" map={tiles} z={-1.4} />
      {/* toilet: tank, bowl, seat */}
      <group position={[0, 0, -0.55]}>
        <mesh position={[0, 0.95, -0.55]} castShadow>
          <boxGeometry args={[0.9, 0.7, 0.32]} />
          <meshPhysicalMaterial color="#FBFBFD" roughness={0.15} clearcoat={1} />
        </mesh>
        <mesh position={[0, 0.25, 0]} castShadow>
          <cylinderGeometry args={[0.3, 0.24, 0.5, 32]} />
          <meshPhysicalMaterial color="#FBFBFD" roughness={0.15} clearcoat={1} />
        </mesh>
        <mesh position={[0, 0.5, 0.02]} scale={[1, 1, 1.25]} rotation={[Math.PI / 2, 0, 0]} castShadow>
          <torusGeometry args={[0.3, 0.07, 16, 40]} />
          <meshPhysicalMaterial color="#F2F0F7" roughness={0.2} clearcoat={1} />
        </mesh>
      </group>
      {/* toilet roll on the wall */}
      <mesh position={[1.0, 0.9, -1.2]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.13, 0.13, 0.2, 24]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
      {/* door frame on the right — Wally peeks in from here */}
      <mesh position={[2.1, 1.5, -1.0]} castShadow>
        <boxGeometry args={[0.15, 3, 0.15]} />
        <meshStandardMaterial color="#8E6BD4" />
      </mesh>
    </group>
  );
};

// ---------- study desk ------------------------------------------------------------------

export const DeskSet: React.FC<{daylight?: number; phoneDown?: boolean}> = ({daylight = 1, phoneDown = true}) => {
  const sky = new THREE.Color('#2B2A6B').lerp(new THREE.Color('#9AD4FF'), daylight);
  return (
    <group>
      <Floor color="#2A2536" />
      <Wall color="#3A3358" z={-1.8} />
      <Window position={[1.6, 2.4, -1.78]} sky={`#${sky.getHexString()}`} sun={daylight > 0.5} moon={daylight <= 0.5} moonY={0.1} />
      {/* chair */}
      <mesh position={[0, 0.45, -0.1]} castShadow>
        <boxGeometry args={[0.9, 0.1, 0.8]} />
        <meshStandardMaterial color="#6B4EAA" />
      </mesh>
      <mesh position={[0, 0.2, -0.1]}>
        <cylinderGeometry args={[0.05, 0.05, 0.4, 12]} />
        <meshStandardMaterial color="#222" />
      </mesh>
      {/* desk */}
      <group position={[0, 0, 0.75]}>
        <mesh position={[0, 0.98, 0]} castShadow receiveShadow>
          <boxGeometry args={[2.6, 0.08, 1.0]} />
          <meshStandardMaterial color="#C9A27E" roughness={0.6} />
        </mesh>
        {[-1.2, 1.2].map((x) => (
          <mesh key={x} position={[x, 0.48, 0]} castShadow>
            <boxGeometry args={[0.08, 0.96, 0.9]} />
            <meshStandardMaterial color="#A88463" />
          </mesh>
        ))}
        {/* lamp */}
        <group position={[-1.0, 1.02, -0.25]}>
          <mesh position={[0, 0.02, 0]}>
            <cylinderGeometry args={[0.14, 0.16, 0.04, 24]} />
            <meshStandardMaterial color="#2A2733" />
          </mesh>
          <mesh position={[0.05, 0.32, 0]} rotation={[0, 0, -0.3]}>
            <cylinderGeometry args={[0.02, 0.02, 0.6, 8]} />
            <meshStandardMaterial color="#2A2733" />
          </mesh>
          <mesh position={[0.2, 0.6, 0.05]} rotation={[0.4, 0, -0.9]}>
            <coneGeometry args={[0.14, 0.22, 24, 1, true]} />
            <meshStandardMaterial color="#F0B55C" emissive="#FFCF8A" emissiveIntensity={1.2} side={THREE.DoubleSide} />
          </mesh>
          <pointLight position={[0.3, 0.45, 0.25]} intensity={5} distance={3} color="#FFD9A0" />
        </group>
        {/* phone lying face down */}
        {phoneDown && (
          <mesh position={[0.85, 1.04, 0.05]} rotation={[0, 0.3, 0]} castShadow>
            <boxGeometry args={[0.24, 0.025, 0.48]} />
            <meshPhysicalMaterial color="#111014" roughness={0.3} clearcoat={1} />
          </mesh>
        )}
        {/* stack of books */}
        {[0, 1, 2].map((i) => (
          <mesh key={i} position={[-0.6, 1.06 + i * 0.08, -0.3]} rotation={[0, i * 0.2, 0]} castShadow>
            <boxGeometry args={[0.5, 0.07, 0.36]} />
            <meshStandardMaterial color={['#8E6BD4', '#E8914A', '#4CD98B'][i]} />
          </mesh>
        ))}
      </group>
      <directionalLight position={[2, 3, -1]} intensity={1.2 * daylight} color="#CFE7FF" />
    </group>
  );
};

// ---------- coins ------------------------------------------------------------------------

// FocusCoins tumbling down onto a surface.
export const CoinRain: React.FC<{frame: number; count?: number; floorY?: number; area?: [number, number]; z?: number}> = ({
  frame,
  count = 14,
  floorY = 1.06,
  area = [2.2, 0.6],
  z = 0.75,
}) => (
  <group>
    {new Array(count).fill(0).map((_, i) => {
      const delay = i * 3;
      const t = Math.max(0, frame - delay) / 30;
      const x = (random(`cx${i}`) - 0.5) * area[0];
      const zz = z + (random(`cz${i}`) - 0.5) * area[1];
      const y = Math.max(floorY + 0.02 + i * 0.004, 3.4 - 9.8 * t * t * 0.5);
      const landed = y <= floorY + 0.03 + i * 0.004;
      const spin = landed ? 0 : t * 12 + i;
      if (frame < delay) return null;
      return (
        <mesh key={i} position={[x, y, zz]} rotation={[landed ? 0 : spin, spin * 0.5, landed ? 0 : spin * 0.3]} castShadow>
          <cylinderGeometry args={[0.1, 0.1, 0.025, 32]} />
          <meshPhysicalMaterial color="#F0B55C" metalness={0.85} roughness={0.25} clearcoat={1} emissive="#7A4A10" emissiveIntensity={0.2} />
        </mesh>
      );
    })}
  </group>
);
