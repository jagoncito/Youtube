"""Regression checks for scheduling input, catalogue coverage and bundle packaging."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
import crear_entrega as producer


def artwork(label,compression=6):
    """Deterministic textured PNG, encoded with only the standard library."""
    import struct,zlib
    label=label.encode() if isinstance(label,str) else label
    cells={(x,y):hashlib.sha256(label+f':{x}:{y}'.encode()).digest()[:3]
           for y in range(8) for x in range(12)}
    raw=b''.join(b'\0'+b''.join(cells[x//8,y//8] for x in range(96)) for y in range(64))
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,64,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(raw,compression))+chunk(b'IEND',b''))

class ProductionContractTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((producer.HERE/'catalogo.json').read_text())
        self.start=dt.datetime(2026,10,27,tzinfo=dt.timezone.utc)

    def test_rotation_is_only_a_preference_and_does_not_prove_novelty(self):
        plans=[producer.selection(self.start+dt.timedelta(hours=4*i),self.catalog) for i in range(6)]
        self.assertEqual(len({p['id'] for p in plans}),6)
        self.assertEqual({tuple(p['works']) for p in plans},{(1,2),(1,3),(2,1),(2,3),(3,1),(3,2)})
        self.assertEqual(len({tuple(sorted(set(p['works']))) for p in plans}),3)
        self.assertTrue(all(sum(p['work_seconds'])==360 for p in plans))

    def test_scene_families_differ_in_substantive_story_axes(self):
        scenes={p['scene']['id']:p['scene'] for p in self.catalog['plans']}
        self.assertEqual(set(scenes),{'atelier','boathouse','rainy-room-002'})
        self.assertTrue(all(sum(p['scene']['id']==key for p in self.catalog['plans'])==2 for key in scenes))
        values=list(scenes.values())
        self.assertEqual(len({s['image'] for s in values}),3)
        for i,a in enumerate(values):
            self.assertEqual(len(a['axes']),5)
            for b in values[i+1:]:
                differences=sum(a['axes'][key]!=b['axes'][key] for key in a['axes'])
                self.assertGreaterEqual(differences,3)

    def test_new_scene_copy_does_not_claim_unimplemented_animal_motion(self):
        for plan in self.catalog['plans']:
            scene=plan['scene']
            if scene['id']=='rainy-room-002':
                continue
            with self.subTest(scene=scene['id']),tempfile.TemporaryDirectory() as td:
                audio={'chapters':[{'number':plan['works'][0],'start_seconds':0},
                                   {'number':plan['works'][1],'start_seconds':180}]}
                selected=producer.selection(self.start,self.catalog,plan['id'])
                description=producer.documents(Path(td),selected,audio,scene,self.catalog)
                self.assertIn(scene['description'],description)
                self.assertIn(scene['animation'],description)
                self.assertNotIn('firelight',description)
                self.assertNotIn('breathing',description)

    def test_curated_scene_assets_match_their_reviewed_manifests(self):
        scenes={p['scene']['id']:p['scene'] for p in self.catalog['plans']}
        for scene in scenes.values():
            with self.subTest(scene=scene['id']):
                template=producer.repository_asset(scene['scene_template']) if scene.get('scene_template') else None
                producer.validate_scene(scene,template)

    def test_scene_gate_still_rejects_the_measured_geometric_bug(self):
        import copy
        from crear_templates import assess_report
        base={'encoded_wrap_mae':.00672,'normal_step_p95_mae':.00172,
              'encoded_wrap_p99_8bit':0,'source_raw':{'periodic_pass':True},
              'active_rois':[{'wrap_mae':.1707,'normal_p95_mae':.0427}]}
        self.assertTrue(assess_report(copy.deepcopy(base))['seam_pass'])
        broken=copy.deepcopy(base)
        broken['encoded_wrap_mae']=.4
        broken['active_rois'][0]['wrap_mae']=10.62
        self.assertFalse(assess_report(broken)['seam_pass'])
        broken_source=copy.deepcopy(base)
        broken_source['source_raw']['periodic_pass']=False
        self.assertFalse(assess_report(broken_source)['seam_pass'])

    def test_seed_changes_do_not_change_the_musical_programme(self):
        a=producer.selection(self.start,self.catalog)
        self.assertEqual(a,producer.selection(self.start,self.catalog))
        b=producer.selection(self.start+dt.timedelta(days=1),self.catalog)
        self.assertEqual(a['id'],b['id'])
        self.assertNotEqual(a['seed'],b['seed'])
        self.assertEqual(sorted(a['works']),sorted(b['works']))

    def test_misaligned_and_ambiguous_slots_are_rejected(self):
        for value in ['2026-10-27T13:00:00Z','2026-10-27T12:01:00Z','2026-10-27T12:00:00']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                producer.utc_slot(value)

    def test_catalogue_cannot_copy_files_outside_the_checkout(self):
        with self.assertRaises(ValueError):
            producer.repository_asset('../../etc/passwd')

    def test_score_integrity(self):
        producer.verify_sources()

    def test_publication_bundle_contains_the_actual_sources(self):
        plan=producer.selection(producer.utc_slot('2026-10-27T12:00:00Z'),self.catalog,'reading-21')
        audio={'chapters':[{'number':2,'start_seconds':0},{'number':1,'start_seconds':174}]}
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            description=producer.documents(folder,plan,audio,self.catalog['scene'],self.catalog)
            for name in ['gymnopedie-2.ly','gymnopedie-2.midi','gymnopedie-1.ly','gymnopedie-1.midi','VSCO-CC0-LICENSE.txt','fuentes.json','instrumento-vsco-fuentes.json']:
                self.assertTrue((folder/'fuentes'/name).is_file(),name)
            self.assertIn('02:54 Gymnopédie No. 1',description)
            self.assertIn('06:00 Gymnopédie No. 2',description)
            self.assertIn('Gymnopédie No. 2',description)
            self.assertIn('https://github.com/MutopiaProject',description)
            self.assertLess(len(description),5000)

class NoveltyGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.catalog=json.loads((producer.HERE/'catalogo.json').read_text())
        self.slot=producer.utc_slot('2026-10-28T00:00:00Z')
        self.scenes={p['scene']['id']:p['scene'] for p in self.catalog['plans']}
        for scene in self.scenes.values():
            path=self.root/scene['image']
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(artwork(scene['id']))
        self.record(1,'rainy-room-002',[1,3])
        self.record(2,'rainy-room-002',[1,2])
        self.record(3,'atelier',[2,1])

    def write_json(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data))

    def record(self,number,scene_id,works,tag=None,status='success'):
        scene=self.scenes[scene_id]
        image=(self.root/scene['image']).read_bytes()
        folder=self.root/'videos'/f'{number:03d}'
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'imagen.png').write_bytes(image)
        identity=dict(scene_sha256=hashlib.sha256(image).hexdigest(),scene_id=scene_id,program=sorted(set(works)))
        manifest=dict(scene_id=scene_id,files={'imagen.png':{'sha256':identity['scene_sha256']}},
                      audio={'chapters':[{'number':n} for n in works]})
        if tag:
            manifest.update(slot='2026-10-28T00:00:00Z',tag=tag)
        self.write_json(folder/'manifest.json',manifest)
        record=dict(number=number,folder=f'videos/{number:03d}',status=status)
        if tag:
            record.update(tag=tag,slot=manifest['slot'],creative_identity=identity)
        self.write_json(self.root/'automatizacion/entregas'/f'{number:03d}.json',record)
        return identity

    def test_three_real_deliveries_leave_only_boathouse_with_works_two_three(self):
        result=producer.select_new_plan(self.slot,self.catalog,self.root)
        self.assertEqual(result['id'],'quiet-break-23')
        self.assertEqual(result['creative_identity']['program'],[2,3])
        self.assertEqual(result['creative_identity']['scene_id'],'boathouse')
        self.assertEqual(len(producer.historical_identities(self.root,self.catalog)),3)

    def test_both_scene_and_programme_must_be_unpublished(self):
        for plan_id in ['reading-13','focus-31','wind-down-12','reading-21','wind-down-32']:
            with self.subTest(plan=plan_id),self.assertRaises(producer.NeedsNewAssets):
                producer.select_new_plan(self.slot,self.catalog,self.root,plan_id=plan_id)

    def test_different_seed_and_reordered_same_works_are_rejected(self):
        for offset in [0,4,24,48]:
            with self.subTest(hours=offset),self.assertRaises(producer.NeedsNewAssets):
                producer.select_new_plan(self.slot+dt.timedelta(hours=offset),self.catalog,self.root,plan_id='focus-31')

    def test_bank_exhaustion_never_reuses_an_asset(self):
        self.record(4,'boathouse',[2,3])
        for offset in [0,4,24]:
            with self.subTest(hours=offset),self.assertRaises(producer.NeedsNewAssets):
                producer.select_new_plan(self.slot+dt.timedelta(hours=offset),self.catalog,self.root)

    def test_same_image_under_another_scene_id_is_still_used(self):
        boat=self.root/self.scenes['boathouse']['image']
        boat.write_bytes((self.root/self.scenes['rainy-room-002']['image']).read_bytes())
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_same_pixels_with_new_encoding_and_scene_id_are_rejected(self):
        image=self.root/self.scenes['boathouse']['image']
        original=(self.root/self.scenes['rainy-room-002']['image']).read_bytes()
        image.write_bytes(artwork('rainy-room-002',compression=1))
        self.assertNotEqual(hashlib.sha256(original).hexdigest(),producer.digest(image))
        self.assertNotEqual(self.scenes['boathouse']['id'],self.scenes['rainy-room-002']['id'])
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_jpeg_roundtrip_of_old_art_is_rejected_under_new_scene_id(self):
        original=self.root/self.scenes['rainy-room-002']['image']
        jpeg=self.root/'reencoded.jpg'
        candidate=self.root/self.scenes['boathouse']['image']
        subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-i',str(original),
                        '-frames:v','1','-q:v','3',str(jpeg)],check=True,capture_output=True)
        subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-i',str(jpeg),
                        '-frames:v','1','-y',str(candidate)],check=True,capture_output=True)
        self.assertNotEqual(producer.digest(original),producer.digest(candidate))
        self.assertTrue(producer.near_duplicate_image(producer.image_fingerprint(original),
                                                       producer.image_fingerprint(candidate)))
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_unindexed_reencoded_image_also_blocks_near_copy(self):
        folder=self.root/'videos/099';folder.mkdir()
        historical=folder/'imagen.png'
        historical.write_bytes(artwork('boathouse',compression=1))
        candidate=self.root/self.scenes['boathouse']['image']
        self.assertNotEqual(producer.digest(historical),producer.digest(candidate))
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_different_textured_scene_passes_the_similarity_guard(self):
        boat=producer.image_fingerprint(self.root/self.scenes['boathouse']['image'])
        for scene_id in ['rainy-room-002','atelier']:
            old=producer.image_fingerprint(self.root/self.scenes[scene_id]['image'])
            self.assertFalse(producer.near_duplicate_image(boat,old))
        self.assertEqual(producer.select_new_plan(self.slot,self.catalog,self.root)['id'],'quiet-break-23')

    def test_flat_colours_do_not_collide_as_zero_hashes(self):
        fingerprints=[]
        for colour in ['red','blue']:
            image=self.root/f'{colour}.png'
            subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-f','lavfi',
                '-i',f'color=c={colour}:s=96x64','-frames:v','1',str(image)],
                check=True,capture_output=True)
            fingerprints.append(producer.image_fingerprint(image))
        self.assertFalse(producer.near_duplicate_image(*fingerprints))
        self.assertTrue(producer.near_duplicate_image(fingerprints[0],fingerprints[0]))

    def test_changed_checksum_does_not_make_same_scene_new(self):
        plan=next(p for p in self.catalog['plans'] if p['id']=='quiet-break-23')
        plan['scene']=dict(plan['scene'],id='atelier')
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_unindexed_local_video_image_also_blocks_reuse(self):
        folder=self.root/'videos/099';folder.mkdir()
        (folder/'imagen.png').write_bytes((self.root/self.scenes['boathouse']['image']).read_bytes())
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_index_history_still_blocks_when_media_folder_is_removed(self):
        for number,scene_id,works in [(1,'rainy-room-002',[1,3]),(2,'rainy-room-002',[1,2]),(3,'atelier',[1,2])]:
            folder=self.root/'videos'/f'{number:03d}'
            manifest=json.loads((folder/'manifest.json').read_text())
            record_path=self.root/'automatizacion/entregas'/f'{number:03d}.json'
            record=json.loads(record_path.read_text());record['manifest']=manifest
            self.write_json(record_path,record)
            import shutil
            shutil.rmtree(folder)
        self.assertEqual(producer.select_new_plan(self.slot,self.catalog,self.root)['id'],'quiet-break-23')

    def test_published_history_without_evidence_blocks_planning(self):
        self.write_json(self.root/'automatizacion/entregas/unknown.json',{'number':9,'status':'success'})
        with self.assertRaisesRegex(producer.NeedsNewAssets,'history lacks'):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_historical_programme_identity_cannot_override_real_chapters(self):
        path=self.root/'videos/001/manifest.json'
        manifest=json.loads(path.read_text())
        manifest['creative_identity']={'program':[2,3]}
        self.write_json(path,manifest)
        with self.assertRaisesRegex(ValueError,'musical works'):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_historical_checksum_disagreement_blocks_planning(self):
        (self.root/'videos/001/imagen.png').write_bytes(b'Changed historical image')
        with self.assertRaisesRegex(ValueError,'disagrees'):
            producer.select_new_plan(self.slot,self.catalog,self.root)

    def test_pending_retry_excludes_only_its_exact_reservation(self):
        tag='jagoncito-20261028-0000Z'
        self.record(4,'boathouse',[2,3],tag=tag,status='pending')
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root)
        result=producer.select_new_plan(self.slot,self.catalog,self.root,exclude_tag=tag)
        self.assertEqual(result['id'],'quiet-break-23')
        self.assertEqual(len(producer.historical_identities(self.root,self.catalog,exclude_tag=tag)),3)

    def test_retry_flag_cannot_exclude_an_already_successful_delivery(self):
        tag='jagoncito-20261028-0000Z'
        self.record(4,'boathouse',[2,3],tag=tag,status='success')
        with self.assertRaises(producer.NeedsNewAssets):
            producer.select_new_plan(self.slot,self.catalog,self.root,exclude_tag=tag)

    def test_git_lfs_pointer_is_not_reviewed_artwork(self):
        (self.root/self.scenes['boathouse']['image']).write_text('version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 100\n')
        with self.assertRaisesRegex(ValueError,'real scene image'):
            producer.select_new_plan(self.slot,self.catalog,self.root,plan_id='quiet-break-23')


if __name__=='__main__':
    unittest.main()
