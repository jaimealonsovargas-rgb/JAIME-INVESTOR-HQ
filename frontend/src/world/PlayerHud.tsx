import { useEffect, useState } from 'react';
import { DEPARTMENTS } from './layout';
import { validTeleport, type PlayerRuntime } from './navigation';

export default function PlayerHud({player}:{player:PlayerRuntime}) {
  const [pose,setPose]=useState(()=>({x:player.position.x,z:player.position.z,yaw:player.yaw}));
  const [message,setMessage]=useState('');
  useEffect(()=>{const timer=setInterval(()=>setPose({x:player.position.x,z:player.position.z,yaw:player.yaw}),150);return()=>clearInterval(timer);},[player]);
  return <aside className="minimap" aria-label="Minimapa y teletransportes seguros"><div className="minimap-title">SEDE · PLANTA 01 <span>34 × 28 m</span></div><div className="minimap-grid">{DEPARTMENTS.map(d=><button key={d.id} title={d.label} aria-label={`Ir a ${d.label}`} onClick={()=>{const spawn=validTeleport(d.id,player.colliders);if(!spawn){setMessage('Punto de acceso no disponible.');return;}player.position.copy(spawn);player.yaw=0;player.cameraYaw=0;player.speed=0;player.revision++;setMessage(d.label);document.querySelector('canvas')?.focus();}}><span>{d.number}</span>{d.label}</button>)}<span className="minimap-player" style={{left:`${(pose.x/34+.5)*100}%`,top:`${(pose.z/28+.5)*100}%`,transform:`translate(-50%,-50%) rotate(${-pose.yaw*180/Math.PI}deg)`}} aria-hidden="true">▲</span></div><p role="status">{message||'Selecciona un departamento para ir'}</p></aside>;
}
