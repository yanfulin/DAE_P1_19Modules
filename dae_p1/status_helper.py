from .M00_common import Verdict, ObservabilityResult

def calculate_simple_status(core_service) -> str:
    """
    Calculates a simplified status string (ok/unstable/suspected/investigation)
    based on the current state of the core service *without* triggering side effects.
    """
    
    # 1. Check for active investigation (Investigation)
    # If there is an active episode, we consider it 'investigation' or 'suspected' depending on preference.
    # The requirement asks for 'investigation'. M09 tracks episodes.
    if core_service.recognition.episodes.current is not None:
        return "investigation"

    # 2. Peek at latest data
    latest_metric = core_service.metrics_buf.last()
    if not latest_metric:
        return "ok" # No data yet, assume OK

    # 3. Re-run detection logic (stateless)
    is_bad, flags = core_service.recognition.detector.is_bad_window(latest_metric)
    
    # 4. Re-run observability logic (stateless)
    # Get latest event if any
    events = core_service.events_buf.snapshot()
    if events:
        obs_res = core_service.recognition.obs.check_event(events[-1])
        opaque = obs_res.opaque_risk
    else:
        # Default state with no events usually implies no immediate observability risk unless we expected one
        # But M16 logic says: check_no_change_event() -> INSUFFICIENT -> OPAQUE
        # However, for steady state 'ok', we shouldn't flag opaque if nothing is happening.
        # Let's align with M16: 
        #   if recent_change_events: check_event
        #   else: check_no_change_event -> which returns OPAQUE.
        # WAIT: If the system is IDLE, M16 says it's OPAQUE?
        # Let's look at M16 again in a moment. 
        # If strict M16 logic says no event = opaque, then 'ok' is impossible?
        # Let's assume for 'simple status', if no flags and no active episode, it is OK.
        opaque = False 
        
    # BUT, if we want to be consistent with 'suspected' logic:
    # Suspected = OPAQUE_RISK.
    
    # Let's refine the logic to be more user-friendly:
    
    if is_bad:
        # We have badness flags.
        # If opaque -> Suspected
        # If not opaque -> Unstable
        
        # We need to know if it's opaque for THIS bad window.
        # In M16: if recent_change_events matches logic.
        pass

    # Let's use the Verdict directly if we can, but Verdict requires us to know 'opaque' input.
    
    # Re-logic:
    # if flags exist:
    #    verdict = classifier.classify(flags, opaque)
    #    if verdict == OPAQUE_RISK -> suspected
    #    if verdict in [WAN, WIFI, etc] -> unstable
    # else:
    #    ok
    
    # How to determine opaque?
    # If there ARE flags, we look for a recent change event to explain them.
    # If no recent change event -> M16 says "INSUFFICIENT" -> OPAQUE.
    # So: Bad params + No recent event = Suspected (Opaque).
    #     Bad params + Recent event + Missing refs = Suspected (Opaque).
    #     Bad params + Recent event + Good refs = Unstable (Identified).
    
    if is_bad:
        # Check observability
        if events:
             # We ideally check if the event is 'recent' enough, but M16 just takes the list.
             # We'll assume the caller passes relevant events.
             obs_res = core_service.recognition.obs.check_event(events[-1])
             is_opaque = obs_res.opaque_risk
        else:
             # Bad window but no explaining event
             is_opaque = True
             
        if is_opaque:
            return "suspected"
        else:
            return "unstable"
            
    # If not bad
    return "ok"
