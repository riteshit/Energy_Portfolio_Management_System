
import customtkinter as ctk
from decimal import Decimal
import dsm_engine
import dsm_rate_cerc_2024
import json

class DSMApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern DSM Calculator")
        self.geometry("1300x800")
        
        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2) # Wider results column
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.create_result_area()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="DSM Calc", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                               command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=20)
        
        # --- TITLE ---
        self.label_title = ctk.CTkLabel(self.main_frame, text="DSM Calculation Parameters", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # --- INPUTS ---
        # Schedule (MW)
        self.schedule_label = ctk.CTkLabel(self.main_frame, text="Schedule (MW):")
        self.schedule_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.schedule_entry = ctk.CTkEntry(self.main_frame, placeholder_text="71.605")
        self.schedule_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Actual (MW)
        self.actual_label = ctk.CTkLabel(self.main_frame, text="Actual (MW):")
        self.actual_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.actual_entry = ctk.CTkEntry(self.main_frame, placeholder_text="74.0085")
        self.actual_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Frequency (Hz)
        self.freq_label = ctk.CTkLabel(self.main_frame, text="Frequency (Hz):")
        self.freq_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.freq_entry = ctk.CTkEntry(self.main_frame, placeholder_text="50.01")
        self.freq_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # --- RATE PARAMETERS ---
        self.rate_title = ctk.CTkLabel(self.main_frame, text="Rate Parameters", font=ctk.CTkFont(size=18, weight="bold"))
        self.rate_title.grid(row=4, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w")

        # Rate Mode Switch
        self.rate_mode_var = ctk.StringVar(value="Auto")
        self.rate_mode_switch = ctk.CTkSwitch(self.main_frame, text="Manual Rate Mode", variable=self.rate_mode_var, onvalue="Manual", offvalue="Auto", command=self.toggle_rate_inputs)
        self.rate_mode_switch.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Manual Rate Entry (Initially hidden or disabled logic, but let's keep it visible)
        self.manual_rate_label = ctk.CTkLabel(self.main_frame, text="Manual Rate (Paise/kWh):")
        self.manual_rate_label.grid(row=6, column=0, padx=10, pady=5, sticky="e")
        self.manual_rate_entry = ctk.CTkEntry(self.main_frame, placeholder_text="0")
        self.manual_rate_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        
        # Auto Rate Inputs Frame (to toggle visibility)
        self.auto_rate_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.auto_rate_frame.grid(row=7, column=0, columnspan=2, sticky="nsew")

        # Entity Type
        self.entity_type_label = ctk.CTkLabel(self.auto_rate_frame, text="Entity Type:")
        self.entity_type_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.entity_type_option = ctk.CTkOptionMenu(self.auto_rate_frame, values=["Buyer", "General Seller", "WS Seller"])
        self.entity_type_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # ACP DAM
        self.acp_dam_label = ctk.CTkLabel(self.auto_rate_frame, text="ACP DAM (Paise/kWh):")
        self.acp_dam_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.acp_dam_entry = ctk.CTkEntry(self.auto_rate_frame, placeholder_text="300")
        self.acp_dam_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # ACP RTM
        self.acp_rtm_label = ctk.CTkLabel(self.auto_rate_frame, text="ACP RTM (Paise/kWh):")
        self.acp_rtm_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.acp_rtm_entry = ctk.CTkEntry(self.auto_rate_frame, placeholder_text="320")
        self.acp_rtm_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Ancillary Charge
        self.auc_label = ctk.CTkLabel(self.auto_rate_frame, text="Ancillary Charge:")
        self.auc_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.auc_entry = ctk.CTkEntry(self.auto_rate_frame, placeholder_text="0")
        self.auc_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Available Cap (for WS)
        self.avail_cap_label = ctk.CTkLabel(self.auto_rate_frame, text="Available Cap (MW):")
        self.avail_cap_label.grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.avail_cap_entry = ctk.CTkEntry(self.auto_rate_frame, placeholder_text="100")
        self.avail_cap_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Is Wind
        self.is_wind_var = ctk.StringVar(value="off")
        self.is_wind_check = ctk.CTkCheckBox(self.auto_rate_frame, text="Is Wind Generator?", variable=self.is_wind_var, onvalue="on", offvalue="off")
        self.is_wind_check.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Establish initial state
        self.toggle_rate_inputs()

        # --- CALCULATE BUTTON ---
        self.calculate_button = ctk.CTkButton(self.main_frame, text="Calculate DSM", command=self.calculate_event, font=ctk.CTkFont(size=16, weight="bold"))
        self.calculate_button.grid(row=8, column=0, columnspan=2, padx=10, pady=20)


    def create_result_area(self):
        # Create a container for the table
        self.result_container = ctk.CTkFrame(self)
        self.result_container.grid(row=0, column=2, rowspan=4, sticky="nsew", padx=(0, 20), pady=20)
        self.result_container.grid_columnconfigure(0, weight=1)
        self.result_container.grid_rowconfigure(1, weight=1) # Row 1 will contain the scrollable list

        # Table Headers
        self.headers_frame = ctk.CTkFrame(self.result_container, height=40, corner_radius=0)
        self.headers_frame.grid(row=0, column=0, sticky="ew")
        
        headers = ["Schedule", "Actual", "Freq", "Rate", "Net DSM"]
        self.header_labels = []
        for i, h in enumerate(headers):
            self.headers_frame.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(self.headers_frame, text=h, font=ctk.CTkFont(size=13, weight="bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5)
            self.header_labels.append(lbl)

        # Scrollable Area for Data Rows
        self.result_frame = ctk.CTkScrollableFrame(self.result_container, label_text=None)
        self.result_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure columns in result_frame to match headers
        for i in range(5):
            self.result_frame.grid_columnconfigure(i, weight=1)

        # Initial message
        self.no_data_label = ctk.CTkLabel(self.result_frame, text="Calculated results will appear here in a table.")
        self.no_data_label.grid(row=0, column=0, columnspan=5, pady=20)
        
        self.data_rows = [] # Keep track of rows

    def add_result_row(self, schedule, actual, freq, rate, net_dsm):
        # Remove "No Data" label if it exists
        if self.no_data_label:
            self.no_data_label.destroy()
            self.no_data_label = None

        row_idx = len(self.data_rows)
        
        # Format values
        vals = [
            f"{schedule:.2f}", 
            f"{actual:.2f}", 
            f"{freq:.2f}", 
            f"{rate:.2f}", 
            f"{net_dsm:.2f}"
        ]
        
        row_widgets = []
        for i, val in enumerate(vals):
            lbl = ctk.CTkLabel(self.result_frame, text=val)
            lbl.grid(row=row_idx, column=i, padx=5, pady=5)
            row_widgets.append(lbl)
            
        self.data_rows.append(row_widgets)

    def toggle_rate_inputs(self):
        mode = self.rate_mode_var.get()
        if mode == "Manual":
            self.manual_rate_entry.configure(state="normal")
            for child in self.auto_rate_frame.winfo_children():
                try:
                    child.configure(state="disabled")
                except: pass
        else:
            self.manual_rate_entry.configure(state="disabled")
            for child in self.auto_rate_frame.winfo_children():
                try:
                    child.configure(state="normal")
                except: pass

    def calculate_event(self):
        try:
            # 1. Get Inputs
            schedule_mw = float(self.schedule_entry.get() or 0)
            actual_mw = float(self.actual_entry.get() or 0)
            freq = float(self.freq_entry.get() or 50.0)
            
            rate_mode = self.rate_mode_var.get()
            computed_rate = 0
            
            if rate_mode == "Manual":
                computed_rate = float(self.manual_rate_entry.get() or 0)
            else:
                # Auto Mode
                entity_type = self.entity_type_option.get()
                acp_dam = float(self.acp_dam_entry.get() or 0)
                acp_rtm = float(self.acp_rtm_entry.get() or 0)
                ancillary = float(self.auc_entry.get() or 0)
                avail_cap = float(self.avail_cap_entry.get() or 0) if self.avail_cap_entry.get() else None
                is_wind = self.is_wind_var.get() == "on"
                
                nr = dsm_rate_cerc_2024.calculate_normal_rate(acp_dam, acp_rtm, ancillary)
                
                schedule_mwh = schedule_mw / 4
                actual_mwh = actual_mw / 4 
                deviation_mw = actual_mw - schedule_mw
                rr_or_contract = nr 
                
                computed_rate = dsm_rate_cerc_2024.get_dsm_rate(
                    entity_type=entity_type, 
                    freq=freq, 
                    nr=nr, 
                    rr_or_contract=rr_or_contract, 
                    deviation=deviation_mw, 
                    schedule_mwh=schedule_mwh, 
                    available_cap=avail_cap, 
                    is_wind=is_wind
                )

            # 3. Calculate DSM Charges
            schedule_mwh_final = Decimal(str(schedule_mw)) / 4
            actual_mwh_final = Decimal(str(actual_mw)) / 4
            
            engine = dsm_engine.DSMEngine()
            result = engine.calculate_row(
                schedule_mwh=schedule_mwh_final, 
                actual_mwh=actual_mwh_final, 
                frequency=Decimal(str(freq)), 
                rate=Decimal(str(computed_rate))
            )
            
            # --- NET DSM CALCULATION ---
            # Result contains "Total under drawal charges" and "Total over drawal charges"
            # Both are typically stored as negative numbers in the engine output (charges are negative flow?)
            # Or usually "Charges" implies payable.
            # Let's check engine. Calculate row returns:
            # res["Total under drawal charges"] = -bq_sum (bq_sum is positive calc)
            # res["Total over drawal charges"] = -br_sum
            # So they are negative.
            # Net DSM = Total Under + Total Over
            
            total_under = float(result.get("Total under drawal charges", 0))
            total_over = float(result.get("Total over drawal charges", 0))
            net_dsm = total_under + total_over
            
            # 4. Update Table
            self.add_result_row(schedule_mw, actual_mw, freq, float(computed_rate), net_dsm)
            
        except ValueError:
            pass # Handle better if needed, for now just ignore invalid inputs
        except Exception as e:
            print(f"Error: {e}")


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    app = DSMApp()
    app.mainloop()
