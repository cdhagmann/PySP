# coding=utf-8
import random
import itertools

from numpy.linalg import eigvalsh
import numpy as np
from scipy.stats import randint
from scipy.stats import norm
from scipy.stats import nbinom


class InvalidCorrelationMatrix(Exception):
    def __init__(self, message):
        super(InvalidCorrelationMatrix, self).__init__(message)


def is_valid_correlation_matrix(matrix, eps=1e-8):
    height, width = np.shape(matrix)
    if height != width:
        raise InvalidCorrelationMatrix('Matrix is not Square')

    for i in xrange(height):
        for j in xrange(i, width):
            if i == j:
                if abs(matrix[i, j] - 1) > eps:
                    raise InvalidCorrelationMatrix('Entry in the diagonal not equal to 1.')
            elif abs(matrix[i, j] - matrix[j, i]) > eps:
                raise InvalidCorrelationMatrix('Matrix is not symmetric.')
            elif abs(matrix[i, j]) - 1 > eps:
                raise InvalidCorrelationMatrix('Matrix entry not between -1 and 1.')

    if min(eigvalsh(matrix)) + 1e-8 < 0:
        raise InvalidCorrelationMatrix('Matrix is not PSD.')

    return True


def spectral_decomposition(pairwise_matrix):
    """
    Simonian, J. (2010). The most simple methodology to create a valid correlation matrix for risk management
        and option pricing purposes. Applied Economics Letters, 17(18), 1767–1768.
        http://doi.org/10.1080/13504850903299628

    Code from http://stackoverflow.com/a/18542094
    """
    n, m = np.shape(pairwise_matrix)
    assert n == m
    eigenvalues, eigenvectors = np.linalg.eig(pairwise_matrix)
    val = np.matrix(np.maximum(eigenvalues, 1e-8))
    vec = np.matrix(eigenvectors)
    temp_matrix = np.array((1 / (np.multiply(vec, vec) * val.T))).reshape(n)
    temp_matrix = np.matrix(np.sqrt(np.diag(temp_matrix)))
    temp_matrix2 = temp_matrix * vec * np.diag(np.array(np.sqrt(val)).reshape(n))
    correlation_matrix = temp_matrix2 * temp_matrix2.T
    return correlation_matrix


# count1 = total = 0
# for i in xrange(n):
#     for j in xrange(i + 1, n):
#         count1 += abs(foo[i, j]) >= .2
#         total += 1
# true_correlation_fraction = count1 / float(total)
# print '{:.0%} CORRELATED'.format(count1 / float(total))


def random_correlation_matrix(n, correlation_fraction=.5, split=None, bounds=(.5, 1)):
    if split is None:
        split = correlation_fraction

    pairwise_matrix = np.ones((n, n))

    for i in xrange(n):
        for j in xrange(i + 1, n):
            if random.random() <= split:
                pairwise_matrix[i, j] = pairwise_matrix[j, i] = random.choice((-1, 1)) * random.uniform(*bounds)
            else:
                pairwise_matrix[i, j] = pairwise_matrix[j, i] = random.uniform(-bounds[0], bounds[0])

    correlation_matrix = spectral_decomposition(pairwise_matrix)
    is_valid_correlation_matrix(correlation_matrix)
    #
    # count1 = total = 0
    # for i in xrange(n):
    #     for j in xrange(i + 1, n):
    #         count1 += abs(correlation_matrix[i, j]) >= .2
    #         total += 1
    # true_correlation_fraction = count1 / float(total)
    # shift = correlation_fraction - true_correlation_fraction
    #
    # print '{:.0%} CORRELATED'.format(count1 / float(total)), correlation_fraction, shift, split, bounds
    # if abs(shift) >= .01:
    #     shift = correlation_fraction - true_correlation_fraction
    #     if split >= 1 and shift >= 0:
    #         bounds = list(bounds)
    #         bounds[0] *= 1.01
    #         if bounds[0] >= 1:
    #             pass
    #         else:
    #             print correlation_fraction, shift, bounds
    #             correlation_matrix = random_correlation_matrix(n, correlation_fraction, split, bounds)
    #     else:
    #         split += shift
    #         split = max([0, split])
    #         split = min([1, split])
    #         correlation_matrix = random_correlation_matrix(n, correlation_fraction, split)

    return correlation_matrix


def flatten_matrix(A):
    return [A[tup] for tup in itertools.product(*map(xrange, A.shape))]


def uniform_demand_distribution(C, t, low=0, high=25):
    n = int(C.shape[0])
    U = np.linalg.cholesky(C)

    raw_demand = np.random.normal(size=(t, n))

    shifted_demand = np.dot(raw_demand, U.T)

    flat_demand = flatten_matrix(shifted_demand)
    true_std = np.std(flat_demand)
    true_mean = np.mean(flat_demand)

    normalized_demand = (shifted_demand - true_mean) / true_std

    new_demand = randint.ppf(norm.cdf(normalized_demand), low, high)

    return new_demand.T


def neg_binom_demand_distribution(C, t, r=10, p=.5):
    n = int(C.shape[0])
    U = np.linalg.cholesky(C)

    raw_demand = np.random.normal(size=(t, n))

    shifted_demand = np.dot(raw_demand, U.T)

    flat_demand = flatten_matrix(shifted_demand)
    true_std = np.std(flat_demand)
    true_mean = np.mean(flat_demand)

    normalized_demand = (shifted_demand - true_mean) / true_std

    new_demand = nbinom.ppf(norm.cdf(normalized_demand), r, p)

    return new_demand.T
