import React from 'react';
import {Bedroom, Blanket} from './sets';
import {Cam, Stage, StudioLights} from './Stage';
import {Doug3D, Doug3DProps} from './Doug3D';
import {Wally3D, Wally3DProps} from './Wally3D';

export type BedSceneProps = {
  clock: string;
  doug?: Doug3DProps;
  wally?: Wally3DProps | null;
  asleep?: boolean;
  lamp?: number;
  cam?: {pos: [number, number, number]; look: [number, number, number]; fov?: number};
  moonY?: number;
};

export const BED_CAM = {pos: [1.0, 2.75, 5.2] as [number, number, number], look: [0.15, 1.8, -0.9] as [number, number, number], fov: 38};

// Doug's bedroom at night. Sitting up against the headboard by default;
// `asleep` lays him down under the blanket.
export const BedScene: React.FC<BedSceneProps> = ({clock, doug, wally, asleep, lamp = 0, cam = BED_CAM, moonY}) => (
  <Stage bg="#120F1C">
    <Cam {...cam} />
    <StudioLights key_={asleep ? 0.7 : 1.3} ambient={0.5} keyColor="#C9D2FF" />
    <Bedroom clock={clock} lamp={lamp} moonY={moonY} />
    {asleep ? (
      <>
        <Doug3D position={[0, 0.8, -0.3]} rotation={[-Math.PI / 2, 0, 0]} expr="sleep" arms="down" scrolling={false} {...doug} />
        <Blanket position={[0, 0.82, 0.25]} up={0.08} />
      </>
    ) : (
      <>
        <Doug3D position={[0, 0.36, -1.05]} legs="sit" {...doug} />
        <Blanket position={[0, 0.74, -0.05]} />
      </>
    )}
    {wally && <Wally3D {...wally} />}
  </Stage>
);
