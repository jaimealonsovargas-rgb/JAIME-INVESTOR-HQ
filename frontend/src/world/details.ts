import { BoxGeometry, BufferGeometry, Float32BufferAttribute, LatheGeometry, Vector2 } from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

// Geometría original compartida: las formas se modelan una vez y luego se fusionan.
export function chairBack() {
  const points:number[]=[],uv:number[]=[],indices:number[]=[];
  const rows=18,cols=10,n=(rows+1)*(cols+1);
  // Superficie continua y normales compartidas: evita caras triangulares visibles
  // al curvar una tapa de extrusión plana.
  for(let side=0;side<2;side++) for(let r=0;r<=rows;r++) for(let c=0;c<=cols;c++) {
    const t=r/rows,u=c/cols*2-1,y=t*.71-.35;
    const lower=(t-.02)/.11,upper=(t-1)/.12;
    const width=.225+.045*Math.sin(Math.PI*t)-.075*Math.exp(-lower*lower)-.10*Math.exp(-upper*upper)-.04*Math.sin(2*Math.PI*t);
    const z=.11*u*u-.055*Math.cos(y*6);
    points.push(u*width,y,z+(side?-.022:.022+.022*(1-u*u)*Math.sin(Math.PI*t)));uv.push(c/cols,t);
    if(r<rows&&c<cols) {const a=side*n+r*(cols+1)+c,b=a+cols+1;indices.push(...(side?[a,b,a+1,a+1,b,b+1]:[a,a+1,b,a+1,b+1,b]));}
  }
  const edge=(a:number,b:number,reverse=false)=>indices.push(...(reverse?[a,a+n,b+n,a,b+n,b]:[a,b,b+n,a,b+n,a+n]));
  for(let r=0;r<rows;r++){edge(r*(cols+1),(r+1)*(cols+1));edge(r*(cols+1)+cols,(r+1)*(cols+1)+cols,true);}
  for(let c=0;c<cols;c++){edge(c,c+1,true);edge(rows*(cols+1)+c,rows*(cols+1)+c+1);}
  const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(points,3));g.setAttribute('uv',new Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();return g;
}

export function chairSeat() {
  const g = new RoundedBoxGeometry(.57, .115, .56, 3, .05);
  const p = g.getAttribute('position');
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i);
    p.setXYZ(i, x * (.94 + z * .12), p.getY(i) - .018 * (x / .285) ** 2, z);
  }
  g.computeVertexNormals(); return g;
}

export function leafGeometry() {
  const points: number[] = [], uv: number[] = [], indices: number[] = [];
  const rows = 10, cols = 4;
  for (let r = 0; r <= rows; r++) for (let c = 0; c <= cols; c++) {
    const t = r / rows, s = c / cols * 2 - 1;
    const width = Math.pow(Math.sin(Math.PI * t), .8) * .12;
    points.push(s * width, .065 * Math.sin(t * Math.PI) - .038 * Math.abs(s) - .06 * t * t, t * .48);
    uv.push(c / cols, t);
    if (r < rows && c < cols) { const a = r * (cols + 1) + c; indices.push(a, a + 1, a + cols + 1, a + 1, a + cols + 2, a + cols + 1); }
  }
  const g = new BufferGeometry(); g.setAttribute('position', new Float32BufferAttribute(points, 3));
  g.setAttribute('uv', new Float32BufferAttribute(uv, 2)); g.setIndex(indices); g.computeVertexNormals(); return g;
}

export function planterGeometry() {
  return new LatheGeometry([[.18,0],[.22,.035],[.27,.46],[.275,.55],[.25,.56],[.245,.51],[.19,.04]].map(p => new Vector2(...p as [number, number])), 24);
}

export function facadeGeometry(w: number, h: number, d: number) {
  const g = new BoxGeometry(w, h, d); const uv = g.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) {
    const width = i < 8 ? d : w;
    uv.setXY(i, uv.getX(i) * width / 5, uv.getY(i) * (i >= 8 && i < 16 ? d : h) / 9);
  }
  return g;
}
