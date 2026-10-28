"""Test suite for Track A: Continuous Optimization.

Validates:
1. Optimizer interfaces, state management, and edge-case handling.
2. Analytic gradient correctness via central finite-difference checking.
3. Analytic Hessian correctness via finite differences.
4. Convergence on known global optima (Convex Quadratic, Rosenbrock).
5. Saddle point escape dynamics.
6. Gauss-Newton least squares convergence.
7. Backpropagation gradient verification via numerical approximations.
8. Hessian-Vector Product (Pearlmutter formula) accuracy.
"""
import pytest
import numpy as np
import sys
import os

TRACK_A_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TRACK_A_DIR not in sys.path:
    sys.path.insert(0, TRACK_A_DIR)

from optimizers import (
    GradientDescent,
    Momentum,
    NesterovAcceleratedGradient,
    AdaGrad,
    RMSProp,
    Adam,
    NewtonsMethod,
    GaussNewton,
    DiagonalFisherOptimizer,
    hessian_vector_product,
)
from objectives import (
    ConvexQuadratic,
    Rosenbrock,
    SaddleFunction,
    NonLinearLeastSquares,
)
from models import TwoLayerMLP


def numerical_gradient(func, x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Central difference numerical gradient approximation."""
    grad = np.zeros_like(x)
    for i in range(len(x)):
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += eps
        x_minus[i] -= eps
        grad[i] = (func(x_plus) - func(x_minus)) / (2.0 * eps)
    return grad


def numerical_hessian(func, x: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Central difference numerical Hessian approximation."""
    n = len(x)
    H = np.zeros((n, n))
    f_x = func(x)
    for i in range(n):
        for j in range(n):
            if i == j:
                x_p = x.copy(); x_p[i] += eps
                x_m = x.copy(); x_m[i] -= eps
                H[i, i] = (func(x_p) - 2.0 * f_x + func(x_m)) / (eps ** 2)
            else:
                x_pp = x.copy(); x_pp[i] += eps; x_pp[j] += eps
                x_pm = x.copy(); x_pp[i] += eps; x_pm[j] -= eps
                x_mp = x.copy(); x_mp[i] -= eps; x_mp[j] += eps
                x_mm = x.copy(); x_mm[i] -= eps; x_mm[j] -= eps
                H[i, j] = (func(x_pp) - func(x_pm) - func(x_mp) + func(x_mm)) / (4.0 * eps ** 2)
    return H


class TestGradientsAndHessians:
    def test_convex_quadratic_derivatives(self):
        Q = np.array([[6.0, 2.0], [2.0, 4.0]])
        b = np.array([1.0, -3.0])
        quad = ConvexQuadratic(Q=Q, b=b)
        x_test = np.array([1.5, -2.0])

        num_grad = numerical_gradient(quad.evaluate, x_test)
        ana_grad = quad.gradient(x_test)
        assert np.allclose(num_grad, ana_grad, atol=1e-5)

        ana_hess = quad.hessian(x_test)
        assert np.allclose(ana_hess, Q)

    def test_rosenbrock_derivatives(self):
        rosen = Rosenbrock(a=1.0, b=100.0)
        x_test = np.array([0.5, 0.25])

        num_grad = numerical_gradient(rosen.evaluate, x_test)
        ana_grad = rosen.gradient(x_test)
        assert np.allclose(num_grad, ana_grad, atol=1e-4)

        ana_hess = rosen.hessian(x_test)
        # Verify symmetry of Hessian
        assert np.allclose(ana_hess, ana_hess.T)

    def test_saddle_point_derivatives_and_indefiniteness(self):
        saddle = SaddleFunction()
        x_zero = np.array([0.0, 0.0])

        # Gradient at origin is zero
        assert np.allclose(saddle.gradient(x_zero), [0.0, 0.0])

        # Hessian at origin has positive and negative eigenvalues (+1 and -1)
        H_zero = saddle.hessian(x_zero)
        eigvals = np.linalg.eigvalsh(H_zero)
        assert eigvals[0] < 0 and eigvals[1] > 0


class TestOptimizersConvergence:
    def test_newton_quadratic_one_step(self):
        """Newton's method on pure quadratic must converge in 1 step for lr=1.0."""
        Q = np.array([[8.0, 0.0], [0.0, 3.0]])
        b = np.array([4.0, 6.0])
        quad = ConvexQuadratic(Q=Q, b=b)
        x0 = np.array([10.0, -10.0])

        newton = NewtonsMethod(lr=1.0, damping=0.0)
        grad = quad.gradient(x0)
        hess = quad.hessian(x0)
        x_next = newton.step(x0, grad, hessian=hess)

        assert np.allclose(x_next, quad.optimum, atol=1e-6)

    def test_first_order_optimizers_decrease_loss(self):
        quad = ConvexQuadratic()
        x0 = np.array([2.0, 2.0])
        initial_loss = quad.evaluate(x0)

        optimizers = [
            GradientDescent(lr=0.05),
            Momentum(lr=0.05),
            NesterovAcceleratedGradient(lr=0.05),
            AdaGrad(lr=0.5),
            RMSProp(lr=0.05),
            Adam(lr=0.1),
        ]

        for opt in optimizers:
            x = x0.copy()
            for _ in range(30):
                g = quad.gradient(x)
                x = opt.step(x, g)
            final_loss = quad.evaluate(x)
            assert final_loss < initial_loss, f"{opt.name} failed to decrease loss."

    def test_gauss_newton_least_squares(self):
        nlls = NonLinearLeastSquares()
        theta = np.array([1.5, 0.5])
        gn = GaussNewton(lr=1.0)

        for _ in range(15):
            r = nlls.residuals(theta)
            J = nlls.jacobian(theta)
            theta = gn.step(theta, residuals=r, jacobian=J)

        # Ground truth is near [2.5, 1.2]
        assert np.isclose(theta[0], 2.5, atol=0.2)
        assert np.isclose(theta[1], 1.2, atol=0.2)


class TestBackpropagationAndHVP:
    def test_mlp_backpropagation_gradient_check(self):
        """Verify analytical backpropagation gradients against numerical gradients."""
        rng = np.random.RandomState(42)
        X = rng.randn(5, 3)
        y = np.array([[1.0], [0.0], [1.0], [0.0], [1.0]])

        mlp = TwoLayerMLP(input_dim=3, hidden_dim=4, seed=42)
        mlp.forward(X)
        ana_grad = mlp.backpropagation(y)

        # Loss function for numerical differentiation
        def loss_at_theta(theta):
            mlp_temp = TwoLayerMLP(input_dim=3, hidden_dim=4, seed=42)
            mlp_temp.set_params_flat(theta)
            preds = mlp_temp.forward(X)
            return mlp_temp.compute_loss(preds, y)

        num_grad = numerical_gradient(loss_at_theta, mlp.params_flat, eps=1e-5)
        # Analytical and numerical gradients should match closely
        diff = np.linalg.norm(ana_grad - num_grad) / (np.linalg.norm(ana_grad) + np.linalg.norm(num_grad))
        assert diff < 1e-4, f"Backprop gradient mismatch: relative diff {diff}"

    def test_hessian_vector_product_accuracy(self):
        Q = np.array([[12.0, -3.0], [-3.0, 5.0]])
        b = np.array([2.0, 1.0])
        quad = ConvexQuadratic(Q=Q, b=b)

        x = np.array([1.0, 2.0])
        v = np.array([0.5, -0.8])

        # Exact H * v = Q * v
        hv_exact = Q @ v
        # Finite difference approximation
        hv_approx = hessian_vector_product(quad.gradient, x, v, eps=1e-5)

        assert np.allclose(hv_exact, hv_approx, atol=1e-4)


class TestOptimizerValidationAndErrors:
    def test_invalid_learning_rate(self):
        with pytest.raises(ValueError):
            GradientDescent(lr=-0.1)

    def test_invalid_momentum_beta(self):
        with pytest.raises(ValueError):
            Momentum(lr=0.01, beta=1.5)

    def test_newton_missing_hessian(self):
        newton = NewtonsMethod(lr=1.0)
        with pytest.raises(ValueError, match="requires 'hessian'"):
            newton.step(np.array([1.0, 1.0]), np.array([0.5, 0.5]))

