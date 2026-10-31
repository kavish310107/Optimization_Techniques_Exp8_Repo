"""
Realistic Software Codebase and Test Suite Models for Track J.
Defines:
- SoftwareModule, TestRequirement (coverage targets), and TestCase.
- Deterministic synthetic generator for large realistic software repositories (CI test suites).
- APFD (Average Percentage of Faults Detected) metric computation for test prioritization.
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Tuple
import numpy as np


@dataclass
class TestCase:
    __test__ = False
    id: int
    name: str
    duration_ms: float
    covered_requirements: Set[int] = field(default_factory=set)
    flakiness_score: float = 0.0
    faults_detected: Set[int] = field(default_factory=set)


@dataclass
class TestSuiteInstance:
    __test__ = False
    name: str
    num_requirements: int
    num_faults: int
    test_cases: List[TestCase]

    @property
    def total_duration_ms(self) -> float:
        return sum(tc.duration_ms for tc in self.test_cases)

    @property
    def total_covered_requirements(self) -> Set[int]:
        s = set()
        for tc in self.test_cases:
            s.update(tc.covered_requirements)
        return s

    @property
    def all_detected_faults(self) -> Set[int]:
        s = set()
        for tc in self.test_cases:
            s.update(tc.faults_detected)
        return s


def generate_realistic_ci_test_suite(
    num_tests: int = 150,
    num_requirements: int = 80,
    num_faults: int = 25,
    seed: int = 42
) -> TestSuiteInstance:
    """
    Synthesizes a realistic CI test suite representing a large modular software repository:
    - Highly uneven test execution durations (unit tests vs integration tests).
    - Power-law requirement coverage (common core modules covered by many tests; edge modules covered by few).
    - Injected subtle regression faults mapped to specific requirement interactions.
    """
    rng = np.random.default_rng(seed)
    
    test_cases: List[TestCase] = []
    
    # Generate test durations log-normally: mean ~25ms, tail up to 800ms
    durations = rng.lognormal(mean=3.2, sigma=0.8, size=num_tests)
    durations = np.clip(durations, 5.0, 1200.0)
    
    # Requirement coverage distributions: core requirements (0-15) have high probability, peripheral requirements (16-79) have lower probability
    req_weights = 1.0 / (np.arange(1, num_requirements + 1) ** 0.6)
    req_weights /= req_weights.sum()
    
    # Fault distribution: faults occur in complex requirement clusters
    fault_requirement_map = {}
    for f in range(num_faults):
        # A fault is triggered when specific requirements are exercised
        target_reqs = set(rng.choice(num_requirements, size=rng.integers(1, 4), replace=False))
        fault_requirement_map[f] = target_reqs
        
    for i in range(num_tests):
        # Number of requirements covered by this test (3 to 12)
        n_cov = int(rng.integers(3, 14))
        covered = set(rng.choice(num_requirements, size=min(n_cov, num_requirements), replace=False, p=req_weights))
        
        # Check which faults are exposed by this test case
        detected_faults = set()
        for f, target_reqs in fault_requirement_map.items():
            if target_reqs.issubset(covered) and (rng.uniform() < 0.85):
                detected_faults.add(f)
                
        tc = TestCase(
            id=i,
            name=f"test_suite_{i:03d}",
            duration_ms=float(durations[i]),
            covered_requirements=covered,
            flakiness_score=float(rng.uniform(0.0, 0.05)),
            faults_detected=detected_faults
        )
        test_cases.append(tc)
        
    # Ensure full coverage is possible: if any requirement is uncovered, add it to a random test
    all_cov = set().union(*(tc.covered_requirements for tc in test_cases))
    for r in range(num_requirements):
        if r not in all_cov:
            chosen_tc = rng.choice(test_cases)
            chosen_tc.covered_requirements.add(r)
            
    return TestSuiteInstance(
        name=f"CI_Regression_Suite_N{num_tests}_R{num_requirements}",
        num_requirements=num_requirements,
        num_faults=num_faults,
        test_cases=test_cases
    )


def compute_apfd(ordered_tests: List[TestCase], all_faults: Set[int]) -> float:
    """
    Computes Average Percentage of Faults Detected (APFD), the standard SE optimization metric:
    APFD = 1 - (sum_{i=1}^m TF_i) / (n * m) + 1 / (2 * n)
    where:
    - n = total number of test cases in the prioritized sequence
    - m = total number of faults detected
    - TF_i = position of the first test in the sequence that detects fault i.
    Range is [0.0, 1.0], with 1.0 being optimal fault detection speed.
    """
    n = len(ordered_tests)
    m = len(all_faults)
    if n == 0 or m == 0:
        return 0.0
        
    # Map each fault to the index of the first test detecting it (1-based index)
    tf_sum = 0
    detected = set()
    
    for rank, tc in enumerate(ordered_tests, start=1):
        for f in tc.faults_detected:
            if f in all_faults and f not in detected:
                detected.add(f)
                tf_sum += rank
                
    # If some faults were never detected by the subset, assign rank n + 1
    unseen_faults = len(all_faults - detected)
    tf_sum += unseen_faults * (n + 1)
    
    apfd = 1.0 - (tf_sum / (n * m)) + (1.0 / (2.0 * n))
    return float(np.clip(apfd, 0.0, 1.0))
