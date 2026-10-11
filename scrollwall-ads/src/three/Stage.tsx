import React from 'react';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {useVideoConfig} from 'remotion';

// Points the camera every frame. Camera moves are driven by props computed
// from the frame number, so renders are deterministic.
export const Cam: React.FC<{pos: [number, number, number]; look: [number, number, number]; fov?: number}> = ({pos, look, fov = 32}) => {
  const {camera} = useThree();
  const cam = camera as THREE.PerspectiveCamera;
  cam.position.set(...pos);
  if (cam.fov !== fov) {
    cam.fov = fov;
    cam.updateProjectionMatrix();
  }
  cam.lookAt(new THREE.Vector3(...look));
  return null;
};

export const Stage: React.FC<{children: React.ReactNode; bg?: string}> = ({children, bg = '#0B0A0F'}) => {
  const {width, height} = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      shadows
      gl={{antialias: true, toneMapping: THREE.ACESFilmicToneMapping, outputColorSpace: THREE.SRGBColorSpace}}
      style={{background: bg}}
    >
      {children}
    </ThreeCanvas>
  );
};

// Soft three-point setup with Scrollwall's violet rim.
export const StudioLights: React.FC<{key_?: number; rim?: string; ambient?: number; keyColor?: string}> = ({
  key_ = 2.4,
  rim = '#8E6BD4',
  ambient = 0.55,
  keyColor = '#FFF4EA',
}) => (
  <>
    <ambientLight intensity={ambient} />
    <hemisphereLight args={['#CBB8FF', '#1A1424', 0.5]} />
    <directionalLight
      position={[3, 6, 5]}
      intensity={key_}
      color={keyColor}
      castShadow
      shadow-mapSize-width={2048}
      shadow-mapSize-height={2048}
      shadow-camera-left={-6}
      shadow-camera-right={6}
      shadow-camera-top={6}
      shadow-camera-bottom={-6}
      shadow-bias={-0.0004}
    />
    <pointLight position={[-3, 3, -3]} intensity={40} color={rim} />
    <pointLight position={[3, 1.5, -2]} intensity={18} color="#E8914A" />
  </>
);
