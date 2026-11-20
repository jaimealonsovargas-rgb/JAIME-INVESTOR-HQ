import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {validateStorageStatus,type StorageStatus} from '../storageApi';
import StoragePanel from './StoragePanel';

const sample:StorageStatus={policy:'local-storage-v1',measured_at:'2026-11-08T12:00:00Z',state:'READY',reason:'READY',message:'Hay margen.',
  acquisition_allowed:true,automatic_deletion:false,data:{bytes:100,limit_bytes:1000,files:1,errors:0},
  output:{bytes:200,limit_bytes:1000,files:2,errors:0},total_bytes:300,total_limit_bytes:2000,
  free_bytes:10000,min_free_bytes:500,reserve_bytes:100,scope:'Ámbito local',recovery:'Cola conservada'};
function render(data?:StorageStatus){
  const client=new QueryClient();if(data)client.setQueryData(['storage-budget'],data);
  const html=renderToStaticMarkup(<QueryClientProvider client={client}><StoragePanel/></QueryClientProvider>);client.clear();return html;
}
describe('storage admission panel',()=>{
  it('shows measured usage and preservation without promising deletion',()=>{
    const html=render(validateStorageStatus(sample));
    expect(html).toContain('Espacio disponible');expect(html).toContain('Sin borrado automático');
    expect(html).toContain('Madrid');expect(html).not.toContain('<details open');
  });
  it('does not show permission until measured and distinguishes the halt',()=>{
    expect(render()).not.toContain('Espacio disponible');
    expect(render({...sample,state:'BLOCKED',reason:'FREE_SPACE',acquisition_allowed:false})).toContain('Captación detenida');
  });
  it.each([{...sample,total_bytes:0},{...sample,free_bytes:-1},{...sample,data:null},
    {...sample,state:'BLOCKED'},{...sample,free_bytes:510},{...sample,data:{...sample.data,errors:1}},
    {...sample,automatic_deletion:true}])('rejects incomplete or contradictory measurements',value=>{
    expect(()=>validateStorageStatus(value)).toThrow();
  });
});
