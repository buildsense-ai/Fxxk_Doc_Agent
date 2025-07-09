import math
from collections import defaultdict
import sys


def solve_climbing_stairs():
    target_stairs = 100

    dp = [defaultdict(int) for _ in range(target_stairs + 1)]
    dp[0][2] = 1

    total_solutions = 0

    # Pre-calculate powers of 1.5 and their floor values to avoid repeated computation
    # and to check for overflow early if needed (though limiting N will prevent it)
    # We set a reasonable upper bound for N based on the fact that (1.5)^N grows very fast
    # and 2 * current_legs will usually not be large enough to sustain a huge N
    # Let's say if current_legs reaches max ~2^15, then 2*current_legs ~ 65536.
    # log(65536, 1.5) is approx 30.
    # So, N should not exceed ~30-40.
    # Let's set a practical max_n_limit to avoid overflow and useless calculations.
    # Max steps in one go will rarely exceed 30 for any reasonable `current_legs`
    # before `legs_lost` becomes too large.
    MAX_N_IN_ONE_GO = 30  # A safe upper limit for n, based on (1.5)^n growth

    # This array will store floor((3/2)^n) for n from 1 up to MAX_N_IN_ONE_GO
    legs_lost_precomputed = [0] * (MAX_N_IN_ONE_GO + 1)
    for n_val in range(1, MAX_N_IN_ONE_GO + 1):
        try:
            # Check if (1.5)**n_val exceeds a very large number before computing floor
            # This is more robust than just checking math.floor result
            val = (1.5) ** n_val
            if val > sys.float_info.max / 2:  # Use a safer limit
                print(f"Warning: (1.5)^{n_val} is too large for float, capping legs_lost_precomputed.")
                legs_lost_precomputed[n_val] = float('inf')  # Mark as impossible to continue
            else:
                legs_lost_precomputed[n_val] = math.floor(val)
        except OverflowError:
            print(f"Overflow during precomputation for n={n_val}. Setting to infinity.")
            legs_lost_precomputed[n_val] = float('inf')  # Mark as impossible to continue

    for i in range(target_stairs + 1):
        for current_legs, count in dp[i].items():
            if count == 0:
                continue

            # Iterate n from 1 up to current_legs, but also cap it at MAX_N_IN_ONE_GO
            for n in range(1, min(current_legs, MAX_N_IN_ONE_GO) + 1):

                legs_lost = legs_lost_precomputed[n]

                # If legs_lost is already marked as infinite (due to precomputation overflow or simply too large)
                if legs_lost == float('inf'):
                    continue  # This n value is too large, the path cannot continue

                next_legs = (current_legs * 2) - legs_lost

                if next_legs <= 0:
                    continue

                next_stairs = i + n

                if next_stairs > target_stairs:
                    continue
                elif next_stairs == target_stairs:
                    total_solutions += count
                else:
                    dp[next_stairs][next_legs] += count

    return total_solutions


# Run the calculation
result = solve_climbing_stairs()
print(f"当台阶数为一百时，登顶共有 {result} 种方案。")