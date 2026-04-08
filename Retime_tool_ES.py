# -*- coding: utf-8 -*-
###################################################
# Retime Slider v4 by Evgeniy Sechko
# Clean cmds-only approach:
#   - Snapshot stores orig_time + current_t per key
#   - current_t updated after every tick — no proximity search
#   - Undo stays ON the whole time — one chunk per drag
#   - GE selection / timeline range / full timeline fallback
###################################################

import maya.cmds as cmds
import maya.mel as mel

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_bias_slider  = None
_undo_open    = False
_lock_range   = None   # (start, end) or None

# Snapshot — built once per drag, updated each tick:
# [{'curve': str, 'orig_time': float, 'current_t': float, 'is_boundary': bool}, ...]
_session_keys = None


# ---------------------------------------------------------------------------
# Timeline helpers
# ---------------------------------------------------------------------------

def _get_time_slider():
    try:
        return mel.eval('$tmpVar=$gPlayBackSlider')
    except Exception:
        return 'timeControl1'


def _get_timeline_range_live():
    ts = _get_time_slider()
    try:
        if not cmds.timeControl(ts, q=True, rangeVisible=True):
            return None
        start, end = cmds.timeControl(ts, q=True, rangeArray=True)
        if start == end:
            return None
        return float(start), float(end)
    except Exception:
        return None


def _set_timeline_range(rng):
    if not rng:
        return
    ts = _get_time_slider()
    start, end = rng
    try:
        cmds.timeControl(ts, e=True, rangeVisible=True, rangeArray=(start, end))
    except Exception:
        try:
            cmds.timeControl(ts, e=True, rangeVisible=True,
                             rangeArray="{0}:{1}".format(int(start), int(end)))
        except Exception:
            pass


def _get_full_timeline_range():
    return (float(cmds.playbackOptions(q=True, min=True)),
            float(cmds.playbackOptions(q=True, max=True)))


# ---------------------------------------------------------------------------
# Snapshot collection  (called ONCE at drag start)
# ---------------------------------------------------------------------------

def _collect_snapshot():
    """
    Returns list of key entries. Each entry:
        curve       : anim curve name (str)
        orig_time   : time at drag start (float) — never changes
        current_t   : where the key is RIGHT NOW — updated each tick
        is_boundary : bool — boundary keys are not moved
    """
    global _lock_range
    snapshot = []

    # --- 1) Graph Editor selected keys -------------------------------------
    curves = cmds.keyframe(q=True, name=True, sl=True) or []
    if curves:
        for crv in curves:
            times = cmds.keyframe(crv, q=True, sl=True, tc=True) or []
            if not times:
                continue
            min_t = min(times)
            max_t = max(times)
            for t in times:
                snapshot.append({
                    'curve':       crv,
                    'orig_time':   float(t),
                    'current_t':   float(t),
                    'is_boundary': abs(t - min_t) < 1e-6 or abs(t - max_t) < 1e-6
                })
        return snapshot

    # --- 2 & 3) Object(s) + range ------------------------------------------
    objs = cmds.ls(sl=True) or []
    if not objs:
        return []

    live = _get_timeline_range_live()
    if live:
        _lock_range = live
    elif _lock_range is None:
        _lock_range = _get_full_timeline_range()

    start, end = _lock_range

    for obj in objs:
        obj_curves = cmds.keyframe(obj, q=True, name=True) or []
        for crv in obj_curves:
            times = cmds.keyframe(crv, q=True, tc=True, time=(start, end)) or []
            if not times:
                continue
            min_t = min(times)
            max_t = max(times)
            for t in times:
                snapshot.append({
                    'curve':       crv,
                    'orig_time':   float(t),
                    'current_t':   float(t),
                    'is_boundary': abs(t - min_t) < 1e-6 or abs(t - max_t) < 1e-6
                })

    return snapshot



# ---------------------------------------------------------------------------
# Bell curve calculator
# ---------------------------------------------------------------------------

def _get_bell_value(adist):
    """
    Calculate bell curve value.
    adist: normalized absolute distance from center (0 to 1)
    Returns: weight (0 to 1)
    
    Uses smooth curve that is extremely flat in center and rises toward edges.
    Degree 5 polynomial for minimal movement at center.
    """
    # Quintic (degree 5) for extremely flat center
    return max(0.0, 1.0 - adist ** 5)


# ---------------------------------------------------------------------------
# Core: restore + apply  (exact — uses current_t, not proximity search)
# ---------------------------------------------------------------------------

def _restore_and_apply(snapshot, bias):
    """
    Apply key displacement by:
    1. Calculate desired delta from original position
    2. Apply delta incrementally (not restore-then-reapply)
    """
    if not snapshot:
        return

    all_orig = [k['orig_time'] for k in snapshot]
    min_t    = min(all_orig)
    max_t    = max(all_orig)
    if max_t == min_t:
        return

    # Find curve peak (maximum absolute value) to use as center
    # TEMPORARILY DISABLED - testing geometric center
    peak_time = center_t = 0.5 * (min_t + max_t)  # Use geometric center for now
    
    # try:
    #     # Get values at each key to find the peak (max or min by absolute value)
    #     peak_val = 0.0
    #     found_peak = False
    #     for k in snapshot:
    #         crv = k['curve']
    #         try:
    #             # Get value at this key
    #             vals = cmds.keyframe(crv, q=True, time=k['orig_time'], vc=True)
    #             if vals:
    #                 val = vals[0]
    #                 # Track which time has the maximum absolute value
    #                 if abs(val) > abs(peak_val):
    #                    peak_val = val
    #                    peak_time = k['orig_time']
    #                    found_peak = True
    #         except Exception as e:
    #             print("ERROR getting value for {}: {}".format(crv, e))
    #     
    #     if found_peak:
    #         center_t = peak_time
    #         print("Peak found at time={} with val={}".format(peak_time, peak_val))
    # except Exception as e:
    #     print("Exception in peak detection: {}".format(e))

    half_range = 0.5 * (max_t - min_t)
    bias_scale = abs(bias) / 10.0  # 0..1

    # Calculate desired NEW positions
    all_orig_sorted = sorted(all_orig)
    
    # Calculate desired positions for all keys
    desired_positions = {}  # orig_time -> new_time
    for orig_t in all_orig:
        if bias == 0.0:
            desired_positions[orig_t] = orig_t
            continue

        boundary_strength = 0.03 if abs(orig_t - min_t) < 1e-6 or abs(orig_t - max_t) < 1e-6 else 1.0

        if bias > 0.0:
            # Spread - proportional scaling from center with smooth distribution
            dist   = (orig_t - center_t) / half_range
            adist  = abs(dist)
            # Quintic curve - faster falloff toward edges
            bell   = max(0.0, 1.0 - adist ** 5)
            # Apply proportional stretch from center point
            # stretch_factor = 1.0 means no change, >1.0 means stretch outward
            stretch_factor = 1.0 + bell * bias_scale * 1.5
            new_t = center_t + (orig_t - center_t) * stretch_factor
        else:
            # Smooth - stronger effect than spread
            prev_t = next_t = None
            for tt in all_orig_sorted:
                if tt < orig_t - 1e-6:
                    prev_t = tt
                elif tt > orig_t + 1e-6 and next_t is None:
                    next_t = tt
            if prev_t is None or next_t is None:
                desired_positions[orig_t] = orig_t
                continue
            mid   = 0.5 * (prev_t + next_t)
            dist   = (orig_t - center_t) / half_range
            adist  = abs(dist)
            # Cubic falloff for smoother gradient
            bell   = max(0.0, 1.0 - adist ** 3)
            # Amplify smooth effect - use 6x multiplier without hard limit
            smooth_strength = bell * bias_scale * boundary_strength * 6.0
            # Soft clamp: reduce effect smoothly at edges if > 1.0
            if smooth_strength > 1.0:
                smooth_strength = 1.0 + (smooth_strength - 1.0) * 0.3
            new_t = (1.0 - smooth_strength) * orig_t + smooth_strength * mid

        new_t = max(min_t, min(max_t, new_t))
        desired_positions[orig_t] = new_t

    # Preserve monotonic order with adaptive safety margin
    min_allowed = min_t
    final_positions = {}
    range_size = max_t - min_t
    safety_margin = max(0.001, range_size * 0.001)  # 0.1% of range
    
    for i, orig_t in enumerate(all_orig_sorted):
        new_t = desired_positions[orig_t]
        new_t = max(new_t, min_allowed + 1e-6)
        
        # Near boundaries: keep safe margin for second-to-last key
        if i == len(all_orig_sorted) - 2:  # Second to last key
            # Reserve minimal space before the last key 
            new_t = min(new_t, max_t - safety_margin)
        
        new_t = min(new_t, max_t)
        final_positions[orig_t] = new_t
        min_allowed = new_t

    # Debug final positions for large spread
    if bias > 5.0:
        print("Final:  {}".format(["{:.2f}".format(final_positions[t]) for t in all_orig_sorted]))
    
    for k in snapshot:
        orig_t = k['orig_time']
        desired_t = final_positions[orig_t]
        current_t = k['current_t']
        
        # Calculate how far to move from current position
        delta = desired_t - orig_t  # Target delta from original
        current_delta = current_t - orig_t  # Current delta
        move_amount = delta - current_delta  # How much more to move
        
        if abs(move_amount) < 1e-6:
            continue
            
        target_t = current_t + move_amount
        
        # Clamp to boundaries
        target_t = max(min_t, min(max_t, target_t))
        
        crv = k['curve']
        try:
            cmds.keyframe(crv, e=True,
                          time=(current_t, current_t),
                          timeChange=target_t)
            k['current_t'] = target_t
        except RuntimeError:
            pass


# ---------------------------------------------------------------------------
# Undo helpers
# ---------------------------------------------------------------------------

def _open_undo():
    global _undo_open
    if not _undo_open:
        cmds.undoInfo(openChunk=True)
        _undo_open = True


def _close_undo():
    global _undo_open
    if _undo_open:
        cmds.undoInfo(closeChunk=True)
        _undo_open = False


# ---------------------------------------------------------------------------
# Slider callbacks
# ---------------------------------------------------------------------------

def _on_bias_drag(*args):
    global _bias_slider, _session_keys, _lock_range

    if _bias_slider is None:
        return

    # Build snapshot once on first tick of this drag session
    if _session_keys is None:
        curves = cmds.keyframe(q=True, name=True, sl=True) or []
        if not curves:
            live = _get_timeline_range_live()
            if live:
                _lock_range = live

        _session_keys = _collect_snapshot()

        if not _session_keys:
            return  # nothing to work on — don't open undo chunk

        _open_undo()

    if not _session_keys:
        return

    # Keep timeline highlight visible
    curves = cmds.keyframe(q=True, name=True, sl=True) or []
    if not curves and _lock_range:
        _set_timeline_range(_lock_range)

    bias = cmds.floatSliderGrp(_bias_slider, q=True, v=True)
    _restore_and_apply(_session_keys, bias)


def _on_bias_release(*args):
    global _bias_slider, _session_keys

    if _bias_slider is None:
        return

    try:
        curves = cmds.keyframe(q=True, name=True, sl=True) or []
        if not curves and _lock_range:
            _set_timeline_range(_lock_range)
    finally:
        _close_undo()
        _session_keys = None

    cmds.floatSliderGrp(_bias_slider, e=True, v=0.0)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def _create_ui():
    global _bias_slider

    if cmds.window("RetimeSliderV4", q=True, exists=True):
        cmds.deleteUI("RetimeSliderV4")

    cmds.window(
        "RetimeSliderV4",
        title="Retime Slider v4 by Evgeniy Sechko",
        sizeable=False,
        widthHeight=(340, 90)
    )

    cmds.columnLayout(adj=True, co=('both', 10))
    cmds.text(l="Retime Slider v4", h=22, align='center', font='boldLabelFont')
    cmds.separator(h=4, style='none')

    cmds.rowLayout(numberOfColumns=1, adj=1)
    cmds.frameLayout(labelVisible=False, bgc=(0.25, 0.25, 0.35), mw=4, mh=4)
    cmds.columnLayout(adj=True)

    _bias_slider = cmds.floatSliderGrp(
        field=False,
        label="",
        minValue=-10.0,
        maxValue=10.0,
        value=0.0,
        precision=2,
        cw2=[0, 300],
        dragCommand=_on_bias_drag,
        changeCommand=_on_bias_release,
        ann="Left: smooth  |  Right: spread"
    )

    cmds.setParent('..')
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.separator(h=4, style='none')
    cmds.text(l="Smooth  <-    |    ->  Spread", h=20, align='center')
    cmds.showWindow("RetimeSliderV4")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def launch():
    global _lock_range, _session_keys
    _lock_range   = None
    _session_keys = None
    _create_ui()


if __name__ == "__main__":
    launch()