export function frameStats(frames:number[]) {
 const sorted=[...frames].sort((a,b)=>a-b);
 return {fps:frames.length?1000*frames.length/frames.reduce((a,b)=>a+b,0):0,p95:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.95))]??0,samples:frames.length};
}
