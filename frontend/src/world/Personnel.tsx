import {Suspense,memo} from 'react';
import type {Material} from 'three';
import Avatar from './Avatar';
import {PERSONNEL} from './staffLayout';
export default memo(function Personnel({contact}:{contact:Material}) {
 return <group name="personal-offline"><Suspense fallback={null}>{PERSONNEL.map(p=><group key={p.id} name={p.id} position={p.position} rotation={[0,p.yaw,0]}><group scale={1+(p.variant%3-1)*.015}><Avatar id={p.id} variant={p.variant} npc contact={contact}/></group></group>)}</Suspense></group>;
});
