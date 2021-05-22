from operator import itemgetter
import copy


def best_intervals_no_overlap(list_intervals):
    """returns the non overlapping intervals with the maximum sum of severities via
    Dynamic Programming"""

    sorted_intervals = sorted(list_intervals, key=itemgetter(1))  # Sort intervals by end
    n = len(sorted_intervals)
    if n == 0:
        return [], 0
    if n == 1:
        return sorted_intervals, sorted_intervals[0][2]

    calculated = {-1: ([], 0)}  # initialize

    for i in range(n):
        if i == 0:
            calculated[i] = [sorted_intervals[i]], sorted_intervals[i][2]  # initialize
            continue
        pred_i = pred(i, sorted_intervals)
        if calculated[i-1][1] > calculated[pred_i][1] + sorted_intervals[i][2]:
            calculated[i] = calculated[i-1]
        else:
            copy_tuples = copy.deepcopy(calculated[pred_i][0])
            copy_tuples.append(sorted_intervals[i])
            calculated[i] = copy_tuples, calculated[pred_i][1] + sorted_intervals[i][2]
    return calculated[n - 1]  # add [0] here to just get the intervals without sum(s)


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


list_interval_tuples = [(0, 5, 3), (2, 3, 1), (2, 4, 3), (0, 8, 3), (4, 6, 2),
                        (2, 8, 3), (7, 8, 1), (7, 8, 2)]  # example intervals

print(best_intervals_no_overlap(list_interval_tuples))
