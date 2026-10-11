import React from 'react';
import {Composition, Still} from 'remotion';
import './fonts';
import {FPS, H, W} from './brand';
import {Test3D} from './three/Test3D';
import {EP1_DURATION, Ep1IgnoreLimit} from './ads/Ep1IgnoreLimit';
import {EP2_DURATION, Ep2Toilet} from './ads/Ep2Toilet';
import {EP3_DURATION, Ep3EarnIt} from './ads/Ep3EarnIt';
import {EP4_DURATION, Ep4Loop} from './ads/Ep4Loop';

export const Root: React.FC = () => (
  <>
    <Composition id="Ep1-IgnoreLimit" component={Ep1IgnoreLimit} durationInFrames={EP1_DURATION} fps={FPS} width={W} height={H} />
    <Composition id="Ep2-Toilet" component={Ep2Toilet} durationInFrames={EP2_DURATION} fps={FPS} width={W} height={H} />
    <Composition id="Ep3-EarnIt" component={Ep3EarnIt} durationInFrames={EP3_DURATION} fps={FPS} width={W} height={H} />
    <Composition id="Ep4-Loop" component={Ep4Loop} durationInFrames={EP4_DURATION} fps={FPS} width={W} height={H} />
    <Still id="CastSheet" component={Test3D} width={W} height={H} />
  </>
);
