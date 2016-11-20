# coding=utf-8
import math
import random
import time

import numpy as np

import pyfu


def _perf_bar_text(avg, stddev, n=20):
    """
    Returns an ascii progress bar showing the average relative to 1 with '#'s
    and two standard deviations with '~'s. E.g. '#####~~~~~       '.
    """
    if avg > 1:
        return '!' * n
    n_avg = int(avg * n)
    n_2dev = min(int((avg + stddev * 2) * n), n) - n_avg
    return ('#' * n_avg + '~' * n_2dev).ljust(n, ' ')


def _measure_duration(func, args_getter, repeats, expected_micros):
    """
    :param func: The function to time.
    :param args_getter: Returns sampled arguments to pass to the function.
    :param float expected_micros: For really short times, timer accuracy becomes
    a problem. But a short time also means we can afford a few repeats. This
    parameter controls that trade-off.
    :return float: The measured duration in micros.
    """
    sub_repeats = int(max(1, min(25, math.ceil(1000 / expected_micros))))

    total = 0.0
    squares_total = 0.0
    for _ in range(repeats):
        args = [args_getter() for _ in range(sub_repeats)]

        start_time = time.clock()
        for e in args:
            func(*e)
        duration = (time.clock() - start_time) / sub_repeats

        total += duration
        squares_total += duration ** 2

    mean_duration = total / repeats
    # Perf measurements aren't normal-distributed, and also our individual
    # samples were multiple runs. So the actual thing is more volatile than this
    # number implies.
    std_dev = (squares_total / repeats - mean_duration ** 2) ** 0.5

    return mean_duration, std_dev


_perf_goal_results = []
def perf_goal(avg_micros=0, avg_nanos=0, repeats=100, args=None):
    """
    A decorator that turns a function into a perf test.
    :param avg_micros: Maximum acceptable average duration, in microseconds.
    :param avg_nanos: Maximum acceptable average duration, in nanoseconds.
    :param repeats: Number of times to sample the function's running time.
    :param args: Arguments to pass into the method.
    """
    if args is None:
        args = []
    args_chooser = _sampled_generation(args, repeats)
    index = len(_perf_goal_results)
    _perf_goal_results.append(None)
    target_nanos = avg_nanos + 1000 * avg_micros
    target_micros = target_nanos * 0.001
    duration_desc = (str(avg_micros).rjust(3) + ' micros'
                     if avg_nanos == 0
                     else str(target_nanos).rjust(3) + ' nanos ')

    def decorate(func):
        name = func.__name__.replace('test_perf_', '')

        def wrapped():
            try:
                _perf_goal_results[index] = '[fail] ' + name

                mean_duration, std_dev = _measure_duration(func,
                                                           args_chooser,
                                                           repeats,
                                                           target_micros)

                avg_ratio = mean_duration * 10**6 / target_micros
                std_dev_ratio = std_dev * 10**6 / target_micros
                did_fail = avg_ratio > 1
                _perf_goal_results[index] = (
                    u"[%s] %s%% ±%s%% of target (%s) for %s" % (
                        _perf_bar_text(avg_ratio, std_dev_ratio),
                        str(int(avg_ratio * 100)).rjust(3, ' '),
                        str(int(std_dev_ratio * 100)).rjust(2, ' '),
                        duration_desc,
                        name))

                if did_fail:
                    raise AssertionError(
                        "%s took too long. Mean (%s us) over target (%s)." %
                        (name, mean_duration * 10 ** 6, duration_desc))
            finally:
                # Because tests can run out of order, we defer the printing
                # until we have all the results and can print in order.
                if all(e is not None for e in _perf_goal_results):
                    print('')
                    print('-------------')
                    print('perf results:')
                    print('-------------')
                    for r in _perf_goal_results:
                        print(r)
                    print('-------------')

        return wrapped
    return decorate


class Sample:
    """
    Recognized by perf_goal as an argument that should vary.
    """
    def __init__(self, sample_function):
        self.sample_function = sample_function


def _sampled_generation(sampler_args, backing_size):
    """
    When generating is more expensive than the thing being timed, we can save a
    lot of time by generating a reasonable number of samples then randomly
    choosing from those samples. This function does that.
    """
    def args_gen():
        ctx = dict()
        return [e.sample_function(ctx)
                if isinstance(e, Sample)
                else e
                for e in sampler_args]

    previous_samples = []

    def args_sample():
        if len(previous_samples) < backing_size:
            previous_samples.append(args_gen())
            return previous_samples[-1]
        return random.choice(previous_samples)

    return args_sample

unit_list = [v for k, v in pyfu.unit.default_unit_database.known_units.items()]


def _sample_random_unit_combo():
    r = 10 * (random.random() + 0.01) * (-1 if random.random() < 0.5 else +1)
    r *= random.choice(unit_list)
    r *= random.choice(unit_list)
    r /= random.choice(unit_list)
    if random.random() > 0.5:
        r *= random.choice(unit_list)
    while r.isDimensionless():
        r *= random.choice(unit_list)
    return r


def _sample_matching_combo_sampler(ctx):
    key = 'a_compatible_unit'
    if key not in ctx:
        ctx[key] = _sample_random_unit_combo()
    return ctx[key] * random.random()

a_random_unit_val = Sample(lambda _: _sample_random_unit_combo())
a_random_compatible_unit_val = Sample(_sample_matching_combo_sampler)

a_random_unit_array = Sample(lambda _:
                             np.array([random.random() for _ in range(1024)]) *
                             _sample_random_unit_combo())

a_random_compatible_unit_array = Sample(
    lambda ctx:
    np.array([random.random() for _ in range(1024)]) *
    _sample_matching_combo_sampler(ctx))
