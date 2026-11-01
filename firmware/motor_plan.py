"""Plan fuer eine Fahrt: Liste aus (Anzahl Schritte, Schritte pro Sekunde). Reines Python, ohne Hardware."""


def segments(steps, rate_min, rate_max, ramp_steps, sections):
    """Rampe hoch, Reisefahrt, Rampe runter. Die Summe der Schritte ist genau `steps`."""
    if steps <= 0:
        return []
    ramp = min(ramp_steps, steps // 2)
    per = ramp // sections
    if per < 1:
        return [(steps, rate_min)]
    ramp = per * sections
    up = []
    for i in range(sections):
        rate = rate_min + (rate_max - rate_min) * (i + 1) // (sections + 1)
        up.append((per, rate))
    cruise = steps - 2 * ramp
    out = list(up)
    if cruise > 0:
        out.append((cruise, rate_max))
    out.extend(reversed(up))
    return out
