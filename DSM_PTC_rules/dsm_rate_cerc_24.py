import math

def round_to_two(value):
    """Utility to round values to the nearest two decimal places."""
    return round(value, 2)

def calculate_normal_rate(acp_dam, acp_rtm, ancillary_charge):
    """
    Calculates the Normal Rate (NR) for a time block [cite: 254-260].
    NR is the highest of:
    A) Weighted average ACP of DAM
    B) Weighted average ACP of RTM
    C) 1/3(DAM) + 1/3(RTM) + 1/3(Ancillary Charge)
    """
    option_c = (1/3 * acp_dam) + (1/3 * acp_rtm) + (1/3 * ancillary_charge)
    nr = max(acp_dam, acp_rtm, option_c)
    return round_to_two(nr)

def get_buyer_volume_limit(schedule_mwh, buyer_type='Standard'):
    """
    Determines Volume Limits for Buyers based on their category [cite: 318-319].
    :param buyer_type: 'Standard', 'Small' (<400MW), 'RE-rich', or 'Super RE-rich'
    """
    if buyer_type == 'Standard':
        vlb1 = min(0.10 * schedule_mwh, 100 / 4)  # 10% or 100MW (converted to MWh for 15m block)
        vlb2 = min(0.15 * schedule_mwh, 200 / 4)
    elif buyer_type == 'Small':
        vlb1 = min(0.20 * schedule_mwh, 40 / 4)
        vlb2 = float('inf') # VLB(3) is not defined for small buyers
    elif buyer_type == 'RE-rich':
        vlb1, vlb2 = 200 / 4, 300 / 4
    elif buyer_type == 'Super RE-rich':
        vlb1, vlb2 = 250 / 4, 350 / 4
    return vlb1, vlb2

def get_seller_volume_limit(scheduled_injection_mwh, seller_category='General'):
    """Determines Volume Limits for Sellers[cite: 265, 269, 271]."""
    if seller_category == 'General':
        return min(0.10 * scheduled_injection_mwh, 100 / 4)
    elif seller_category == 'RoR':
        return min(0.15 * scheduled_injection_mwh, 150 / 4)
    elif seller_category == 'MSW':
        return 0.20 * scheduled_injection_mwh
    return 0

def get_dsm_rate(entity_type, freq, nr, rr_or_contract, deviation, schedule_mwh, available_cap=None, is_wind=False):
    """
    Core engine to calculate the final DSM rate (Paise/kWh) [cite: 263-316].
    """
    f = round_to_two(freq)
    
    # --- BUYER LOGIC --- [cite: 300-316]
    if entity_type == 'Buyer':
        vlb1, vlb2 = get_buyer_volume_limit(schedule_mwh)
        abs_dev = abs(deviation)
        
        if deviation > 0:  # Over-drawal (Payable)
            if abs_dev <= vlb1:
                if f >= 50.05: return 0.75 * nr [cite: 303]
                if f <= 49.90: return 1.50 * nr [cite: 305]
                if f > 50.00: return nr * (1 - (f - 50.00) * 500 / 100)
                return nr * (1 + (50.00 - f) * 500 / 100)
            elif abs_dev <= vlb2:
                return 1.50 * nr if f < 50.00 else nr [cite: 312-313]
            else: # VLB 3
                return 2.00 * nr if f < 50.00 else nr [cite: 316]
        
        else:  # Under-drawal (Receivable)
            if f >= 50.05: return 0.50 * nr [cite: 302]
            if f <= 49.90: return 1.00 * nr [cite: 304]
            if f > 50.00: return nr * (0.9 - (f - 50.00) * 800 / 100)
            return nr * (0.9 + (50.00 - f) * 100 / 100)

    # --- GENERAL SELLER LOGIC --- 
    elif entity_type == 'General Seller':
        limit = get_seller_volume_limit(schedule_mwh, 'General')
        if abs(deviation) <= limit:
            if 49.97 <= f <= 50.03: return rr_or_contract
            if deviation < 0: # Under-injection (Payable)
                if f > 50.05: return 0.85 * rr_or_contract
                if f < 49.90: return 1.50 * rr_or_contract
                if f > 50.03: return rr_or_contract * (1 - (f - 50.03) * 750 / 100)
                return rr_or_contract * (1 + (49.97 - f) * 715 / 100)
            else: # Over-injection (Receivable)
                if f > 50.05: return 0
                if f < 49.90: return 1.15 * rr_or_contract
                if f > 50.03: return rr_or_contract * (1 - (f - 50.03) * 2500 / 100)
                return rr_or_contract * (1 + (49.97 - f) * 215 / 100)
        else:
            return 2.00 * rr_or_contract if deviation < 0 and f < 49.90 else 0

    # --- WIND/SOLAR LOGIC --- [cite: 272-285]
    elif entity_type == 'WS Seller':
        # Deviation % is based on Available Capacity [cite: 245]
        dev_pc = (abs(deviation) / available_cap) * 100
        v1 = 15 if is_wind else 10 # Up to 31.03.2026 [cite: 281, 284]
        v2 = 20 if is_wind else 15
        
        if deviation < 0: # Under-injection (Payable)
            if dev_pc <= v1: return rr_or_contract
            if dev_pc <= v2: return 1.10 * rr_or_contract
            return 2.00 * rr_or_contract
        else: # Over-injection (Receivable)
            if dev_pc <= v1: return rr_or_contract
            if dev_pc <= v2: return 0.90 * rr_or_contract
            return 0

    return 0
