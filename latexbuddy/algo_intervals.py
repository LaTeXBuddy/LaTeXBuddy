from operator import itemgetter


list_interval_tuples = [(0, 5, 3), (2, 3, 1), (7, 8, 1)]  # example intervals


def get_best_intervals(interval_tuples):
    """returns the non overlapping intervals with the maximum sum of severities"""

    sorted_intervals = sorted(interval_tuples, key=itemgetter(1))  # Sort intervals by end
    n = len(list_interval_tuples) - 1
    return max_no_overlap(n, sorted_intervals)


def max_no_overlap(i, sorted_intervals):
    """Calculates the optimal set of intervals
    with maximum sum of severities for the first i-1 intervals up to the index i.
    Can later be optimized with DP to make less recursive calls if needed"""

    n = len(sorted_intervals)
    if i == -1:
        return [], 0
    if i <= n:
        minus_one = max_no_overlap(i-1, sorted_intervals)
        pre = max_no_overlap(pred(i, sorted_intervals), sorted_intervals)
        
        if minus_one[1] > pre[1] + sorted_intervals[i][2]:
            return max_no_overlap(i-1, sorted_intervals)
        else:
            pre[0].append(sorted_intervals[i])
            return pre[0], pre[1] + sorted_intervals[i][2]


def pred(i, sorted_intervals):
    """calculates the index of the closest predecessor to the interval with index i"""

    n = len(sorted_intervals) - 1
    i_start = sorted_intervals[i][0]
    j = i - 1
    while j >= 0:
        if int(sorted_intervals[j][1]) <= i_start:
            return j  # interval with index j is closest predecessor
        j = j - 1
    return -1  # no predecessor exists


print(get_best_intervals(list_interval_tuples))
