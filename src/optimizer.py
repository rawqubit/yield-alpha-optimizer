import scipy.optimize as opt
import numpy as np

def optimize_portfolio(yields, risks, gas_fees, portfolio_size, max_risk):
    """
    Optimizes the allocation of a stablecoin portfolio to maximize overall net yield
    (yield minus gas fees) while keeping the weighted average risk below or equal
    to a maximum risk tolerance.

    Parameters:
    yields (dict): Protocol names -> expected yield rates (e.g., {'Aave_Eth': 0.05})
    risks (dict): Protocol names -> assigned risk scores (e.g., {'Aave_Eth': 0.2})
    gas_fees (dict): Protocol names -> fixed gas cost to deposit/withdraw in $
    portfolio_size (float): Total portfolio value in $
    max_risk (float): Maximum allowed weighted average risk score.

    Returns:
    dict: A dictionary mapping protocol names to their optimal allocation weights (summing to 1).
    """
    protocols = list(yields.keys())

    # Check data integrity
    for p in protocols:
        if p not in risks:
            raise ValueError(f"Missing risk score for protocol: {p}")
        if p not in gas_fees:
            raise ValueError(f"Missing gas fee for protocol: {p}")

    n = len(protocols)

    # We have 2*n variables:
    # 0 to n-1: x_i (weight of portfolio allocated to protocol i)
    # n to 2n-1: y_i (binary variable, 1 if x_i > 0, else 0)

    # Objective function: Maximize Net Yield = Sum(x_i * yield_i * portfolio_size - y_i * gas_fee_i)
    # scipy minimizes, so we negate it:
    # c = [-yield_i * portfolio_size, ..., gas_fee_i, ...]
    c = np.zeros(2 * n)
    for i, p in enumerate(protocols):
        c[i] = -yields[p] * portfolio_size
        c[n + i] = gas_fees[p]

    # Constraints:

    # 1. Sum of weights x_i = 1
    # A_eq * vars = b_eq
    A_eq = np.zeros((1, 2 * n))
    for i in range(n):
        A_eq[0, i] = 1.0
    b_eq = np.array([1.0])

    # 2. Weighted average risk <= max_risk
    # Sum(x_i * risk_i) <= max_risk
    A_ub = np.zeros((1 + n, 2 * n))
    for i in range(n):
        A_ub[0, i] = risks[protocols[i]]
    b_ub = np.zeros(1 + n)
    b_ub[0] = max_risk

    # 3. Big-M constraint to link x_i and y_i: x_i <= y_i
    # x_i - y_i <= 0
    for i in range(n):
        A_ub[1 + i, i] = 1.0
        A_ub[1 + i, n + i] = -1.0
        b_ub[1 + i] = 0.0

    # Bounds
    # x_i between 0 and 1
    # y_i between 0 and 1 (they are integer, so effectively binary 0 or 1)
    bounds = [(0, 1) for _ in range(n)] + [(0, 1) for _ in range(n)]

    # Integrality
    # x_i are continuous (0), y_i are integer (1)
    integrality = [0] * n + [1] * n

    # Solve MILP
    result = opt.milp(c=c, integrality=integrality, bounds=opt.Bounds(lb=[b[0] for b in bounds], ub=[b[1] for b in bounds]), constraints=opt.LinearConstraint(A_ub, ub=b_ub), options={'disp': False})

    # Add equality constraint to LinearConstraint.
    # We can combine A_eq and A_ub into a single constraint block

    A_combined = np.vstack([A_eq, A_ub])
    # The equality constraint has lb == ub
    lb_combined = np.concatenate([b_eq, [-np.inf] * (1 + n)])
    ub_combined = np.concatenate([b_eq, b_ub])

    result = opt.milp(c=c, integrality=integrality, bounds=opt.Bounds(lb=[b[0] for b in bounds], ub=[b[1] for b in bounds]), constraints=opt.LinearConstraint(A_combined, lb=lb_combined, ub=ub_combined))

    if result.success:
        allocations = {protocols[i]: round(result.x[i], 4) for i in range(n)}

        # Check if the net yield is actually positive. If the gas fees are larger than the yield, it might just allocate everything to the lowest fee protocol to minimize loss.
        # If the best net yield is negative, we should probably throw an error.
        net_yield = -result.fun
        if net_yield < 0:
            raise ValueError("Portfolio too small: Gas fees exceed potential yield.")

        return allocations
    else:
        raise ValueError("Could not find an allocation that satisfies the given risk tolerance.")
