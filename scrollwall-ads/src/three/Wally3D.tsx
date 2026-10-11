import React, {useMemo} from 'react';
import * as THREE from 'three';
import {useCurrentFrame} from 'remotion';
import {Limb, V} from './parts';

// Wally in 3D: a glossy capsule — the pill from the app icon — with a
// vinyl-toy face. All geometry is built from primitives so nothing has to load.

export type W3Expr = 'neutral' | 'happy' | 'angry' | 'shock' | 'smug' | 'sad' | 'sleepy';
export type W3Mouth = 'smile' | 'grin' | 'open' | 'o' | 'flat' | 'frown' | 'smirk';
export type W3Arms = 'down' | 'stop' | 'cross' | 'wave' | 'up' | 'point' | 'shrug' | 'hold';

export type Wally3DProps = {
  position?: [number, number, number];
  rotationY?: number;
  tilt?: number; // lean (rad) around z
  scale?: number;
  squash?: number;
  expr?: W3Expr;
  mouth?: W3Mouth;
  arms?: W3Arms;
  talk?: boolean;
  look?: [number, number];
  nightcap?: boolean;
  shades?: boolean;
  height?: number; // stretch factor of the body (1 = normal); used for gags
};

const BODY_R = 0.5;
const BODY_L = 1.3;
const FACE_Z = BODY_R * 0.96;

const useMats = () =>
  useMemo(
    () => ({
      body: new THREE.MeshPhysicalMaterial({
        color: '#F3EEFD',
        roughness: 0.22,
        clearcoat: 1,
        clearcoatRoughness: 0.12,
        sheen: 0.6,
        sheenColor: new THREE.Color('#B9A5E8'),
        emissive: new THREE.Color('#5B3FA0'),
        emissiveIntensity: 0.08,
      }),
      limb: new THREE.MeshPhysicalMaterial({color: '#E4DAF9', roughness: 0.3, clearcoat: 0.8}),
      ink: new THREE.MeshPhysicalMaterial({color: '#141219', roughness: 0.15, clearcoat: 1}),
      white: new THREE.MeshBasicMaterial({color: '#ffffff'}),
      cheek: new THREE.MeshStandardMaterial({color: '#F59ABF', transparent: true, opacity: 0.55, roughness: 0.8}),
      tongue: new THREE.MeshStandardMaterial({color: '#F07FA8', roughness: 0.5}),
      cap: new THREE.MeshStandardMaterial({color: '#6B4EAA', roughness: 0.7}),
      capTrim: new THREE.MeshStandardMaterial({color: '#F3EEFC', roughness: 0.9}),
    }),
    [],
  );

// A point on the capsule's front surface for a given (x, y) on the face.
const onFace = (x: number, y: number, lift = 0): [number, number, number] => {
  const z = Math.sqrt(Math.max(0, BODY_R * BODY_R - x * x)) * 0.98 + lift;
  return [x, y, z];
};

export const Wally3D: React.FC<Wally3DProps> = ({
  position = [0, 0, 0],
  rotationY = 0,
  tilt = 0,
  scale = 1,
  squash = 1,
  expr = 'neutral',
  mouth = 'smile',
  arms = 'down',
  talk = false,
  look = [0, 0],
  nightcap = false,
  shades = false,
  height = 1,
}) => {
  const f = useCurrentFrame();
  const m = useMats();
  const cyc = (f + 37) % 100;
  const blink = cyc < 5 ? Math.sin((cyc / 5) * Math.PI) : 0;
  const mo: W3Mouth = talk ? (Math.floor(f / 4) % 2 === 0 ? 'open' : 'smile') : mouth;
  const idle = Math.sin(f / 14) * 0.015;
  const bodyH = BODY_L * height;
  const centerY = BODY_R + bodyH / 2 + 0.12; // feet at y≈0
  const faceY = centerY + bodyH * 0.18;
  const sh = [BODY_R * 0.92, centerY - bodyH * 0.12] as const; // shoulder x, y
  const wave = Math.sin(f / 3.2) * 0.18;

  const armTargets: Record<W3Arms, [THREE.Vector3, THREE.Vector3]> = {
    down: [V(-0.66, sh[1] - 0.45, 0.05), V(0.66, sh[1] - 0.45, 0.05)],
    stop: [V(-0.66, sh[1] - 0.45, 0.05), V(0.62, sh[1] + 0.45, 0.45)],
    cross: [V(0.28, sh[1] - 0.18, 0.62), V(-0.28, sh[1] - 0.28, 0.64)],
    wave: [V(-0.66, sh[1] - 0.45, 0.05), V(0.78 + wave, sh[1] + 0.55, 0.1)],
    up: [V(-0.85 - wave * 0.4, sh[1] + 0.6, 0.05), V(0.85 + wave * 0.4, sh[1] + 0.6, 0.05)],
    point: [V(-0.66, sh[1] - 0.45, 0.05), V(1.05, sh[1] + 0.05, 0.25)],
    shrug: [V(-0.88, sh[1] + 0.12, 0.25), V(0.88, sh[1] + 0.12, 0.25)],
    hold: [V(-0.2, sh[1] - 0.2, 0.72), V(0.2, sh[1] - 0.2, 0.72)],
  };
  const [lt, rt] = armTargets[arms];
  const ls = V(-sh[0], sh[1], 0);
  const rs = V(sh[0], sh[1], 0);

  const eyeK = expr === 'shock' ? 1.25 : 1;
  const lx = look[0] * 0.04;
  const ly = look[1] * 0.03;

  const brow = (side: -1 | 1) => {
    const x = side * 0.17;
    let rot = 0;
    let y = faceY + 0.2;
    if (expr === 'angry') rot = side * -0.45;
    if (expr === 'sad') rot = side * 0.4;
    if (expr === 'shock') y += 0.07;
    if (expr === 'smug') {
      if (side === 1) {
        y += 0.05;
        rot = 0.25;
      } else rot = 0;
    }
    if (expr === 'sleepy') return null;
    return (
      <mesh position={onFace(x, y, 0.01)} rotation={[0, side * 0.35, rot + Math.PI / 2]} material={m.ink}>
        <capsuleGeometry args={[0.022, 0.1, 4, 8]} />
      </mesh>
    );
  };

  const eye = (side: -1 | 1) => {
    const x = side * 0.17;
    const pos = onFace(x + lx, faceY + ly, 0);
    if (expr === 'happy' || expr === 'sleepy') {
      return (
        <mesh position={onFace(x, faceY - (expr === 'sleepy' ? 0.02 : 0), 0.005)} rotation={[0, side * 0.35, expr === 'sleepy' ? Math.PI : 0]} material={m.ink}>
          <torusGeometry args={[0.07, 0.02, 8, 24, Math.PI]} />
        </mesh>
      );
    }
    const sy = Math.max(0.08, 1 - blink) * (expr === 'smug' ? 0.55 : 1);
    return (
      <group position={pos} rotation={[0, side * 0.35, 0]} scale={[eyeK, eyeK * sy, eyeK]}>
        <mesh material={m.ink} scale={[0.075, 0.105, 0.04]}>
          <sphereGeometry args={[1, 32, 32]} />
        </mesh>
        <mesh material={m.white} position={[0.025, 0.04, 0.035]}>
          <sphereGeometry args={[0.022, 16, 16]} />
        </mesh>
        <mesh material={m.white} position={[-0.022, -0.035, 0.035]}>
          <sphereGeometry args={[0.01, 12, 12]} />
        </mesh>
      </group>
    );
  };

  const mouthMesh = () => {
    const y = faceY - 0.19;
    const p = onFace(0, y, 0.005);
    switch (mo) {
      case 'open':
        return (
          <group position={p}>
            <mesh material={m.ink} scale={[0.07, 0.085, 0.03]}>
              <sphereGeometry args={[1, 24, 24]} />
            </mesh>
            <mesh material={m.tongue} position={[0, -0.035, 0.02]} scale={[0.045, 0.025, 0.02]}>
              <sphereGeometry args={[1, 16, 16]} />
            </mesh>
          </group>
        );
      case 'o':
        return (
          <mesh position={p} material={m.ink} scale={[0.04, 0.05, 0.02]}>
            <sphereGeometry args={[1, 16, 16]} />
          </mesh>
        );
      case 'grin':
        return (
          <group position={[p[0], p[1] + 0.03, p[2]]}>
            <mesh material={m.ink}>
              <circleGeometry args={[0.1, 32, Math.PI, Math.PI]} />
            </mesh>
            <mesh material={m.tongue} position={[0, -0.06, 0.005]} scale={[0.05, 0.025, 0.01]}>
              <sphereGeometry args={[1, 16, 16]} />
            </mesh>
          </group>
        );
      case 'flat':
        return (
          <mesh position={p} rotation={[0, 0, Math.PI / 2]} material={m.ink}>
            <capsuleGeometry args={[0.02, 0.1, 4, 8]} />
          </mesh>
        );
      case 'frown':
        return (
          <mesh position={[p[0], p[1] - 0.05, p[2]]} material={m.ink}>
            <torusGeometry args={[0.08, 0.02, 8, 24, Math.PI]} />
          </mesh>
        );
      case 'smirk':
        return (
          <mesh position={[p[0] + 0.02, p[1] + 0.03, p[2]]} rotation={[0, 0, Math.PI + 0.35]} material={m.ink}>
            <torusGeometry args={[0.08, 0.02, 8, 24, Math.PI * 0.75]} />
          </mesh>
        );
      case 'smile':
      default:
        return (
          <mesh position={[p[0], p[1] + 0.04, p[2]]} rotation={[0, 0, Math.PI]} material={m.ink}>
            <torusGeometry args={[0.08, 0.02, 8, 24, Math.PI]} />
          </mesh>
        );
    }
  };

  return (
    <group position={position} rotation={[0, rotationY, tilt]} scale={[scale * squash, (scale / squash) * (1 + idle), scale * squash]}>
      {/* feet */}
      <mesh position={[-0.2, 0.07, 0.08]} scale={[0.17, 0.09, 0.22]} material={m.limb} castShadow>
        <sphereGeometry args={[1, 24, 24]} />
      </mesh>
      <mesh position={[0.2, 0.07, 0.08]} scale={[0.17, 0.09, 0.22]} material={m.limb} castShadow>
        <sphereGeometry args={[1, 24, 24]} />
      </mesh>
      {/* body */}
      <mesh position={[0, centerY, 0]} material={m.body} castShadow>
        <capsuleGeometry args={[BODY_R, bodyH, 16, 48]} />
      </mesh>
      {/* cheeks */}
      <mesh position={onFace(-0.27, faceY - 0.12, -0.01)} rotation={[0, -0.6, 0]} scale={[0.07, 0.04, 0.02]} material={m.cheek}>
        <sphereGeometry args={[1, 16, 16]} />
      </mesh>
      <mesh position={onFace(0.27, faceY - 0.12, -0.01)} rotation={[0, 0.6, 0]} scale={[0.07, 0.04, 0.02]} material={m.cheek}>
        <sphereGeometry args={[1, 16, 16]} />
      </mesh>
      {eye(-1)}
      {eye(1)}
      {brow(-1)}
      {brow(1)}
      {mouthMesh()}
      {shades && (
        <group position={onFace(0, faceY + 0.01, 0.04)}>
          <mesh position={[-0.17, 0, 0]} material={m.ink}>
            <boxGeometry args={[0.2, 0.13, 0.03]} />
          </mesh>
          <mesh position={[0.17, 0, 0]} material={m.ink}>
            <boxGeometry args={[0.2, 0.13, 0.03]} />
          </mesh>
          <mesh position={[0, 0.03, 0]} material={m.ink}>
            <boxGeometry args={[0.5, 0.025, 0.03]} />
          </mesh>
        </group>
      )}
      {nightcap && (
        <group position={[0, centerY + bodyH / 2 + 0.15, 0]} rotation={[0, 0, -0.35]}>
          <mesh material={m.cap} position={[0.08, 0.22, 0]}>
            <coneGeometry args={[0.42, 0.75, 32]} />
          </mesh>
          <mesh material={m.capTrim} rotation={[Math.PI / 2, 0, 0]} position={[0, -0.12, 0]}>
            <torusGeometry args={[0.44, 0.07, 12, 40]} />
          </mesh>
          <mesh material={m.capTrim} position={[0.16, 0.62, 0]}>
            <sphereGeometry args={[0.09, 16, 16]} />
          </mesh>
        </group>
      )}
      <Limb from={ls} to={lt} mat={m.limb} handMat={m.body} />
      <Limb from={rs} to={rt} mat={m.limb} handMat={m.body} hand={arms === 'stop' || arms === 'wave' ? 0.14 : 0.11} />
    </group>
  );
};
