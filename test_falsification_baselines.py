import unittest
import numpy as np
from falsification_audit import lipschitz_box, box_distance, synthetic
from projection_baseline_audit import dual_distance
from stress_test_certificate import capsule_distance


class BaselineChecks(unittest.TestCase):
    def test_single_ball_projection(self):
        result=dual_distance(np.array([0.]),np.array([[3.]]),np.array([2.]))
        self.assertAlmostEqual(result['lower'],1.,places=7)

    def test_intersection_projection(self):
        result=dual_distance(np.array([5.]),np.array([[0.],[2.]]),np.array([2.,2.]))
        self.assertAlmostEqual(result['lower'],3.,places=7)

    def test_inside_intersection(self):
        result=dual_distance(np.array([1.]),np.array([[0.],[2.]]),np.array([2.,2.]))
        self.assertEqual(result['lower'],0.)

    def test_classical_envelope(self):
        lo,hi,L=lipschitz_box(np.array([0.,1.]),np.array([[0.],[1.]]),2.,0.)
        np.testing.assert_allclose([lo[0],hi[0],L[0]],[0.,2.,1.])
        self.assertEqual(box_distance(np.array([3.]),lo,hi),1.)

    def test_smooth_and_noise_counterexamples(self):
        # These are counterexamples to unconditional claims, not to the
        # conditional theorem. Empty-set behavior is recorded by the audit.
        cases=synthetic()
        self.assertEqual(cases['smooth_escape']['score'],6.)
        self.assertEqual(cases['smooth_escape']['error'],0.)
        self.assertGreater(cases['anchor_bias']['score'],.199999)

    def test_capsule_projection(self):
        a=np.array([0.,0.]);b=np.array([2.,0.])
        self.assertAlmostEqual(capsule_distance(np.array([1.,3.]),a,b,1.),2.)
        self.assertAlmostEqual(capsule_distance(np.array([5.,4.]),a,b,1.),4.)
        self.assertEqual(capsule_distance(np.array([1.,.5]),a,b,1.),0.)

    def test_capsule_degenerate_segment(self):
        a=np.array([0.,0.])
        self.assertAlmostEqual(capsule_distance(np.array([3.,4.]),a,a,2.),3.)


if __name__=='__main__':unittest.main()
