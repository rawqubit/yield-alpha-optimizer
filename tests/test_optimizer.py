import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from optimizer import optimize_portfolio

def test_high_risk_tolerance():
    yields = {'A': 0.05, 'B': 0.10}
    risks = {'A': 0.1, 'B': 0.5}
    gas_fees = {'A': 1.0, 'B': 1.0}

    # High risk tolerance, no fees issue, it should allocate 100% to B
    allocations = optimize_portfolio(yields, risks, gas_fees, portfolio_size=10000, max_risk=1.0)
    assert allocations['A'] == 0.0
    assert allocations['B'] == 1.0

def test_low_risk_tolerance():
    yields = {'A': 0.05, 'B': 0.10}
    risks = {'A': 0.1, 'B': 0.5}
    gas_fees = {'A': 1.0, 'B': 1.0}

    # Low risk tolerance limits us to A
    allocations = optimize_portfolio(yields, risks, gas_fees, portfolio_size=10000, max_risk=0.1)
    assert allocations['A'] == 1.0
    assert allocations['B'] == 0.0

def test_mixed_risk_tolerance():
    yields = {'A': 0.05, 'B': 0.10}
    risks = {'A': 0.1, 'B': 0.5}
    gas_fees = {'A': 0.0, 'B': 0.0}

    # Risk tolerance exactly halfway (0.3), no gas fees to make it simple
    allocations = optimize_portfolio(yields, risks, gas_fees, portfolio_size=10000, max_risk=0.3)
    assert allocations['A'] == 0.5
    assert allocations['B'] == 0.5

def test_gas_fee_viability_small_portfolio():
    yields = {'Eth': 0.10, 'Poly': 0.09}
    risks = {'Eth': 0.1, 'Poly': 0.1}
    gas_fees = {'Eth': 50.0, 'Poly': 1.0}

    # Small portfolio size of $500
    # Yield on Eth: 50 - Gas: 50 = $0 net
    # Yield on Poly: 45 - Gas: 1 = $44 net
    # It should pick Poly despite lower yield.
    allocations = optimize_portfolio(yields, risks, gas_fees, portfolio_size=500, max_risk=1.0)
    assert allocations['Eth'] == 0.0
    assert allocations['Poly'] == 1.0

def test_gas_fee_viability_large_portfolio():
    yields = {'Eth': 0.10, 'Poly': 0.09}
    risks = {'Eth': 0.1, 'Poly': 0.1}
    gas_fees = {'Eth': 50.0, 'Poly': 1.0}

    # Large portfolio size of $100,000
    # Yield on Eth: 10,000 - Gas: 50 = 9950 net
    # Yield on Poly: 9,000 - Gas: 1 = 8999 net
    # It should pick Eth to maximize net yield.
    allocations = optimize_portfolio(yields, risks, gas_fees, portfolio_size=100000, max_risk=1.0)
    assert allocations['Eth'] == 1.0
    assert allocations['Poly'] == 0.0

def test_unprofitable_portfolio():
    yields = {'A': 0.05}
    risks = {'A': 0.1}
    gas_fees = {'A': 100.0}

    # Portfolio of 1000 yields $50, but gas is $100.
    # The portfolio is unprofitable.
    with pytest.raises(ValueError, match="Portfolio too small: Gas fees exceed potential yield."):
        optimize_portfolio(yields, risks, gas_fees, portfolio_size=1000, max_risk=1.0)

def test_impossible_risk_tolerance():
    yields = {'A': 0.05, 'B': 0.10}
    risks = {'A': 0.1, 'B': 0.5}
    gas_fees = {'A': 0.0, 'B': 0.0}

    with pytest.raises(ValueError, match="Could not find an allocation that satisfies the given risk tolerance."):
        optimize_portfolio(yields, risks, gas_fees, portfolio_size=1000, max_risk=0.05)

def test_missing_data():
    yields = {'A': 0.05}
    risks = {}
    gas_fees = {'A': 1.0}
    with pytest.raises(ValueError, match="Missing risk score for protocol: A"):
        optimize_portfolio(yields, risks, gas_fees, portfolio_size=1000, max_risk=0.5)

    yields2 = {'A': 0.05}
    risks2 = {'A': 0.1}
    gas_fees2 = {}
    with pytest.raises(ValueError, match="Missing gas fee for protocol: A"):
        optimize_portfolio(yields2, risks2, gas_fees2, portfolio_size=1000, max_risk=0.5)
