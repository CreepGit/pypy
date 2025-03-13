import math, random, time, json

def isPrime(n: int):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def findPrimesUnder(n: int, count: int):
    primes = []
    i = n
    while len(primes) < count:
        if isPrime(i):
            primes.append(i)
        i -= 1
    return primes

def findPrimeUnder(n: int, steps: int = 1):
    i = n
    while steps > 0:
        i -= 1
        if isPrime(i):
            steps -= 1
    return i

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def isCoprime(a: int, b: int):
    return gcd(a, b) == 1

def findPrimeFactors(n: int):
    """Find all prime factors of n, including repeated factors"""
    factors = []
    # Check for factor 2 separately
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    
    # Check for odd prime factors
    i = 3
    while i * i <= n:
        while n % i == 0:
            factors.append(i)
            n //= i
        i += 2
    
    # If n is a prime number greater than 2
    if n > 2:
        factors.append(n)
    
    return factors

def findUniqueFactorsOfPhi(p):
    """Find the unique prime factors of p-1 (Euler's totient function for a prime)"""
    return set(findPrimeFactors(p-1))

def modPow(base, exponent, modulus):
    """Compute (base^exponent) % modulus efficiently"""
    result = 1
    base = base % modulus
    while exponent > 0:
        if exponent % 2 == 1:
            result = (result * base) % modulus
        exponent = exponent >> 1
        base = (base * base) % modulus
    return result

def isPrimitiveRoot(a, p):
    """
    Check if a is a primitive root modulo p (where p is prime).
    A number a is a primitive root modulo p if the order of a is p-1.
    """
    if not isPrime(p):
        raise ValueError("p must be prime")
    
    # If a is not coprime to p, it can't be a primitive root
    if gcd(a, p) != 1:
        return False
    
    # Find the unique prime factors of p-1
    factors = findUniqueFactorsOfPhi(p)
    
    # For each prime factor q of p-1, check if a^((p-1)/q) ≡ 1 (mod p)
    # If any of these congruences hold, then a is not a primitive root
    for q in factors:
        if modPow(a, (p-1) // q, p) == 1:
            return False
    
    return True

def willComputeToCompletion(a: int, m: int, c: int, _x: int):
    """
    Check if the LCG will have a full period based on the Hull-Dobell theorem
    and additional checks for primitive roots.
    
    For an LCG with parameters (a, c, m) to have a full period:
    1. gcd(c, m) = 1
    2. If m is prime:
       a. a must be a primitive root modulo m
    3. If m is composite:
       a. For every prime p that divides m, p also divides a-1
       b. If 4 divides m, then 4 divides a-1
    """
    # Step 1: gcd(c, m) = 1
    if gcd(c, m) != 1:
        print(f"Failed step 1: gcd({c}, {m}) = {gcd(c, m)} ≠ 1")
        return False
    print(f"Passed step 1: gcd({c}, {m}) = 1")
    
    # Check if m is prime
    if isPrime(m):
        # For prime modulus, we need a to be a primitive root modulo m
        # First, check if a ≠ 1 (mod m)
        if a % m == 1:
            print(f"Failed prime modulus check: a = {a} ≡ 1 (mod {m})")
            return False
        
        # Check if a is a primitive root modulo m
        if not isPrimitiveRoot(a, m):
            print(f"Failed primitive root check: {a} is not a primitive root modulo {m}")
            return False
        
        print(f"Passed primitive root check: {a} is a primitive root modulo {m}")
        return True
    
    # For composite modulus, apply the full Hull-Dobell theorem
    
    # Step 2: For every prime p that divides m, p also divides a-1
    unique_factors = set(findPrimeFactors(m))
    print(f"Prime factors of {m}: {unique_factors}")
    print(f"a-1 = {a-1}")
    for factor in unique_factors:
        if (a - 1) % factor != 0:
            print(f"Failed step 2: {a-1} is not divisible by {factor}")
            return False
    print(f"Passed step 2: a-1 = {a-1} is divisible by all prime factors of m")
    
    # Step 3: If 4 divides m, then 4 divides a-1
    if m % 4 == 0:
        if ((a - 1) % 4) != 0:
            print(f"Failed step 3: {a-1} is not divisible by 4")
            return False
        print(f"Passed step 3: {a-1} is divisible by 4")
    else:
        print(f"Skipped step 3: {m} is not divisible by 4")
    
    return True

def computeTillCompletion(a: int, m: int, c: int, x: int):
    """Compute the LCG until it has computed a full cycle"""
    visited = set()
    current_x = x
    cycle_start = None
    
    # Store the first few values for debugging
    first_values = []
    
    i = 0
    while True:
        current_x = (a * current_x + c) % m
        
        # Store first 10 values for debugging
        if i < 10:
            first_values.append(current_x)
        
        if current_x in visited:
            cycle_start = current_x
            break
        
        visited.add(current_x)
        i += 1
    
    print(f"First 10 values: {first_values}")
    print(f"Cycle starts at: {cycle_start}")
    print(f"Cycle length: {len(visited)}")
    
    return len(visited)

def check(a: int, m: int, c: int, x: int):
    will_complete = willComputeToCompletion(a, m, c, x)
    found = computeTillCompletion(a, m, c, x)
    
    # For prime modulus, the maximum period is m-1
    expected_period = m-1 if isPrime(m) else m
    
    difference = abs(found - expected_period)
    print(f"{found=} {expected_period=} {difference=}")
    
    # Check if our prediction matches the actual result
    if will_complete:
        # We predicted full period, so difference should be small
        if difference > 2:  # Within 2, probably right?
            print(f"ERROR: Predicted full period but got {found} < {expected_period}")
            print(f"ERROR: Predicted full period but got {found} < {expected_period}")
            print(f"ERROR: Predicted full period but got {found} < {expected_period}")
            print(f"ERROR: Predicted full period but got {found} < {expected_period}")
            return False
        else:
            print(f"SUCCESS: Predicted full period and got {found} ≈ {expected_period}")
            return True
    else:
        # We predicted not full period, so difference should be large
        if difference <= 2:
            print(f"ERROR: Predicted not full period but got {found} ≈ {expected_period}")
            print(f"ERROR: Predicted not full period but got {found} ≈ {expected_period}")
            print(f"ERROR: Predicted not full period but got {found} ≈ {expected_period}")
            print(f"ERROR: Predicted not full period but got {found} ≈ {expected_period}")
            print(f"ERROR: Predicted not full period but got {found} ≈ {expected_period}")
            return False
        else:
            print(f"SUCCESS: Predicted not full period and got {found} < {expected_period}")
            return True


# print("Test case 1:")
# print(check(69069, findPrimeUnder(52**4), 1, 0))
# print("\nTest case 2:")
# print(check(69060, findPrimeUnder(52**4), 1, 0))

# # Add a test case with a smaller modulus for easier debugging
# print("\nTest case 3 (smaller modulus):")
# small_prime = 97  # A small prime number
# print(check(69, small_prime, 1, 0))

# # Add a test case with a different multiplier for the same modulus
# print("\nTest case 4 (different multiplier):")
# print(check(69061, findPrimeUnder(52**4), 1, 0))

# # Add a test case with a known primitive root
# print("\nTest case 5 (known primitive root):")
# print(check(3, 7, 1, 0))  # 3 is a primitive root modulo 7

# print("\nTest case 6 (large modulus):")
# print("Computes =", willComputeToCompletion(69069, findPrimeUnder(52**4, 3), 1, 0))
# print("|")
# print(check(69069, findPrimeUnder(52**4, 3), 1, 0))

# fails = 0
# for test_num in range(100):
#     print(f"\nTest case {test_num}:")
#     success = check(69069, findPrimeUnder(52**4, random.randint(1, 400)), 1, 0)
#     if not success:
#         time.sleep(1)
#         fails += 1
        
# print(f"Fails: {fails}")


def gatherGoodValues():
    CANDITATE_A_VALUES = [214013, 69069, 48271, 16807, 22695477, 3263443, 465019, 481621, 456979]
    TARGETS = [
        int(math.pow(52, 4)),
        int(math.pow(62, 4)),
        int(math.pow(52, 5)),
        int(math.pow(62, 5)),
        int(math.pow(52, 6)),
        int(math.pow(62, 6)),
        int(math.pow(52, 7)),
        int(math.pow(62, 7)),
    ]
    def test(target: int):
        for m in findPrimesUnder(target, 100):
            for a in CANDITATE_A_VALUES:
                if willComputeToCompletion(a, m, 1, 0):
                    return {
                        "a": a,
                        "m": m,
                        "c": 1,
                        "x": 0
                    }
    results = []
    for target_m in TARGETS:
        results.append(test(target_m))
    return results

results = gatherGoodValues()
print(json.dumps(results, indent=4))
# [
#     {
#         "a": 214013,
#         "m": 7311593,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 214013,
#         "m": 14776331,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 69069,
#         "m": 380204023,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 214013,
#         "m": 916132829,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 22695477,
#         "m": 19770609653,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 22695477,
#         "m": 56800235549,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 69069,
#         "m": 1028071702519,
#         "c": 1,
#         "x": 0
#     },
#     {
#         "a": 48271,
#         "m": 3521614606199,
#         "c": 1,
#         "x": 0
#     }
# ]