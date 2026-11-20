export type StorageStatus={
  policy:'local-storage-v1';measured_at:string;state:'READY'|'WARNING'|'BLOCKED';reason:string;message:string;
  acquisition_allowed:boolean;automatic_deletion:false;
  data:{bytes:number;limit_bytes:number;files:number;errors:number};output:{bytes:number;limit_bytes:number;files:number;errors:number};
  total_bytes:number;total_limit_bytes:number;free_bytes:number|null;min_free_bytes:number;reserve_bytes:number;scope:string;recovery:string;
};
const count=(value:unknown):value is number=>typeof value==='number'&&Number.isSafeInteger(value)&&value>=0;
export function validateStorageStatus(value:unknown):StorageStatus{
  const v=value as StorageStatus;
  if(!v||v.policy!=='local-storage-v1'||!['READY','WARNING','BLOCKED'].includes(v.state)
    ||typeof v.measured_at!=='string'||!Number.isFinite(Date.parse(v.measured_at))
    ||typeof v.acquisition_allowed!=='boolean'||v.automatic_deletion!==false
    ||!['READY','DATA_LIMIT','OUTPUT_LIMIT','TOTAL_LIMIT','FREE_SPACE','INVENTORY_UNAVAILABLE'].includes(v.reason)
    ||(v.state==='BLOCKED')===v.acquisition_allowed||(v.reason==='READY')!==v.acquisition_allowed
    ||[v.message,v.scope,v.recovery].some(x=>typeof x!=='string')
    ||[v.total_bytes,v.total_limit_bytes,v.min_free_bytes,v.reserve_bytes].some(x=>!count(x))
    ||(v.free_bytes!==null&&!count(v.free_bytes))
    ||[v.data,v.output].some(d=>!d||!count(d.bytes)||!count(d.files)||!count(d.errors)||!count(d.limit_bytes)||d.limit_bytes===0)
    ||v.total_bytes!==v.data.bytes+v.output.bytes||v.total_limit_bytes===0
    ||(v.acquisition_allowed&&(v.free_bytes===null||v.free_bytes<v.min_free_bytes+v.reserve_bytes
      ||v.data.bytes+v.reserve_bytes>v.data.limit_bytes||v.output.bytes>v.output.limit_bytes
      ||v.total_bytes+v.reserve_bytes>v.total_limit_bytes||v.data.errors+v.output.errors>0)))
    throw new Error('No se puede verificar el almacenamiento.');
  return v;
}
export async function readStorage(signal?:AbortSignal){
  const response=await fetch('/api/storage/status',{signal});
  if(!response.ok)throw new Error('No se puede consultar el almacenamiento.');
  return validateStorageStatus(await response.json());
}
