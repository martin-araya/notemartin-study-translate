def compute(a, b):
    """Compute the sum of two numbers.

    :param a: The first addend.
    :type a: int
    :param b: The second addend.
    :type b: int
    :returns: The arithmetic sum.
    :rtype: int
    :raises ValueError: If both arguments are negative.
    """
    if a < 0 and b < 0:
        raise ValueError("negative")
    return a + b