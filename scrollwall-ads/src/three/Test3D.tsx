import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Wally3D} from './Wally3D';
import {Doug3D} from './Doug3D';
import {Cam, Stage, StudioLights} from './Stage';

export const Test3D: React.FC = () => (
  <AbsoluteFill>
    <Stage>
      <Cam pos={[0, 1.7, 8.5]} look={[0, 1.0, 0]} fov={30} />
      <StudioLights />
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#1B1824" />
      </mesh>
      <Doug3D position={[-0.7, 0, 0.6]} expr="tired" arms="phone" look={[0, -1]} rotation={[0, 0.3, 0]} />
      <Wally3D position={[0.85, 0, 0]} expr="smug" mouth="smirk" arms="cross" rotationY={-0.35} scale={0.95} />
      <Doug3D position={[-0.9, 0, -2.5]} expr="shock" arms="up" screen="off" />
      <Wally3D position={[1.0, 0, -2.5]} expr="happy" mouth="grin" arms="wave" nightcap scale={0.95} />
    </Stage>
  </AbsoluteFill>
);
