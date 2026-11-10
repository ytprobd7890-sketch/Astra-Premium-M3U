import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_hourly_workflow_publishes_only_the_all_live_playlist(self):
        with (ROOT / '.github/workflows/auto-update.yml').open(encoding='utf-8') as source:
            # BaseLoader avoids YAML 1.1 interpreting the GitHub key "on" as a boolean.
            workflow = yaml.load(source, Loader=yaml.BaseLoader)
        self.assertEqual(workflow['on']['schedule'][0]['cron'], '0 * * * *')
        self.assertIn('workflow_dispatch', workflow['on'])
        self.assertEqual(workflow['permissions']['contents'], 'write')
        self.assertEqual(workflow['concurrency']['cancel-in-progress'], 'false')
        job = workflow['jobs']['check-live']
        self.assertEqual(job['timeout-minutes'], '60')
        commands = '\n'.join(step.get('run', '') for step in job['steps'])
        self.assertIn('python -m unittest discover -s tests -v', commands)
        self.assertIn('python src/main.py', commands)
        self.assertIn('git add -- playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u', commands)
        self.assertIn('git push origin "HEAD:$GITHUB_REF"', commands)
        uploads = [step for step in job['steps'] if step.get('uses', '').startswith('actions/upload-artifact@')]
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0]['with']['path'], 'playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u')
        self.assertNotIn('PREMIUM_BEST', commands)
        self.assertNotIn('by_country', commands)
        self.assertNotIn('duplicates.json', commands)

    def test_config_has_one_output(self):
        with (ROOT / 'config.yaml').open(encoding='utf-8') as source:
            config = yaml.safe_load(source)
        self.assertEqual(config['output'], {'final_checked': 'playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u'})
        self.assertNotIn('deduplicator', config)


if __name__ == '__main__':
    unittest.main()
