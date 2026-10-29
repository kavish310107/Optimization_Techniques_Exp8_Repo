"""Max-Cut Graph Problem Formulation:
Given an undirected weighted graph G = (V, E, W):
Maximize cut size:
    Cut(S, S_bar) = sum_{(i,j) in E, i in S, j in S_bar} w_ij

Formulations:
1. Binary Variable formulation:
    x_i in {0, 1} indicates partition S (x_i=1) vs S_bar (x_i=0).
    Edge (i,j) is cut if x_i != x_j, i.e., x_i + x_j - 2 x_i x_j.
    Cut(x) = sum_{(i,j) in E} w_ij (x_i + x_j - 2 x_i x_j).

2. QUBO Minimization:
    Minimize x^T Q x, where Q_ij = 2 w_ij (i!=j) and Q_ii = - sum_j w_ij.

3. Ising Spin formulation (Binary-to-Spin conversion):
    Spin variable s_i in {-1, +1}:
    Relation: x_i = (1 - s_i) / 2  or  s_i = 1 - 2 x_i.
    Hamiltonian: H(s) = sum_{(i,j) in E} J_ij s_i s_j + sum_i h_i s_i + const.
    For Max-Cut: J_ij = w_ij / 2, with no local field (h_i = 0).
    Max-Cut equals ground state (minimum energy) of antiferromagnetic Ising model.
"""
from typing import Tuple, Dict, Optional
import numpy as np


class MaxCutProblem:
    """Max-Cut instance with QUBO and Ising model conversions."""

    def __init__(self, adjacency_matrix: np.ndarray, name: str = "MaxCut"):
        A = np.asarray(adjacency_matrix, dtype=float)
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Adjacency matrix must be square, got {A.shape}")
        # Enforce zero diagonal and symmetry
        np.fill_diagonal(A, 0.0)
        A = 0.5 * (A + A.T)

        self.W = A
        self.n = A.shape[0]
        self.name = name

    def evaluate_cut(self, x: np.ndarray) -> float:
        """Evaluate cut weight for binary partition vector x in {0, 1}^n."""
        x = np.asarray(x, dtype=float).round().astype(int)
        cut = 0.0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if x[i] != x[j]:
                    cut += self.W[i, j]
        return float(cut)

    def evaluate_energy(self, spins: np.ndarray) -> float:
        """Evaluate Ising energy H(s) for spin vector s in {-1, +1}^n.
        
        H(s) = sum_{(i<j)} J_ij s_i s_j
        where J_ij = W_ij / 2.
        """
        s = np.asarray(spins, dtype=float)
        J, h, offset = self.to_ising()
        # Energy = 0.5 * s^T J s + h^T s + offset
        energy = float(0.5 * s.T @ J @ s + np.dot(h, s) + offset)
        return energy

    def to_qubo(self) -> Tuple[np.ndarray, float]:
        """Convert Max-Cut to upper-triangular or symmetric QUBO minimization matrix.
        
        Maximize: sum_{(i<j)} w_ij (x_i + x_j - 2 x_i x_j)
        Minimize: sum_{(i<j)} w_ij (2 x_i x_j - x_i - x_j) = x^T Q x
        
        Returns:
            (Q_matrix, constant_offset)
        """
        Q = np.zeros((self.n, self.n), dtype=float)
        for i in range(self.n):
            # Q_ii = - degree(i) = - sum_j w_ij
            Q[i, i] = - np.sum(self.W[i, :])
            for j in range(self.n):
                if i != j:
                    Q[i, j] = self.W[i, j]
        return Q, 0.0

    def to_ising(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """Convert Max-Cut to Ising Hamiltonian parameters (J, h, offset).
        
        Using binary-to-spin substitution: x_i = (1 - s_i) / 2
        Cut(x) = sum_{(i<j)} w_ij * (1 - s_i s_j) / 2
               = 0.5 * sum_{(i<j)} w_ij - 0.5 * sum_{(i<j)} w_ij s_i s_j
               
        Minimizing energy H(s) = - Cut(s):
            H(s) = sum_{(i<j)} (w_ij / 2) s_i s_j - 0.5 * sum_{(i<j)} w_ij
            
        Returns:
            J (coupling matrix n x n), h (local magnetic field vector n), offset (scalar)
        """
        total_edge_weight = float(np.sum(np.triu(self.W, 1)))
        J = 0.5 * self.W.copy()  # Off-diagonal couplings J_ij = w_ij / 2
        np.fill_diagonal(J, 0.0)
        h = np.zeros(self.n, dtype=float)  # No linear bias in pure Max-Cut
        offset = - 0.5 * total_edge_weight
        return J, h, offset

    @staticmethod
    def binary_to_spin(x: np.ndarray) -> np.ndarray:
        """Convert x in {0, 1} to spin s in {-1, +1}: s = 1 - 2*x."""
        x = np.asarray(x, dtype=float)
        return 1.0 - 2.0 * x

    @staticmethod
    def spin_to_binary(s: np.ndarray) -> np.ndarray:
        """Convert spin s in {-1, +1} to x in {0, 1}: x = (1 - s) / 2."""
        s = np.asarray(s, dtype=float)
        return (1.0 - s) / 2.0

