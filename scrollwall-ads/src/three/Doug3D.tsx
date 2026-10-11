import React, {useMemo} from 'react';
import * as THREE from 'three';
import {useCurrentFrame} from 'remotion';
import {Limb, Phone3D, ScreenMode, V} from './parts';

// Doug — the relatable one. Hoodie up, eye bags down, phone permanently
// eighteen centimetres from his face.

export type DougExpr = 'tired' | 'dead' | 'shock' | 'happy' | 'focus' | 'sleep' | 'sneaky' | 'sad' | 'neutral';
export type DougArms = 'phone' | 'down' | 'up' | 'desk' | 'reach' | 'book' | 'shrug';
export type DougLegs = 'stand' | 'sit' | 'walk';

export type Doug3DProps = {
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
  squash?: number;
  expr?: DougExpr;
  arms?: DougArms;
  legs?: DougLegs;
  screen?: ScreenMode;
  phoneGlow?: number;
  scrolling?: boolean; // thumb-flick wobble on the phone
  talk?: boolean;
  look?: [number, number];
  headTilt?: number;
  wobble?: number; // numb-legs shake 0..1
};

const BODY_R = 0.4;
const BODY_L = 0.34;
const CY = 0.3 + BODY_R + BODY_L / 2; // body centre, feet at 0
const HY = 1.52; // head centre
const HR = 0.42; // head radius
const FACE_Y = HY - 0.02;

// A point on the head's surface, for placing face features.
const onHead = (x: number, y: number, lift = 0): [number, number, number] => {
  const dy = y - HY;
  const z = Math.sqrt(Math.max(0, HR * HR - x * x - dy * dy)) + lift;
  return [x, y, z];
};

export const Doug3D: React.FC<Doug3DProps> = ({
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  scale = 1,
  squash = 1,
  expr = 'tired',
  arms = 'phone',
  legs = 'stand',
  screen = 'feed',
  phoneGlow = 1,
  scrolling = true,
  talk = false,
  look = [0, 0],
  headTilt = 0,
  wobble = 0,
}) => {
  const f = useCurrentFrame();
  const m = useMemo(
    () => ({
      hoodie: new THREE.MeshPhysicalMaterial({color: '#4B4563', roughness: 0.9, sheen: 1, sheenColor: new THREE.Color('#8E7FB8')}),
      hood: new THREE.MeshPhysicalMaterial({color: '#5A5375', roughness: 0.9, sheen: 1, sheenColor: new THREE.Color('#9C8FC8')}),
      pants: new THREE.MeshStandardMaterial({color: '#2B2836', roughness: 0.95}),
      skin: new THREE.MeshPhysicalMaterial({color: '#F2C3A0', roughness: 0.55, sheen: 0.4, sheenColor: new THREE.Color('#FFB59A')}),
      hair: new THREE.MeshStandardMaterial({color: '#3A2A22', roughness: 0.8}),
      white: new THREE.MeshPhysicalMaterial({color: '#FFFFFF', roughness: 0.2, clearcoat: 1}),
      ink: new THREE.MeshPhysicalMaterial({color: '#141219', roughness: 0.15, clearcoat: 1}),
      bags: new THREE.MeshStandardMaterial({color: '#9A6E8E', roughness: 0.9}),
      shoe: new THREE.MeshPhysicalMaterial({color: '#F4F2F8', roughness: 0.5}),
      sole: new THREE.MeshStandardMaterial({color: '#8E6BD4', roughness: 0.6}),
      string: new THREE.MeshStandardMaterial({color: '#E8E4F2', roughness: 0.7}),
    }),
    [],
  );

  const cyc = (f + 53) % 95;
  const blink = cyc < 5 ? Math.sin((cyc / 5) * Math.PI) : 0;
  const flick = scrolling ? Math.max(0, Math.sin(((f % 9) / 9) * Math.PI * 2)) * 0.12 : 0;
  const shake = wobble * Math.sin(f * 2.3) * 0.04;
  const walk = legs === 'walk' ? Math.sin(f / 3) : 0;

  // How closed the eyelids are.
  const lid = {tired: 0.45, dead: 0.7, shock: 0, happy: 0, focus: 0.3, sleep: 1, sneaky: 0.5, sad: 0.25, neutral: 0.12}[expr];

  const sh = CY + 0.22;
  const handTargets: Record<DougArms, [THREE.Vector3, THREE.Vector3]> = {
    phone: [V(-0.12, CY + 0.12, 0.5), V(0.12, CY + 0.12, 0.5)],
    down: [V(-0.55, CY - 0.3, 0.06), V(0.55, CY - 0.3, 0.06)],
    up: [V(-0.75, CY + 0.85, 0.1), V(0.75, CY + 0.85, 0.1)],
    desk: [V(-0.28, CY - 0.02, 0.6), V(0.28, CY - 0.02, 0.6)],
    reach: [V(-0.5, CY - 0.28, 0.12), V(0.35, CY + 0.05, 0.85)],
    book: [V(-0.2, CY + 0.08, 0.52), V(0.2, CY + 0.08, 0.52)],
    shrug: [V(-0.72, CY + 0.2, 0.25), V(0.72, CY + 0.2, 0.25)],
  };
  const [lh, rh] = handTargets[arms];

  const hip = 0.42;
  const legPts = (side: -1 | 1): [THREE.Vector3, THREE.Vector3] => {
    if (legs === 'sit') return [V(side * 0.17, hip + 0.03, 0.1), V(side * 0.19, hip - 0.04, 0.55)];
    return [V(side * 0.17, hip, 0), V(side * 0.19, 0.1, side * walk * 0.18)];
  };

  const eye = (side: -1 | 1) => {
    const x = side * 0.14;
    const y = FACE_Y + 0.04;
    if (expr === 'happy' || expr === 'sleep') {
      return (
        <mesh position={onHead(x, y, 0.005)} rotation={[0, 0, expr === 'sleep' ? Math.PI : 0]} material={m.ink}>
          <torusGeometry args={[0.055, 0.015, 8, 20, Math.PI]} />
        </mesh>
      );
    }
    const k = expr === 'shock' ? 1.3 : 1;
    const closed = Math.min(1, lid + blink * (1 - lid));
    return (
      <group position={onHead(x, y, -0.03)} rotation={[0, side * 0.33, 0]} scale={k}>
        <mesh material={m.white} scale={[0.07, 0.085, 0.04]}>
          <sphereGeometry args={[1, 24, 24]} />
        </mesh>
        <mesh material={m.ink} position={[look[0] * 0.02, look[1] * 0.02 - 0.01, 0.035]}>
          <sphereGeometry args={[0.033, 16, 16]} />
        </mesh>
        <mesh material={m.white} position={[look[0] * 0.02 + 0.012, look[1] * 0.02 + 0.005, 0.064]}>
          <sphereGeometry args={[0.009, 8, 8]} />
        </mesh>
        {closed > 0.01 && (
          // eyelid: a skin dome that slides down over the eye
          <mesh material={m.skin} position={[0, 0.085 - closed * 0.085, 0.012]} scale={[0.078, 0.02 + closed * 0.075, 0.05]}>
            <sphereGeometry args={[1, 20, 20]} />
          </mesh>
        )}
      </group>
    );
  };

  const mouth = () => {
    const p = onHead(0, FACE_Y - 0.14, 0.003);
    if (talk && Math.floor(f / 4) % 2 === 0) {
      return (
        <mesh position={p} material={m.ink} scale={[0.04, 0.045, 0.02]}>
          <sphereGeometry args={[1, 16, 16]} />
        </mesh>
      );
    }
    switch (expr) {
      case 'shock':
        return (
          <mesh position={p} material={m.ink} scale={[0.045, 0.06, 0.02]}>
            <sphereGeometry args={[1, 16, 16]} />
          </mesh>
        );
      case 'happy':
        return (
          <mesh position={[p[0], p[1] + 0.02, p[2]]} material={m.ink}>
            <circleGeometry args={[0.065, 24, Math.PI, Math.PI]} />
          </mesh>
        );
      case 'sad':
      case 'dead':
        return (
          <mesh position={[p[0], p[1] - 0.035, p[2]]} material={m.ink}>
            <torusGeometry args={[0.05, 0.012, 8, 20, Math.PI]} />
          </mesh>
        );
      case 'sneaky':
        return (
          <mesh position={[p[0] + 0.02, p[1] + 0.02, p[2]]} rotation={[0, 0, Math.PI + 0.4]} material={m.ink}>
            <torusGeometry args={[0.05, 0.012, 8, 20, Math.PI * 0.7]} />
          </mesh>
        );
      case 'sleep':
        return (
          <mesh position={p} material={m.ink} scale={[0.022, 0.026, 0.01]}>
            <sphereGeometry args={[1, 12, 12]} />
          </mesh>
        );
      default:
        return (
          <mesh position={p} rotation={[0, 0, Math.PI / 2]} material={m.ink}>
            <capsuleGeometry args={[0.012, 0.06, 4, 8]} />
          </mesh>
        );
    }
  };

  const headRot: [number, number, number] = [arms === 'phone' || arms === 'book' ? 0.22 : 0, 0, headTilt];

  return (
    <group position={[position[0] + shake, position[1], position[2]]} rotation={rotation} scale={[scale * squash, scale / squash, scale * squash]}>
      {/* legs + sneakers */}
      {([-1, 1] as const).map((side) => {
        const [a, b] = legPts(side);
        return (
          <group key={side}>
            <Limb from={a} to={b} r={0.11} mat={m.pants} handMat={m.pants} hand={0.11} />
            <mesh position={[b.x, b.y - 0.02, b.z + 0.06]} scale={[0.13, 0.08, 0.2]} material={m.shoe} castShadow>
              <sphereGeometry args={[1, 20, 20]} />
            </mesh>
            <mesh position={[b.x, b.y - 0.07, b.z + 0.06]} scale={[0.135, 0.025, 0.205]} material={m.sole}>
              <sphereGeometry args={[1, 20, 20]} />
            </mesh>
          </group>
        );
      })}
      {/* hoodie body */}
      <mesh position={[0, CY, 0]} material={m.hoodie} castShadow>
        <capsuleGeometry args={[BODY_R, BODY_L, 16, 40]} />
      </mesh>
      {/* front pocket */}
      <mesh position={[0, CY - 0.16, 0.34]} rotation={[-0.3, 0, 0]} scale={[0.24, 0.1, 0.06]} material={m.hood}>
        <sphereGeometry args={[1, 20, 20]} />
      </mesh>
      {/* head (tilts toward the phone) */}
      <group position={[0, HY - 0.3, 0]} rotation={headRot}>
        <group position={[0, -(HY - 0.3), 0]}>
          {/* hood shell behind the head */}
          <mesh position={[0, HY + 0.05, -0.16]} scale={[1, 1.02, 1]} material={m.hoodie} castShadow>
            <sphereGeometry args={[0.52, 40, 40]} />
          </mesh>
          {/* hood rim framing the face */}
          <mesh position={[0, HY + 0.02, 0.24]} scale={[1, 1.06, 1]} material={m.hood}>
            <torusGeometry args={[0.36, 0.075, 16, 48]} />
          </mesh>
          {/* head */}
          <mesh position={[0, HY, 0]} material={m.skin} castShadow>
            <sphereGeometry args={[HR, 40, 40]} />
          </mesh>
          {/* messy fringe poking out of the hood */}
          {[-0.14, -0.02, 0.1, 0.2].map((x, i) => (
            <mesh key={i} position={onHead(x, HY + 0.27, -0.04)} rotation={[1.1, 0, (i - 1.5) * 0.45]} material={m.hair}>
              <capsuleGeometry args={[0.055, 0.09, 4, 10]} />
            </mesh>
          ))}
          {eye(-1)}
          {eye(1)}
          {/* eye bags */}
          {(expr === 'tired' || expr === 'dead' || expr === 'sneaky') &&
            ([-1, 1] as const).map((s) => (
              <mesh key={s} position={onHead(s * 0.14, FACE_Y - 0.04, 0.0)} rotation={[0, s * 0.33, Math.PI]} material={m.bags}>
                <torusGeometry args={[0.05, 0.01, 6, 16, Math.PI]} />
              </mesh>
            ))}
          {/* cheeks */}
          {([-1, 1] as const).map((s) => (
            <mesh key={`c${s}`} position={onHead(s * 0.25, FACE_Y - 0.09, -0.02)} rotation={[0, s * 0.6, 0]} scale={[0.06, 0.035, 0.02]}>
              <sphereGeometry args={[1, 12, 12]} />
              <meshStandardMaterial color="#F08F8F" transparent opacity={0.45} />
            </mesh>
          ))}
          {mouth()}
        </group>
      </group>
      {/* drawstrings */}
      {([-1, 1] as const).map((s) => (
        <group key={s}>
          <mesh position={[s * 0.09, CY + 0.2, 0.38]} material={m.string}>
            <cylinderGeometry args={[0.012, 0.012, 0.2, 8]} />
          </mesh>
          <mesh position={[s * 0.09, CY + 0.09, 0.38]} material={m.string}>
            <sphereGeometry args={[0.02, 8, 8]} />
          </mesh>
        </group>
      ))}
      <Limb from={V(-0.36, sh, 0)} to={lh} r={0.085} mat={m.hoodie} handMat={m.skin} hand={0.09} />
      <Limb from={V(0.36, sh, 0)} to={rh} r={0.085} mat={m.hoodie} handMat={m.skin} hand={0.09} />
      {arms === 'phone' && (
        <Phone3D
          frame={f}
          mode={screen}
          glow={phoneGlow}
          position={[0, CY + 0.2, 0.56]}
          rotation={[0.55 + flick, Math.PI, 0]}
          scale={0.62}
        />
      )}
      {arms === 'book' && (
        <group position={[0, CY + 0.12, 0.6]} rotation={[-0.7, 0, 0]}>
          <mesh position={[-0.17, 0, 0]} rotation={[0, 0.25, 0]}>
            <boxGeometry args={[0.32, 0.42, 0.02]} />
            <meshStandardMaterial color="#F7F5FA" />
          </mesh>
          <mesh position={[0.17, 0, 0]} rotation={[0, -0.25, 0]}>
            <boxGeometry args={[0.32, 0.42, 0.02]} />
            <meshStandardMaterial color="#EDE6FF" />
          </mesh>
        </group>
      )}
    </group>
  );
};
