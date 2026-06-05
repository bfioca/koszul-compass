"""Numerical slope-zero feasibility checks for favourable CICY line bundles."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np


@dataclass
class SlopeSearchResult:
    feasible: bool
    max_abs_slope: float
    max_normalized_slope: float
    mean_square_slope: float
    normalized_mean_square_slope: float
    kahler_point: list[float]
    kappa: list[float]
    slopes: list[float]
    iterations: int
    restarts: int
    seed: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "feasible": self.feasible,
            "max_abs_slope": self.max_abs_slope,
            "max_normalized_slope": self.max_normalized_slope,
            "mean_square_slope": self.mean_square_slope,
            "normalized_mean_square_slope": self.normalized_mean_square_slope,
            "kahler_point": self.kahler_point,
            "kappa": self.kappa,
            "slopes": self.slopes,
            "iterations": self.iterations,
            "restarts": self.restarts,
            "seed": self.seed,
        }


def intersection_tensor(d: dict[tuple[int, int, int], int], h11: int) -> np.ndarray:
    tensor = np.zeros((h11, h11, h11), dtype=float)
    for (i, j, k), value in d.items():
        tensor[i, j, k] = value
    return tensor


def softmax(x: np.ndarray) -> np.ndarray:
    y = np.exp(x - np.max(x))
    return y / y.sum()


def slopes_at(matrix: list[list[int]], tensor: np.ndarray, kahler_point: np.ndarray) -> np.ndarray:
    charges = np.asarray(matrix, dtype=float)
    kappa = np.einsum("ijk,j,k->i", tensor, kahler_point, kahler_point)
    return charges.T @ kappa


def _loss_and_grad_x(
    charges: np.ndarray,
    tensor: np.ndarray,
    x: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    t = softmax(x)
    kappa = np.einsum("ijk,j,k->i", tensor, t, t)
    slopes = charges.T @ kappa
    slope_square = float(slopes @ slopes)
    kappa_square = max(float(kappa @ kappa), 1e-24)
    loss = slope_square / (len(slopes) * kappa_square)

    # d mu_a / d t_l = 2 * sum_{i,k} k_i^a d_{i,l,k} t_k, using symmetric d_ijk.
    dmu_dt = 2.0 * np.einsum("ia,ilk,k->al", charges, tensor, t)
    d_slope_square_dt = 2.0 * (slopes @ dmu_dt)

    # d kappa_i / d t_l = 2 * sum_k d_{i,l,k} t_k.
    dkappa_dt = 2.0 * np.einsum("ilk,k->il", tensor, t)
    d_kappa_square_dt = 2.0 * (kappa @ dkappa_dt)

    grad_t = (
        d_slope_square_dt * kappa_square - slope_square * d_kappa_square_dt
    ) / (len(slopes) * kappa_square * kappa_square)

    # Softmax Jacobian-vector product: grad_x_m = t_m * (grad_t_m - <grad_t,t>).
    grad_x = t * (grad_t - float(grad_t @ t))
    return loss, grad_x, t, slopes, kappa, slope_square / len(slopes)


def find_slope_zero(
    matrix: list[list[int]],
    tensor: np.ndarray,
    *,
    tolerance: float = 1e-7,
    restarts: int = 24,
    max_iterations: int = 2500,
    seed: int = 12345,
    learning_rate: float = 0.08,
) -> SlopeSearchResult:
    """Search for t_i > 0, sum_i t_i=1 with all bundle slopes near zero.

    This is a numerical feasibility certificate in the favourable ambient cone
    approximation. It is not a formal proof of poly-stability.
    """

    charges = np.asarray(matrix, dtype=float)
    rng = np.random.default_rng(seed)
    best: tuple[float, np.ndarray, np.ndarray, np.ndarray, float, int] | None = None

    starts = [np.zeros(charges.shape[0])]
    starts.extend(rng.normal(size=charges.shape[0]) for _ in range(max(0, restarts - 1)))

    for restart_index, start in enumerate(starts, start=1):
        x = np.asarray(start, dtype=float)
        m = np.zeros_like(x)
        v = np.zeros_like(x)
        best_restart_loss = math.inf
        stale = 0

        for iteration in range(1, max_iterations + 1):
            loss, grad, t, slopes, kappa, mean_square_slope = _loss_and_grad_x(charges, tensor, x)
            if best is None or loss < best[0]:
                best = (loss, t.copy(), slopes.copy(), kappa.copy(), mean_square_slope, iteration)
            kappa_norm = max(float(np.linalg.norm(kappa)), 1e-12)
            if max(abs(float(s)) for s in slopes) / kappa_norm <= tolerance:
                best = (loss, t.copy(), slopes.copy(), kappa.copy(), mean_square_slope, iteration)
                return _result_from_best(best, True, restart_index, seed)

            if loss + 1e-18 < best_restart_loss:
                best_restart_loss = loss
                stale = 0
            else:
                stale += 1
                if stale > 400 and loss < tolerance * tolerance:
                    break

            m = 0.9 * m + 0.1 * grad
            v = 0.999 * v + 0.001 * (grad * grad)
            step = learning_rate * m / (np.sqrt(v) + 1e-10)
            x -= step
            x -= x.mean()

    if best is None:
        raise RuntimeError("slope search produced no result")
    return _result_from_best(best, False, restarts, seed, tolerance)


def _result_from_best(
    best: tuple[float, np.ndarray, np.ndarray, np.ndarray, float, int],
    feasible: bool,
    restarts: int,
    seed: int,
    tolerance: float = 1e-7,
) -> SlopeSearchResult:
    loss, t, slopes, kappa, mean_square_slope, iterations = best
    max_abs = max(abs(float(s)) for s in slopes)
    kappa_norm = max(float(np.linalg.norm(kappa)), 1e-12)
    max_normalized = max_abs / kappa_norm
    return SlopeSearchResult(
        feasible=feasible or max_normalized <= tolerance,
        max_abs_slope=max_abs,
        max_normalized_slope=max_normalized,
        mean_square_slope=float(mean_square_slope),
        normalized_mean_square_slope=float(loss),
        kahler_point=[float(x) for x in t],
        kappa=[float(x) for x in kappa],
        slopes=[float(x) for x in slopes],
        iterations=iterations,
        restarts=restarts,
        seed=seed,
    )
