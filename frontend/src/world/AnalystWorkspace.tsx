import MonitorOverlay from './MonitorOverlay';
import {PERSONNEL} from './staffLayout';
import './world.css';

/** Direct, keyboard-friendly access; the same inspector without loading WebGL. */
export default function AnalystWorkspace({personId}:{personId:string}) {
 const person=PERSONNEL.find(p=>p.id===personId);
 if(!person)return <main><h1>Especialista no encontrado</h1><a href="/">Volver a la oficina</a></main>;
 return <main className="world" aria-label="Espacio de análisis"><MonitorOverlay id={person.department} personId={person.id} onClose={()=>window.location.assign('/')}/></main>;
}
