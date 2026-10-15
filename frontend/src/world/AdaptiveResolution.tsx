import { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { AdaptiveDprController, type DprChange, type DprReason } from './adaptiveDpr';
import { QUALITY, type Quality } from './layout';
import type { PlayerRuntime } from './navigation';

interface ResolutionTelemetry {
  profile: Quality; dpr: number; signalFps: number | null; reason: DprReason;
  changes: (DprChange & { at: number })[];
}
declare global { interface Window { __HQ_DPR__?: ResolutionTelemetry } }

export default function AdaptiveResolution({ quality, player, onDprChange }: {
  quality: Quality; player: PlayerRuntime; onDprChange: (dpr: number) => void;
}) {
  const setDpr = useThree(state => state.setDpr);
  const gl = useThree(state => state.gl);
  const controller = useRef(new AdaptiveDprController());
  const previous = useRef(0), revision = useRef(player.revision), published = useRef(0);
  const idleSince = useRef(0);
  const changes = useRef<ResolutionTelemetry['changes']>([]);
  useEffect(() => {
    controller.current = new AdaptiveDprController();
    changes.current = [];
    previous.current = 0;
    setDpr(QUALITY[quality].dpr);
    onDprChange(QUALITY[quality].dpr);
  }, [quality, setDpr, onDprChange]);
  useEffect(() => {
    const reset = () => { previous.current = 0; controller.current.suspend(); };
    window.addEventListener('resize', reset);
    document.addEventListener('visibilitychange', reset);
    return () => {
      window.removeEventListener('resize', reset);
      document.removeEventListener('visibilitychange', reset);
      delete window.__HQ_DPR__;
    };
  }, []);
  useFrame(() => {
    const now = performance.now();
    const available = quality === 'balanced' && !document.hidden && player.mode === 'play' && !player.paused && !gl.getContext().isContextLost();
    const eligible = available && player.speed > .1;
    if (!available || revision.current !== player.revision) {
      revision.current = player.revision;
      previous.current = 0;
      controller.current.suspend();
    } else if (!eligible) {
      if(!idleSince.current)idleSince.current=now;
      if(now-idleSince.current>300)controller.current.suspend();
    } else if (previous.current) {
      const change = controller.current.observe(now - previous.current, true);
      if (change) {
        // Canvas recibe el mismo valor: sus reconfiguraciones no restauran el DPR inicial.
        setDpr(change.to);
        onDprChange(change.to);
        changes.current.push({ ...change, at: now });
        if (changes.current.length > 80) changes.current.shift();
      }
    }
    if(eligible)idleSince.current=0;
    previous.current = eligible ? now : 0;
    if (now - published.current > 500) {
      published.current = now;
      window.__HQ_DPR__ = { profile: quality, dpr: gl.getPixelRatio(), signalFps: controller.current.fps,
        reason: controller.current.reason, changes: [...changes.current] };
    }
  }, -.5);
  return null;
}
