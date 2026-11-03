#!/usr/bin/env python3
"""Real mouse polygon/Z selection; independent Matplotlib membership and full-record checks."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from matplotlib.path import Path as PolygonPath
from ui_region import RegionDriver, source_arrays
from ui_smoke import layer, pcd_parts, sha256


class PolygonDriver(RegionDriver):
    def point(self, position):
        self.move_to(*position)
        self.xtst.XTestFakeButtonEvent(self.display, 1, True, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.05)
        self.xtst.XTestFakeButtonEvent(self.display, 1, False, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.15)

    def drag(self, start, end):
        self.move_to(*start)
        self.xtst.XTestFakeButtonEvent(self.display, 1, True, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.08)
        for amount in np.linspace(0.2, 1.0, 5):
            self.move_to(*(np.array(start) * (1 - amount) + np.array(end) * amount))
        self.xtst.XTestFakeButtonEvent(self.display, 1, False, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.3)


def mask_for(xyz, state):
    vertices = np.array(state['region']['picks'])[:, :2]
    polygon = PolygonPath(np.vstack([vertices, vertices[0]]), closed=True)
    mask = polygon.contains_points(xyz[:, :2])
    ranges = np.array(state['ranges'])
    return mask & np.all((xyz >= ranges[:, 0]) & (xyz <= ranges[:, 1]), axis=1)


def run(args):
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / 'state.json'
    state_path.unlink(missing_ok=True)
    source = args.pcd.resolve(strict=True)
    before = sha256(source)
    header, payload = pcd_parts(source)
    xyz, records = source_arrays(header, payload)
    report = {'passed': False, 'source': str(source), 'source_sha256_before': before,
              'points': len(xyz), 'reference': 'matplotlib.path.Path.contains_points', 'steps': []}
    process = driver = None
    started = time.monotonic()
    def record(message):
        report['steps'].append(message)
        print(message, flush=True)
    try:
        with (output / 'gui.log').open('w') as log:
            process = subprocess.Popen([str(args.binary.resolve()), str(source)],
                env=dict(os.environ, TAFFY_UI_STATE=str(state_path), WINIT_UNIX_BACKEND='x11'),
                stdout=log, stderr=subprocess.STDOUT)
            driver = PolygonDriver(state_path)
            state = driver.wait(lambda s: len(s.get('layers', [])) == 1 and not s['busy'], 'load', 60)
            assert state['region']['polygon']
            driver.find_window(process.pid)
            source_id = state['selected_layer_id']
            driver.click('region_start')
            rect = driver.state()['widgets']['viewport']
            def screen(fx, fy):
                return (rect[0] + rect[2]*fx, rect[1] + rect[3]*fy)
            # A crossed polygon must not produce a delete-ready preview.
            for i, xy in enumerate([(0.3,0.4),(0.7,0.6),(0.3,0.6),(0.7,0.4)]):
                driver.point(screen(*xy))
                driver.wait(lambda s: len(s['region']['picks']) == i+1, 'bowtie vertex')
            driver.click('region_calculate')
            state=driver.wait(lambda s: not s['busy'] and s.get('error'), 'reject self intersection')
            assert state['region']['count'] is None and state['region']['highlight_points']==0
            assert len(state['layers']) == 1
            driver.click('error_close')
            driver.click('region_clear')
            record('Self-intersecting contour rejected without changing the cloud')
            driver.click('region_start')
            driver.fill_number('region_z_min','0.15')
            driver.fill_number('region_z_max','1.2')
            state=driver.wait(lambda s: abs(s['ranges'][2][0]-.15)<1e-5 and abs(s['ranges'][2][1]-1.2)<1e-5,'Z inputs')
            vertices=[(0.1,0.2),(0.8,0.2),(0.8,0.47),(0.5,0.47),(0.5,0.8),(0.1,0.8)]
            for i, xy in enumerate(vertices):
                driver.point(screen(*xy))
                driver.wait(lambda s: len(s['region']['picks']) == i+1, 'free polygon vertex')
            driver.click('region_undo_pick')
            driver.wait(lambda s: len(s['region']['picks']) == 5, 'undo vertex')
            driver.point(screen(*vertices[-1]))
            state=driver.wait(lambda s: len(s['region']['picks']) == 6, 'restore vertex')
            picks=state['region']['picks']
            assert any(not np.any(np.all(xyz[:, :2] == np.array(p)[:2], axis=1)) for p in picks)
            camera_before=state['projected_candidates']
            driver.drag(screen(.45,.45),screen(.55,.5))
            state=driver.state()
            assert state['region']['picks']==picks
            assert state['projected_candidates']==camera_before, 'Drawing camera moved'
            record('Free vertices, undo and concave contour work; camera stays locked while drawing')
            driver.click('region_calculate')
            state=driver.wait(lambda s: s['region']['count'] is not None and not s['busy'], 'preview',60)
            assert not state.get('error')
            expected=mask_for(xyz,state)
            count=int(expected.sum())
            assert 0<count<len(xyz)
            assert state['region']['count']==count, (state['region']['count'],count)
            assert state['region']['highlight_points']==count
            driver.screenshot(output/'01-polygon-preview.png')
            driver.drag(screen(.45,.45),screen(.55,.5))
            state=driver.state()
            assert state['region']['picks']==picks and state['region']['count']==count
            assert state['projected_candidates']!=camera_before, 'Closed preview cannot rotate'
            driver.screenshot(output/'02-side-inspection.png')
            record('Concave polygon and Z selection match Matplotlib; rotating preserves selection')
            driver.fill_number('region_z_max','0.5')
            state=driver.wait(lambda s: s['region']['count'] is None,'height invalidation')
            assert state['region']['highlight_points']==0
            assert state['region']['picks']==picks
            driver.click('region_calculate')
            state=driver.wait(lambda s: s['region']['count'] is not None and not s['busy'],'recompute',60)
            expected=mask_for(xyz,state)
            final_count=int(expected.sum())
            assert state['region']['count']==final_count and final_count<count
            record('Changing Z clears stale highlight and recomputes a smaller volume')
            report.update(deleted_points=final_count, initial_preview_points=count,
                          polygon_xy=np.array(picks)[:, :2].tolist(), z_range=state['ranges'][2])
            driver.click('region_delete')
            state=driver.wait(lambda s: len(s['layers'])==2 and not s['busy'],'delete',60)
            assert layer(state,source_id)['points']==len(xyz) and not layer(state,source_id)['visible']
            assert layer(state,state['selected_layer_id'])['points']==len(xyz)-final_count
            exported=output/'polygon-deleted.pcd'
            exported.unlink(missing_ok=True)
            driver.modal('export',exported)
            driver.wait(lambda s: exported.exists() and not s['busy'],'export',60)
            actual_header, actual_payload=pcd_parts(exported)
            for key in ('FIELDS','SIZE','TYPE','COUNT','VIEWPOINT'):
                assert actual_header[key]==header[key],key
            assert actual_payload==records[~expected].tobytes(), 'Survivors/extra fields differ'
            report['survivors']=len(xyz)-final_count
            report['fields']=actual_header['FIELDS']
            driver.screenshot(output/'03-polygon-deleted.png')
            record('Deleted survivors and normals exported byte-for-byte; original layer retained')
            driver.click('region_convex_mode')
            assert not driver.state()['region']['polygon']
            driver.click('region_polygon_mode')
            assert driver.state()['region']['polygon']
            assert not driver.state()['region']['picks']
            driver.chord('Alt_L','F4')
            assert process.wait(timeout=10)==0
            report['source_sha256_after']=sha256(source)
            assert report['source_sha256_after']==before
            report['passed']=True
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if driver: driver.close()
        report['seconds']=round(time.monotonic()-started,3)
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,default=Path(__file__).resolve().parents[1]/'taffy-pcd-editor')
    parser.add_argument('--pcd',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('/tmp/taffy-polygon-check'))
    print(json.dumps(run(parser.parse_args()),ensure_ascii=False,indent=2))
