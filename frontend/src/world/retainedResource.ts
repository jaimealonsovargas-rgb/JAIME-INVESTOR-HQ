/** Defer disposal through React's setup → cleanup → setup effect rehearsal. */
const owners=new WeakMap<object,{count:number;dispose:()=>void}>();
export function retainResource(resource:object,dispose:()=>void){
 let owner=owners.get(resource);
 if(!owner){owner={count:0,dispose};owners.set(resource,owner);}
 owner.count++;
 const retained=owner;
 let released=false;
 return ()=>{
  if(released)return;
  released=true;retained.count--;
  queueMicrotask(()=>{
   if(retained.count===0&&owners.get(resource)===retained){owners.delete(resource);retained.dispose();}
  });
 };
}
