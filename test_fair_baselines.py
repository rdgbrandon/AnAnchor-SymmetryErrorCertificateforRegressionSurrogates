import math
import unittest
import numpy as np
from fair_baselines_audit import conformal, jackknife_candidates, jackknife_interval
from theory_rate_audit import allowance_rate


class FiniteSampleTests(unittest.TestCase):
    def test_small_calibration_abstains(self):
        for n in [3,4,8]:
            self.assertTrue(math.isinf(conformal(np.arange(n))))
        self.assertEqual(conformal(np.arange(9)),8.)

    def test_jackknife_threshold(self):
        self.assertEqual(jackknife_interval(list(range(18)),list(range(18))),(0.,math.inf))
        self.assertEqual(jackknife_interval(list(range(19)),list(range(19))),(0.,18.))

    def test_exact_linear_error_uses_test_predictions(self):
        x=np.array([0.,1.,2.,3.]); errors=2*x+1
        lo,hi=jackknife_candidates(x,errors,5.)
        np.testing.assert_allclose(lo,11.,atol=1e-12)
        np.testing.assert_allclose(hi,11.,atol=1e-12)
        lo2,hi2=jackknife_candidates(x,errors,6.)
        np.testing.assert_allclose(lo2,13.,atol=1e-12)
        np.testing.assert_allclose(hi2,13.,atol=1e-12)

    def test_order_invariance(self):
        x=np.array([0.,.4,1.3,2.]);e=np.array([1.,5.,2.,3.]);p=[2,0,3,1]
        lo,hi=jackknife_candidates(x,e,3.)
        lp,hp=jackknife_candidates(x[p],e[p],3.)
        np.testing.assert_allclose(np.sort(lo),np.sort(lp))
        np.testing.assert_allclose(np.sort(hi),np.sort(hp))

    def test_no_fake_nonempty_interval(self):
        self.assertEqual(jackknife_interval([-3.]*19,[-1.]*19),(0.,-1.))

    def test_conditional_integral_bound(self):
        q=np.array([.3,1.,-.2]);gamma=(.6,1.4);eta=.2;d=2.
        rate=allowance_rate(q,gamma,eta)
        # Explicit smooth correction r(u) with derivative norm <= eta.
        direction=np.array([1.,2.,3.]);direction/=np.linalg.norm(direction)
        u=np.linspace(0,d,10001)
        deriv=(1+.4*np.sin(u))[:,None]*.5+eta*np.cos(u)[:,None]*direction
        y=np.trapz(deriv,u,axis=0)
        self.assertLessEqual(np.linalg.norm(y-q*d),rate*d+1e-12)

    def test_shape_projects_out_flux(self):
        q=np.array([1.,-1.,0.])
        self.assertAlmostEqual(allowance_rate(q,(1.,1.),0.,shape=True),np.linalg.norm(q))
        self.assertGreater(allowance_rate(q,(1.,1.),0.),np.linalg.norm(q))
        with self.assertRaises(ValueError): allowance_rate(q,(2.,1.),0.)


if __name__=='__main__':unittest.main()
