"""Regression checks for scheduling input, catalogue coverage and bundle packaging."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
import crear_entrega as producer

class ProductionContractTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((producer.HERE/'catalogo.json').read_text())
        self.start=dt.datetime(2026,10,27,tzinfo=dt.timezone.utc)

    def test_six_slots_cover_the_curated_programmes(self):
        plans=[producer.selection(self.start+dt.timedelta(hours=4*i),self.catalog) for i in range(6)]
        self.assertEqual(len({p['id'] for p in plans}),6)
        self.assertEqual({tuple(p['works']) for p in plans},{(1,2),(1,3),(2,1),(2,3),(3,1),(3,2)})
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

    def test_retries_are_deterministic_but_next_day_is_new(self):
        a=producer.selection(self.start,self.catalog)
        self.assertEqual(a,producer.selection(self.start,self.catalog))
        b=producer.selection(self.start+dt.timedelta(days=1),self.catalog)
        self.assertEqual(a['id'],b['id'])
        self.assertNotEqual(a['seed'],b['seed'])

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

if __name__=='__main__':
    unittest.main()
