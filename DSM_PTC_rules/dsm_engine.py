from decimal import Decimal, ROUND_HALF_UP, getcontext
import json

# Set precision higher than Excel (which uses double precision ~15-17 digits)
getcontext().prec = 28

class DSMEngine:
    def __init__(self):
        pass

    def calculate_row(self, schedule_mwh, actual_mwh, frequency, rate):
        """
        Calculates DSM for a single time block.
        Inputs are expected as Decimal or numeric types.
        """
        S = Decimal(str(schedule_mwh))
        A_raw = Decimal(str(actual_mwh))
        F_freq = Decimal(str(frequency))
        K_rate = Decimal(str(rate))

        # Constants for logic
        factors_low = {
            Decimal('49.99'): Decimal('0.0091'),
            Decimal('49.98'): Decimal('0.0092'),
            Decimal('49.97'): Decimal('0.0093'),
            Decimal('49.96'): Decimal('0.0094'),
            Decimal('49.95'): Decimal('0.0095'),
            Decimal('49.94'): Decimal('0.0096'),
            Decimal('49.93'): Decimal('0.0097'),
            Decimal('49.92'): Decimal('0.0098'),
            Decimal('49.91'): Decimal('0.0099')
        }
        factors_bb = {
            Decimal('50'): Decimal('-0.01'),
            Decimal('49.99'): Decimal('-0.0105'),
            Decimal('49.98'): Decimal('-0.011'),
            Decimal('49.97'): Decimal('-0.0115'),
            Decimal('49.96'): Decimal('-0.012'),
            Decimal('49.95'): Decimal('-0.0125'),
            Decimal('49.94'): Decimal('-0.013'),
            Decimal('49.93'): Decimal('-0.0135'),
            Decimal('49.92'): Decimal('-0.014'),
            Decimal('49.91'): Decimal('-0.0145')
        }
        factors_r = {
            Decimal('50.01'): Decimal('0.0082'),
            Decimal('50.02'): Decimal('0.0074'),
            Decimal('50.03'): Decimal('0.0066'),
            Decimal('50.04'): Decimal('0.0058'),
            Decimal('50.05'): Decimal('0.005')
        }
        # factors_v and factors_z and factors_ad are identical to factors_r so we can reuse or define aliases
        factors_v = factors_r
        factors_z = factors_r
        factors_ad = factors_r

        factors_ba = {
            Decimal('50.01'): Decimal('-0.0095'),
            Decimal('50.02'): Decimal('-0.009'),
            Decimal('50.03'): Decimal('-0.0085'),
            Decimal('50.04'): Decimal('-0.008'),
            Decimal('50.05'): Decimal('-0.0075')
        }
        factors_bf = factors_ba
        factors_bj = factors_ba

        # Intermediate calculations from Excel
        E = S * 4  # Schedule (MW)
        F = A_raw * 4  # Act (MW)
        G = abs(F - E)  # DEV
        
        if E != 0:
            H = (G / E) * 100  # DEV %
        else:
            H = Decimal('0')
            
        I = (G / 4) * 1000  # DEV (Kwh)
        L = S * 1000  # Sch (Kwh)
        M = L * Decimal('0.05')  # 5% sch
        N = L * Decimal('0.10')  # 10% sch
        O = L * Decimal('0.15')  # 15% sch
        P = L * Decimal('0.20')  # 20% sch

        res = {
            "Schedule(MWH)": S,
            "Actual(MWH)": A_raw,
            "Schedule(MW)": E,
            "Act(MW)": F,
            "DEV": G,
            "DEV%": H,
            "DEV(Kwh)": I,
            "Freq": F_freq,
            "Rate": K_rate,
            "Sch(Kwh)": L,
            "5%sch": M,
            "10%sch": N,
            "15%sch": O,
            "20%sch": P
        }

        # Under drawal logic (F < E)
        is_under = F < E
        is_over = F > E
        is_high_sch = E > 400
        
        # --- Under drawal Sch>400 MW ---
        # Q: Dev within 10%
        Q = Decimal('0')
        if is_under and is_high_sch and I <= N:
            if F_freq == Decimal('50'):
                Q = I * K_rate * Decimal('0.009')
        res["UD_>400_10%"] = Q

        # R: Frequency based (Higher than 50)
        R = Decimal('0')
        if is_under and is_high_sch and I <= N:
            R = I * K_rate * factors_r.get(F_freq, Decimal('0'))
        res["UD_>400_R"] = R

        # S: Frequency based (Lower than 50)
        S_charge = Decimal('0')
        if is_under and is_high_sch and I <= N:
            if F_freq in factors_low:
                S_charge = I * K_rate * factors_low[F_freq]
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                S_charge = I * K_rate * Decimal('0.01')
        res["UD_>400_S"] = S_charge

        # T: High freq (>= 50.06)
        T = Decimal('0')
        if is_under and is_high_sch and I <= N:
            if Decimal('50.06') <= F_freq <= Decimal('50.09'):
                T = I * K_rate * 0
            elif F_freq >= Decimal('50.1'):
                T = I * K_rate * Decimal('-0.001')
        res["UD_>400_T"] = T

        # U, V, W, X (UD >400, Dev 10-15%)
        U = V = W = X = Decimal('0')
        if is_under and is_high_sch and N < I <= O:
            # U: 50Hz
            if F_freq == Decimal('50'):
                U = (N * K_rate * Decimal('0.009')) + ((I - N) * K_rate * Decimal('0.008'))
            # V: 50.01-50.05
            if F_freq in factors_v:
                V = (N * K_rate * factors_v[F_freq]) + ((I - N) * K_rate * Decimal('0.005'))
            # W: <50
            if F_freq in factors_low:
                W = (N * K_rate * factors_low[F_freq]) + ((I - N) * K_rate * Decimal('0.008'))
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                W = (N * K_rate * Decimal('0.01')) + ((I - N) * K_rate * Decimal('0.008'))
            # X: >=50.06
            if Decimal('50.06') <= F_freq <= Decimal('50.09'):
                X = I * K_rate * 0
            elif F_freq >= Decimal('50.1'):
                X = I * K_rate * Decimal('-0.001')
        
        res["UD_>400_10-15%_U"] = U
        res["UD_>400_10-15%_V"] = V
        res["UD_>400_10-15%_W"] = W
        res["UD_>400_10-15%_X"] = X

        # Y, Z, AA, AB (UD >400, Dev >15%)
        Y = Z = AA = AB = Decimal('0')
        if is_under and is_high_sch and I > O:
            # Y: Frequency 50 or lower
            if F_freq == Decimal('50'):
                Y = (N * K_rate * Decimal('0.009')) + (M * K_rate * Decimal('0.008')) + ((I - O) * 0)
            elif F_freq in factors_low:
                Y = (N * K_rate * factors_low[F_freq]) + (M * K_rate * Decimal('0.008')) + ((I - O) * 0)
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                Y = (N * K_rate * Decimal('0.01')) + (M * K_rate * Decimal('0.008')) + ((I - O) * 0)
            
            # Z: 50.01-50.05
            if F_freq in factors_z:
                Z = (N * K_rate * factors_z[F_freq]) + (M * K_rate * Decimal('0.005')) + ((I - O) * 0)
            
            # AA: 50.05-50.09
            if Decimal('50.05') < F_freq <= Decimal('50.09'):
                AA = I * K_rate * 0
            
            # AB: >=50.1
            if F_freq >= Decimal('50.1'):
                AB = I * K_rate * Decimal('-0.001')

        res["UD_>400_>15%_Y"] = Y
        res["UD_>400_>15%_Z"] = Z
        res["UD_>400_>15%_AA"] = AA
        res["UD_>400_>15%_AB"] = AB

        # --- Under drawal Sch<=400 MW ---
        # AC-AG: Dev till 20% (and Dev <= 40 MW)
        # Note: G <= 40 MW is equivalent to I <= 10000 Kwh
        AC = AD = AE = AF = AG = Decimal('0')
        if is_under and not is_high_sch and I <= P and G <= 40:
            if F_freq == Decimal('50'):
                AC = I * K_rate * Decimal('0.009')
            
            AD = I * K_rate * factors_ad.get(F_freq, Decimal('0'))
            
            if F_freq in factors_low:
                AE = I * K_rate * factors_low[F_freq]
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                AE = I * K_rate * Decimal('0.01')
                
            if Decimal('50.06') <= F_freq <= Decimal('50.09'):
                AF = I * K_rate * 0
            
            if F_freq >= Decimal('50.1'):
                AG = I * K_rate * Decimal('-0.001')
        
        res["UD_<=400_20%_AC"] = AC
        res["UD_<=400_20%_AD"] = AD
        res["UD_<=400_20%_AE"] = AE
        res["UD_<=400_20%_AF"] = AF
        res["UD_<=400_20%_AG"] = AG

        # AH-AZ: Dev above 20% (or Dev > 40 MW aka I > 10000)
        # Column AZ in Excel handles many of these. Let's merge logic for AH-AY into AZ if possible or keep them separate.
        # Actually AH-AY in JSON are mostly IF checks. AZ is the mega formula.
        # I'll implement AZ logic as it covers the bands.
        AZ = Decimal('0')
        if is_under and not is_high_sch:
            if I > P or G > 40:
                # The Excel AZ uses a nested IF structure for frequency.
                # It also uses OR logic which we interpreted as just using the base calculation.
                
                def calc_extra_ud(factor, extra_factor):
                    # Formula pattern: (10000*K*factor + (I-10000)*K*extra_factor)
                    # We need to decide if we use 10000 or P for the band limit.
                    # Since it's E<=400, 10% is 10000 if E=400.
                    # Wait, the Excel formula used 10000.
                    limit = Decimal('10000')
                    return (limit * K_rate * factor) + ((I - limit) * K_rate * extra_factor)

                if F_freq <= Decimal('49.9') and F_freq > 0:
                    AZ = calc_extra_ud(Decimal('0.01'), Decimal('0.008'))
                elif F_freq == Decimal('49.91'): AZ = calc_extra_ud(Decimal('0.0099'), Decimal('0.008'))
                elif F_freq == Decimal('49.92'): AZ = calc_extra_ud(Decimal('0.0098'), Decimal('0.008'))
                elif F_freq == Decimal('49.93'): AZ = calc_extra_ud(Decimal('0.0097'), Decimal('0.008'))
                elif F_freq == Decimal('49.94'): AZ = calc_extra_ud(Decimal('0.0096'), Decimal('0.008'))
                elif F_freq == Decimal('49.95'): AZ = calc_extra_ud(Decimal('0.0095'), Decimal('0.008'))
                elif F_freq == Decimal('49.96'): AZ = calc_extra_ud(Decimal('0.0094'), Decimal('0.008'))
                elif F_freq == Decimal('49.97'): AZ = calc_extra_ud(Decimal('0.0093'), Decimal('0.008'))
                elif F_freq == Decimal('49.98'): AZ = calc_extra_ud(Decimal('0.0092'), Decimal('0.008'))
                elif F_freq == Decimal('49.99'): AZ = calc_extra_ud(Decimal('0.0091'), Decimal('0.008'))
                elif F_freq == Decimal('50'): AZ = calc_extra_ud(Decimal('0.009'), Decimal('0.008'))
                elif F_freq == Decimal('50.01'): AZ = calc_extra_ud(Decimal('0.0082'), Decimal('0.005'))
                elif F_freq == Decimal('50.02'): AZ = calc_extra_ud(Decimal('0.0074'), Decimal('0.005'))
                elif F_freq == Decimal('50.03'): AZ = calc_extra_ud(Decimal('0.0066'), Decimal('0.005'))
                elif F_freq == Decimal('50.04'): AZ = calc_extra_ud(Decimal('0.0058'), Decimal('0.005'))
                elif F_freq == Decimal('50.05'): AZ = calc_extra_ud(Decimal('0.005'), Decimal('0.005'))
                elif Decimal('50.06') <= F_freq <= Decimal('50.09'):
                    AZ = I * K_rate * 0
                # AY handles >= 50.1 separately in SUM
        res["UD_<=400_>20%_AZ"] = AZ
        
        # AY: UD <= 400, F>=50.1
        AY = Decimal('0')
        if is_under and not is_high_sch:
            if (I > P or G > 40) and F_freq >= Decimal('50.1'):
                AY = I * K_rate * Decimal('-0.001')
        res["UD_<=400_>20%_AY"] = AY

        # Total Under Drawal Charges (BQ)
        # Formula: =-SUM(Q4:T4,U4:X4,Y4:AB4,AC4:AG4,AZ4,AY4)
        bq_sum = Q + R + S_charge + T + U + V + W + X + Y + Z + AA + AB + AC + AD + AE + AF + AG + AZ + AY
        res["Total under drawal charges"] = -bq_sum

        # --- Over drawal logic (F > E) ---
        # BA, BB, BC, BD: OD > 400, Dev within 10%
        BA = BB = BC = BD = Decimal('0')
        if is_over and is_high_sch and I <= N:
            # BA: 50.01-50.05
            BA = I * K_rate * factors_ba.get(F_freq, Decimal('0'))
            
            # BB: <=50
            factors_bb = {
                Decimal('50'): Decimal('-0.01'),
                Decimal('49.99'): Decimal('-0.0105'),
                Decimal('49.98'): Decimal('-0.011'),
                Decimal('49.97'): Decimal('-0.0115'),
                Decimal('49.96'): Decimal('-0.012'),
                Decimal('49.95'): Decimal('-0.0125'),
                Decimal('49.94'): Decimal('-0.013'),
                Decimal('49.93'): Decimal('-0.0135'),
                Decimal('49.92'): Decimal('-0.014'),
                Decimal('49.91'): Decimal('-0.0145')
            }
            if F_freq in factors_bb:
                BB = I * K_rate * factors_bb[F_freq]
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                BB = I * K_rate * Decimal('-0.015')
            
            # BC: 50.05 < J <= 50.09
            if Decimal('50.05') < F_freq <= Decimal('50.09'):
                BC = I * K_rate * Decimal('-0.005')
            
            # BD: >= 50.1
            if F_freq >= Decimal('50.1'):
                BD = I * K_rate * 0
        
        res["OD_>400_10%_BA"] = BA
        res["OD_>400_10%_BB"] = BB
        res["OD_>400_10%_BC"] = BC
        res["OD_>400_10%_BD"] = BD

        # BE, BF, BG, BH: OD > 400, Dev 10-15%
        BE = BF = BG = BH = Decimal('0')
        if is_over and is_high_sch and N < I <= O:
            # BE: 50Hz
            if F_freq == Decimal('50'):
                BE = (N * K_rate * Decimal('-0.01')) + ((I - N) * K_rate * Decimal('-0.01'))
            # BF: 50.01-50.05
            if F_freq in factors_bf:
                BF = (N * K_rate * factors_bf[F_freq]) + ((I - N) * K_rate * Decimal('-0.01'))
            # BG: <50
            if F_freq in factors_bb:
                BG = (N * K_rate * factors_bb[F_freq]) + ((I - N) * K_rate * Decimal('-0.015'))
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                BG = (N * K_rate * Decimal('-0.015')) + ((I - N) * K_rate * Decimal('-0.015'))
            # BH: 50.05-50.09
            if Decimal('50.05') < F_freq <= Decimal('50.09'):
                BH = (N * K_rate * Decimal('-0.005')) + ((I - N) * K_rate * Decimal('-0.0075'))
            elif F_freq >= Decimal('50.1'):
                BH = I * K_rate * 0
        
        res["OD_>400_10-15%_BE"] = BE
        res["OD_>400_10-15%_BF"] = BF
        res["OD_>400_10-15%_BG"] = BG
        res["OD_>400_10-15%_BH"] = BH

        # BI, BJ, BK, BL: OD > 400, Dev > 15%
        BI = BJ = BK = BL = Decimal('0')
        if is_over and is_high_sch and I > O:
            # BI: <=50
            if F_freq == Decimal('50'):
                BI = (N * K_rate * Decimal('-0.01')) + (M * K_rate * Decimal('-0.01')) + ((I - O) * K_rate * Decimal('-0.01'))
            elif F_freq in factors_bb:
                # Note: BG-like pattern but slightly different factors in BI
                # Excel: IF(J4<=49.9, (N*K*-0.015)+(M*K*-0.015)+((I-O)*K*-0.02), ...)
                # Wait, I must use exactly what's in Row 304.
                # Col BI (Dev above 15%):
                # IF(J4=50, (N*K*-0.01)+(M*K*-0.01)+((I-O)*K*-0.01),
                # IF(J4=49.99, (N*K*-0.0105)+(M*K*-0.015)+((I-O)*K*-0.02), ...))
                extra_od_factor = Decimal('-0.02')
                base_od_limit = Decimal('-0.015')
                if F_freq in factors_bb:
                    BI = (N * K_rate * factors_bb[F_freq]) + (M * K_rate * base_od_limit) + ((I - O) * K_rate * extra_od_factor)
                elif F_freq <= Decimal('49.9') and F_freq > 0:
                    BI = (N * K_rate * Decimal('-0.015')) + (M * K_rate * Decimal('-0.015')) + ((I - O) * K_rate * extra_od_factor)
            
            # BJ: 50.01-50.05
            if F_freq in factors_bj:
                BJ = (N * K_rate * factors_bj[F_freq]) + (M * K_rate * Decimal('-0.01')) + ((I - O) * K_rate * Decimal('-0.01'))
            
            # BK: 50.05-50.09
            if Decimal('50.05') < F_freq <= Decimal('50.09'):
                BK = (N * K_rate * Decimal('-0.005')) + (M * K_rate * Decimal('-0.0075')) + ((I - O) * K_rate * Decimal('-0.01'))
            
            # BL: >= 50.1
            if F_freq >= Decimal('50.1'):
                BL = (I - O) * K_rate * Decimal('-0.005')

        res["OD_>400_>15%_BI"] = BI
        res["OD_>400_>15%_BJ"] = BJ
        res["OD_>400_>15%_BK"] = BK
        res["OD_>400_>15%_BL"] = BL

        # BM, BN, BO: OD <= 400, Dev till 20%
        BM = BN = BO = Decimal('0')
        if is_over and not is_high_sch and I <= P and G <= 40:
            # BM: <= 50
            if F_freq in factors_bb:
                BM = I * K_rate * factors_bb[F_freq]
            elif F_freq <= Decimal('49.9') and F_freq > 0:
                BM = I * K_rate * Decimal('-0.015')
            
            # BN: 50.01-50.05
            BN = I * K_rate * factors_ba.get(F_freq, Decimal('0')) # reusing ba factors
            
            # BO: >= 50.06
            if Decimal('50.06') <= F_freq <= Decimal('50.09'):
                BO = I * K_rate * Decimal('-0.005')
            elif F_freq >= Decimal('50.1'):
                BO = I * K_rate * 0
        
        res["OD_<=400_20%_BM"] = BM
        res["OD_<=400_20%_BN"] = BN
        res["OD_<=400_20%_BO"] = BO

        # BP: OD <= 400, Dev > 20%
        BP = Decimal('0')
        if is_over and not is_high_sch:
            if I > P or G > 40:
                def calc_extra_od(factor, extra_factor):
                    limit = Decimal('10000')
                    return (limit * K_rate * factor) + ((I - limit) * K_rate * extra_factor)

                if F_freq <= Decimal('49.9') and F_freq > 0:
                    BP = calc_extra_od(Decimal('-0.015'), Decimal('-0.015'))
                elif F_freq == Decimal('49.91'): BP = calc_extra_od(Decimal('-0.0145'), Decimal('-0.015'))
                elif F_freq == Decimal('49.92'): BP = calc_extra_od(Decimal('-0.014'), Decimal('-0.015'))
                elif F_freq == Decimal('49.93'): BP = calc_extra_od(Decimal('-0.0135'), Decimal('-0.015'))
                elif F_freq == Decimal('49.94'): BP = calc_extra_od(Decimal('-0.013'), Decimal('-0.015'))
                elif F_freq == Decimal('49.95'): BP = calc_extra_od(Decimal('-0.0125'), Decimal('-0.015'))
                elif F_freq == Decimal('49.96'): BP = calc_extra_od(Decimal('-0.012'), Decimal('-0.015'))
                elif F_freq == Decimal('49.97'): BP = calc_extra_od(Decimal('-0.0115'), Decimal('-0.015'))
                elif F_freq == Decimal('49.98'): BP = calc_extra_od(Decimal('-0.011'), Decimal('-0.015'))
                elif F_freq == Decimal('49.99'): BP = calc_extra_od(Decimal('-0.0105'), Decimal('-0.015'))
                elif F_freq == Decimal('50'): BP = calc_extra_od(Decimal('-0.01'), Decimal('-0.01'))
                elif F_freq == Decimal('50.01'): BP = calc_extra_od(Decimal('-0.0095'), Decimal('-0.01'))
                elif F_freq == Decimal('50.02'): BP = calc_extra_od(Decimal('-0.009'), Decimal('-0.01'))
                elif F_freq == Decimal('50.03'): BP = calc_extra_od(Decimal('-0.0085'), Decimal('-0.01'))
                elif F_freq == Decimal('50.04'): BP = calc_extra_od(Decimal('-0.008'), Decimal('-0.01'))
                elif F_freq == Decimal('50.05'): BP = calc_extra_od(Decimal('-0.0075'), Decimal('-0.01'))
                elif F_freq >= Decimal('50.1'):
                    BP = I * K_rate * 0
                elif Decimal('50.06') <= F_freq <= Decimal('50.09'):
                    BP = calc_extra_od(Decimal('-0.005'), Decimal('-0.0075'))

        res["OD_<=400_>20%_BP"] = BP

        # Total Over Drawal Charges (BR)
        # Formula: =-SUM(BA4:BP4)
        br_sum = BA + BB + BC + BD + BE + BF + BG + BH + BI + BJ + BK + BL + BM + BN + BO + BP
        res["Total over drawal charges"] = -br_sum

        return res

if __name__ == "__main__":
    # Quick test with sample data
    engine = DSMEngine()
    # Row 4 from Excel: C4=71.605, D4=74.0085, J4=50.01, K4=286.42
    # Note: Schedule MW = 71.605 * 4 = 286.42. Wait, E is S*4. 71.605*4 = 286.42
    # result = engine.calculate_row(71.605, 74.0085, 50.01, 286.42)
    result = engine.calculate_row(78.34, 58.33, 48.99, 282.42)
    print(json.dumps({k: str(v) for k, v in result.items()}, indent=4))
