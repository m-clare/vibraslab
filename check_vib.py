from numpy import pi, sin


def calculate_mode_scaling(x, y, Lb, Lg, fb, fg):
	if fb <= fg:
		phi = sin(pi * x / Lb) * sin(pi * (y + Lg) / (3 * Lg))
	else:
		phi = sin(pi * (x + Lb) / (3 * Lb)) * sin(pi * y / Lg)
	return phi

def calculate_