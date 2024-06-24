import numpy as np

def normalize_l2(x):
    """
    Normaliza un vector utilizando la norma L2.
    
    Args:
    x (np.array): Vector a normalizar.
    
    Returns:
    np.array: Vector normalizado.
    """
    norm = np.linalg.norm(x)
    if norm == 0:
        return x
    return x / norm
