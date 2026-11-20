import {expect,it,vi} from 'vitest';
import {retainResource} from './retainedResource';
it('keeps GPU resources alive during StrictMode rehearsal and disposes after real unmount',async()=>{
 const gpu={},dispose=vi.fn();
 const rehearsal=retainResource(gpu,dispose);rehearsal();
 const mounted=retainResource(gpu,dispose);
 await Promise.resolve();expect(dispose).not.toHaveBeenCalled();
 mounted();mounted();await Promise.resolve();expect(dispose).toHaveBeenCalledTimes(1);
});
it('releases a replaced model without disposing the new scene',async()=>{
 const oldModel={},newModel={},oldDispose=vi.fn(),newDispose=vi.fn();
 const release=retainResource(oldModel,oldDispose);retainResource(newModel,newDispose);release();
 await Promise.resolve();expect(oldDispose).toHaveBeenCalledOnce();expect(newDispose).not.toHaveBeenCalled();
});
