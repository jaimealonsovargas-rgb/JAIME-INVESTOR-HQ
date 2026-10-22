"""Bounded Windows-only diagnostic; one request, no HQ writes or downloads.

Run once per already-installed model. Synthetic timing fixture, NOT research QA.
PDH hard-page-in counters are SYSTEM-wide, process faults include soft faults.
"""
import argparse
import asyncio
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import httpx


class Memory(C.Structure):
    _fields_ = [('length', C.c_ulong), ('load', C.c_ulong)] + [(k, C.c_ulonglong) for k in
        ('total', 'available', 'commit_limit', 'commit_available', 'virtual', 'virtual_available', 'extended')]


class ProcessMemory(C.Structure):
    _fields_ = [('cb', C.c_ulong), ('faults', C.c_ulong)] + [(k, C.c_size_t) for k in
        ('peak_rss', 'rss', 'peak_paged_pool', 'paged_pool', 'peak_nonpaged_pool', 'nonpaged_pool', 'commit', 'peak_commit', 'private')]


class Power(C.Structure):
    _fields_ = [(k, C.c_ubyte) for k in ('ac', 'battery_flag', 'battery_percent', 'saver')] + [(k, C.c_ulong) for k in ('life', 'full_life')]


class CounterValue(C.Structure):
    _fields_ = [('status', C.c_ulong), ('value', C.c_double)]


class Monitor:
    def __init__(self, pid):
        self.rows, self.stop = [], threading.Event()
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.restype = C.c_void_p
        self.handle = C.c_void_p(self.kernel.OpenProcess(0x410, False, pid))
        if not self.handle.value:
            raise OSError('Cannot inspect runtime PID')
        self.pdh = C.WinDLL('pdh')
        self.query = C.c_void_p()
        self.pdh.PdhOpenQueryW(None, 0, C.byref(self.query))
        self.counters = {}
        for name, path in {'system_cpu_percent': r'\Processor(_Total)\% Processor Time',
                           'page_reads_per_sec': r'\Memory\Page Reads/sec',
                           'pages_input_per_sec': r'\Memory\Pages Input/sec'}.items():
            counter = C.c_void_p()
            if self.pdh.PdhAddEnglishCounterW(self.query, C.c_wchar_p(path), 0, C.byref(counter)) == 0:
                self.counters[name] = counter
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        last = None
        while not self.stop.is_set():
            now = time.monotonic()
            m = Memory(); m.length = C.sizeof(m)
            self.kernel.GlobalMemoryStatusEx(C.byref(m))
            p = ProcessMemory(); p.cb = C.sizeof(p)
            C.WinDLL('psapi').GetProcessMemoryInfo(self.handle, C.byref(p), p.cb)
            times = [C.c_ulonglong() for _ in range(4)]
            self.kernel.GetProcessTimes(self.handle, *[C.byref(t) for t in times])
            cpu_seconds = (times[2].value + times[3].value) / 1e7
            power = Power(); self.kernel.GetSystemPowerStatus(C.byref(power))
            row = {'monotonic': now, 'available_bytes': m.available,
                   'system_committed_bytes': m.commit_limit-m.commit_available,
                   'process_rss_bytes': p.rss, 'process_private_bytes': p.private,
                   'process_faults_total': p.faults, 'ac': power.ac, 'battery_percent': power.battery_percent}
            if last:
                row['process_cpu_percent_all_logical'] = 100*(cpu_seconds-last[1])/(now-last[0])/os.cpu_count()
                row['process_faults_per_sec'] = (p.faults-last[2])/(now-last[0])
            self.pdh.PdhCollectQueryData(self.query)
            for name, counter in self.counters.items():
                val = CounterValue()
                status = self.pdh.PdhGetFormattedCounterValue(counter, 0x200, None, C.byref(val))
                if status == 0 and val.status in (0, 1):
                    row[name] = val.value
            self.rows.append(row)
            last = (now, cpu_seconds, p.faults)
            self.stop.wait(1)

    def close(self):
        self.stop.set(); self.thread.join(3)
        self.pdh.PdhCloseQuery(self.query); self.kernel.CloseHandle(self.handle)


async def request(report):
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False, timeout=120) as client:
        status = (await client.get('http://127.0.0.1:8000/api/agents/status')).json()
        if status['active_jobs'] or status['queue']:
            raise RuntimeError('ACTIVE_HQ_JOBS: do not overlap an inference')
        model = (await client.get('http://127.0.0.1:8089/v1/models')).json()['data'][0]['id']
        report['model'] = model
        context = '\n'.join(f'Fixture {n}: texto de prueba sintético, sin dato financiero. La evidencia limitada exige indicar incertidumbre.' for n in range(18))
        payload = {'model': model, 'messages': [
            {'role': 'system', 'content': 'TEST_ONLY. Resume el límite de evidencia en español en una frase. Sin herramientas ni cifras. JSON.'},
            {'role': 'user', 'content': context}], 'temperature': 0, 'seed': 17, 'max_tokens': 128,
            'stream': True, 'stream_options': {'include_usage': True},
            'chat_template_kwargs': {'enable_thinking': False}, 'reasoning_effort': 'none',
            'response_format': {'type': 'json_object', 'schema': {'type': 'object', 'properties': {
                'limitation': {'type': 'string', 'minLength': 40, 'maxLength': 180}},
                'required': ['limitation'], 'additionalProperties': False}}}
        report['payload_hash'] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        start = time.perf_counter(); report['output'] = ''
        async with client.stream('POST', 'http://127.0.0.1:8089/v1/chat/completions', json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith('data: ') or line == 'data: [DONE]':
                    continue
                item = json.loads(line[6:])
                if item.get('usage'): report['usage'] = item['usage']
                if item.get('timings'): report['server_timings'] = item['timings']
                for choice in item.get('choices', []):
                    token = choice.get('delta', {}).get('content') or ''
                    if token:
                        report.setdefault('ttft_seconds', time.perf_counter()-start)
                        report['output'] += token
                    if choice.get('finish_reason'): report['finish_reason'] = choice['finish_reason']
        report['elapsed_seconds'] = time.perf_counter()-start
        try:
            value = json.loads(report['output'])
            report['json_valid'] = isinstance(value.get('limitation'), str) and report.get('finish_reason') == 'stop'
        except ValueError:
            report['json_valid'] = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'classification': 'TEST_ONLY_TIMING_NOT_SEMANTIC_ACCEPTANCE', 'attempt_limit': 1,
              'max_output_tokens': 128, 'deadline_seconds': 120, 'logical_cpus': os.cpu_count(),
              'at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    monitor = Monitor(args.pid); monitor.thread.start(); start = time.perf_counter()
    try:
        asyncio.run(asyncio.wait_for(request(report), timeout=120))
    except Exception as exc:
        report['error'] = type(exc).__name__
    finally:
        monitor.close(); report['total_wall_seconds'] = time.perf_counter()-start
        report['samples'] = monitor.rows
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('samples', 'output')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
