import unittest
from src.ai.anomaly import evaluate,triage,make_fixture

class IA2GTests(unittest.TestCase):
    def test_train_does_not_contain_attack_labels(self):
        train,test,labels=make_fixture()
        self.assertEqual(len(train),600)
        self.assertEqual((labels==1).sum(),80)
        self.assertEqual((labels==0).sum(),160)
    def test_deterministic_metrics(self):
        a=evaluate();b=evaluate()
        self.assertEqual(a,b)
        self.assertEqual(sum(a['confusion_matrix'].values()),240)
    def test_no_automatic_action(self):
        a=evaluate();d=triage(a)
        self.assertEqual(a['actions_executed'],0)
        self.assertFalse(d['approved'])
        self.assertFalse(d['executed'])
        self.assertTrue(a['human_approval_required'])
    def test_metrics_are_bounded(self):
        a=evaluate()
        for k in ('accuracy','precision','recall','f1'):
            self.assertGreaterEqual(a[k],0);self.assertLessEqual(a[k],1)
