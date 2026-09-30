"""Archived deterministic reconstruction, consolidated for reproducibility.

The centered five-sample mean uses zero padding, matching the archived
Python implementation and all numerical reconstruction tables.
Units: seconds, feet, ft/s, ft/s^2; reported speed errors use mph.
"""
import numpy as np

import pandas as pd

import math

MPH_TO_FTPS = 1.4666666666666666

FTPS_TO_MPH = 1.0 / MPH_TO_FTPS

DT = 0.1

V_STOP = 0.5

STOP_LINE_COORD2 = 1074.0

ALPHA0 = 10.0

BAR_ALPHA = 34.0

JMAX = 50.0

TAU = 0.5

T_STAR = 5.0

TTB_REF = 1.5

L_A, L_P, L_T = 0.7, 0.6, 0.4

DELTA_T = 1.0

CP_MIN_SEG_SEC = 1.0

CP_SMOOTH_W = 5

CP_DELTA = 0.2

def moving_average(x, w):
    if w <= 1:
        return x.copy()
    return np.convolve(x, np.ones(w) / w, mode="same")

def detect_t2_change_point(t, a, dt=DT, min_seg_sec=CP_MIN_SEG_SEC, smooth_w=CP_SMOOTH_W, delta=CP_DELTA):
    n = len(a)
    kmin = max(int(min_seg_sec / dt), 1)
    kmax = n - kmin - 1
    if kmax <= kmin:
        return float(t[n // 2]), int(n // 2)

    a_sm = moving_average(a, smooth_w)

    best = None
    for k in range(kmin, kmax + 1):
        mu1 = a_sm[:k].mean()
        mu2 = a_sm[k:].mean()
        if mu2 < mu1 - delta:
            sse = ((a_sm[:k] - mu1) ** 2).sum() + ((a_sm[k:] - mu2) ** 2).sum()
            if best is None or sse < best[0]:
                best = (sse, k)

    if best is None:
        best = (np.inf, kmin)
        for k in range(kmin, kmax + 1):
            mu1 = a_sm[:k].mean()
            mu2 = a_sm[k:].mean()
            sse = ((a_sm[:k] - mu1) ** 2).sum() + ((a_sm[k:] - mu2) ** 2).sum()
            if sse < best[0]:
                best = (sse, k)

    _, k = best
    return float(t[k]), int(k)

def safe_speed(d, alpha, dt=DT):
    d = max(d, 0.0)
    return max(0.0, -alpha * dt + math.sqrt((alpha * dt) ** 2 + 2.0 * alpha * d))

def simulate_constdecel(t, x0, v0, x_stop, dt=DT):
    d0 = x_stop - x0
    if d0 <= 1e-9:
        a_cd = 0.0
    else:
        a_cd = -v0 * v0 / (2.0 * d0)
    v_pred = np.maximum(0.0, v0 + a_cd * t)
    return v_pred

def simulate_safeenv(t, x0, v0, x_stop, alpha0=ALPHA0, dt=DT):
    x, v = x0, v0
    out = [v0]
    for _ in range(1, len(t)):
        d = x_stop - x
        vs = safe_speed(d, alpha0, dt)
        v_next = min(v, vs)
        x = x + v_next * dt
        v = v_next
        out.append(v)
    return np.array(out)

def simulate_cgp(t, x0, v0, a0, x_stop, t1, t2,
                  alpha0=ALPHA0, bar_alpha=BAR_ALPHA, jmax=JMAX,
                  l_a=L_A, l_p=L_P, l_t=L_T, t_star=T_STAR, ttb_ref=TTB_REF, delta_t=DELTA_T,
                  dt=DT, gate=True, ugm=True, return_state=False):
    x, v = x0, v0
    a = float(np.clip(a0, -bar_alpha, 0.0))
    out = [v0]
    states = [(x, v, a)]
    a_plus = None

    for k in range(1, len(t)):
        tk = t[k - 1]
        d = x_stop - x
        if d <= 0.0:
            v, a = 0.0, 0.0
            out.append(v)
            states.append((x, v, a))
            continue

        v_safe = safe_speed(d, alpha0, dt)

        if a_plus is None and tk >= t1:
            ttb = d / max(v, 1e-6)
            g_a = math.exp(a)
            g_p = math.tanh(ttb_ref / max(ttb, 1e-6))
            g_t = 1.0 / (1.0 + math.exp(-(t1 - t_star) / delta_t))
            c = (1.0 + l_a * g_a + l_p * g_p + l_t * g_t) if ugm else 1.0
            alpha_req = v * v / (2.0 * max(d, 1e-6))
            a_plus = -min(bar_alpha, c * alpha_req)

        H = 1.0 if gate and tk >= t2 else 0.0
        a_des = (1.0 - H) * a + H * (a_plus if a_plus is not None else a)
        v_des = v + a_des * dt

        a_min = max(-bar_alpha, a - jmax * dt)
        a_max = min(0.0, a + jmax * dt)
        v_min = max(0.0, v + a_min * dt)
        v_max = min(v_safe, v + a_max * dt)

        if v_min > v_max:
            v_next = min(max(v_des, 0.0), v_safe)
        else:
            v_next = min(v_max, max(v_min, v_des))

        a_next = (v_next - v) / dt
        x = x + v_next * dt
        v, a = v_next, a_next
        out.append(v)
        states.append((x, v, a))

    return np.array(states) if return_state else np.array(out)
