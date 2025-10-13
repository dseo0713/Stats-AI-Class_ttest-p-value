import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import scipy.stats as stats
import platform
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# Set matplotlib font for Korean
if platform.system() == "Windows":
    matplotlib.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    matplotlib.rcParams["font.family"] = "AppleGothic"
else:
    matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

class TTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("독립표본 t-검정 프로그램 (최종)")
        self.root.geometry("1000x800")
        
        # Data storage
        self.data = None
        self.x = None
        self.y = None
        self.g1 = None
        self.g2 = None
        
        # Options
        self.tail_var = tk.StringVar(value="양측(two-tailed)")
        self.alpha_var = tk.DoubleVar(value=0.05)
        self.show_plots_var = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
        # Load example data by default
        self.load_example_data()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="독립표본 t-검정 프로그램", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Data Upload Tab
        self.data_frame = ttk.Frame(notebook)
        notebook.add(self.data_frame, text="1) 데이터 업로드")
        self.create_data_tab()
        
        # Results Tab
        self.results_frame = ttk.Frame(notebook)
        notebook.add(self.results_frame, text="2) 검정 결과")
        self.create_results_tab()
        
        # Options Frame (Sidebar equivalent)
        self.create_options_frame()
    
    def create_options_frame(self):
        # Options frame on the right
        options_frame = ttk.LabelFrame(self.root, text="옵션")
        options_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=10)
        
        # Test direction
        ttk.Label(options_frame, text="검정 방향:").pack(anchor=tk.W, pady=(10, 5))
        ttk.Radiobutton(options_frame, text="양측(two-tailed)", variable=self.tail_var, 
                       value="양측(two-tailed)").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="단측(one-tailed, A > B)", variable=self.tail_var, 
                       value="단측(one-tailed, A > B)").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="단측(one-tailed, A < B)", variable=self.tail_var, 
                       value="단측(one-tailed, A < B)").pack(anchor=tk.W)
        
        # Alpha level
        ttk.Label(options_frame, text="유의수준 α:").pack(anchor=tk.W, pady=(20, 5))
        alpha_spinbox = ttk.Spinbox(options_frame, from_=0.001, to=0.5, increment=0.01, 
                                   textvariable=self.alpha_var, format="%.3f", width=10)
        alpha_spinbox.pack(anchor=tk.W)
        
        # Show plots checkbox
        ttk.Checkbutton(options_frame, text="요약 그래프 표시", variable=self.show_plots_var).pack(anchor=tk.W, pady=(20, 5))
        
        # Update button
        update_btn = ttk.Button(options_frame, text="결과 업데이트", command=self.update_results)
        update_btn.pack(pady=20)
    
    def create_data_tab(self):
        # File upload section
        upload_frame = ttk.LabelFrame(self.data_frame, text="파일 업로드")
        upload_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(upload_frame, text="CSV 또는 Excel 파일 선택", 
                  command=self.load_file).pack(pady=10)
        
        ttk.Button(upload_frame, text="예시 데이터 사용", 
                  command=self.load_example_data).pack(pady=5)
        
        # Data preview
        self.data_text = tk.Text(self.data_frame, height=15, width=80)
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar for data text
        scrollbar = ttk.Scrollbar(self.data_frame, orient=tk.VERTICAL, command=self.data_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_text.configure(yscrollcommand=scrollbar.set)
    
    def create_results_tab(self):
        # Results text area
        self.results_text = tk.Text(self.results_frame, height=20, width=80)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar for results text
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Plot frame
        self.plot_frame = ttk.Frame(self.results_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="데이터 파일 선택",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.csv'):
                    self.data = pd.read_csv(file_path)
                else:
                    # For Excel files, read the first sheet
                    self.data = pd.read_excel(file_path, sheet_name=0)
                
                self.process_data()
                self.display_data()
                self.update_results()
                
            except Exception as e:
                messagebox.showerror("오류", f"파일을 읽는 중 오류가 발생했습니다: {e}")
    
    def load_example_data(self):
        self.data = pd.DataFrame({
            "group": ["남자"]*7 + ["여자"]*6,
            "value": [78,67,97,87,78,76,79, 56,76,56,45,65,55]
        })
        self.process_data()
        self.display_data()
        self.update_results()
    
    def process_data(self):
        if self.data is None:
            return
        
        # Check for required columns
        cols = list(self.data.columns)
        if not {"group", "value"}.issubset(cols):
            # Try to map columns
            if len(cols) >= 2:
                self.data = self.data.rename(columns={cols[0]: "group", cols[1]: "value"})
            else:
                messagebox.showerror("오류", "데이터에 최소 2개의 열이 필요합니다.")
                return
        
        # Clean data
        self.data = self.data.dropna(subset=["group", "value"])
        try:
            self.data["value"] = pd.to_numeric(self.data["value"])
        except Exception:
            messagebox.showerror("오류", "값(value) 열은 숫자여야 합니다.")
            return
        
        # Check for exactly 2 groups
        groups = self.data["group"].unique()
        if len(groups) != 2:
            messagebox.showerror("오류", f"두 개의 집단만 필요합니다. 현재 집단: {list(groups)}")
            return
        
        self.g1, self.g2 = groups[0], groups[1]
        self.x = self.data.loc[self.data["group"] == self.g1, "value"].to_numpy(dtype=float)
        self.y = self.data.loc[self.data["group"] == self.g2, "value"].to_numpy(dtype=float)
    
    def display_data(self):
        if self.data is None:
            return
        
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(tk.END, "데이터 미리보기:\n\n")
        self.data_text.insert(tk.END, str(self.data))
        self.data_text.insert(tk.END, f"\n\n집단 1 ({self.g1}): {len(self.x)}개 사례")
        self.data_text.insert(tk.END, f"\n집단 2 ({self.g2}): {len(self.y)}개 사례")
    
    def descriptives(self, arr):
        n = len(arr)
        mean = float(np.mean(arr)) if n > 0 else np.nan
        sd = float(np.std(arr, ddof=1)) if n > 1 else np.nan
        var = float(np.var(arr, ddof=1)) if n > 1 else np.nan
        return n, mean, sd, var
    
    def update_results(self):
        if self.data is None or self.x is None or self.y is None:
            return
        
        self.results_text.delete(1.0, tk.END)
        
        # Descriptives
        n1, m1, sd1, var1 = self.descriptives(self.x)
        n2, m2, sd2, var2 = self.descriptives(self.y)
        
        self.results_text.insert(tk.END, "2) 기술통계\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        self.results_text.insert(tk.END, f"{'집단':<10} {'사례수(n)':<10} {'평균':<10} {'표준편차':<10} {'분산':<10}\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n")
        self.results_text.insert(tk.END, f"{self.g1:<10} {n1:<10} {m1:<10.2f} {sd1:<10.2f} {var1:<10.2f}\n")
        self.results_text.insert(tk.END, f"{self.g2:<10} {n2:<10} {m2:<10.2f} {sd2:<10.2f} {var2:<10.2f}\n\n")
        
        # t-test
        self.results_text.insert(tk.END, "3) 검정 결과\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        
        equal_var = True
        tstat, p_two = stats.ttest_ind(self.x, self.y, equal_var=equal_var, alternative="two-sided")
        
        tail = self.tail_var.get()
        if "단측" in tail:
            if "A > B" in tail:
                p_val = p_two/2.0 if tstat > 0 else 1 - (p_two/2.0)
            else:
                p_val = p_two/2.0 if tstat < 0 else 1 - (p_two/2.0)
        else:
            p_val = p_two
        
        df = n1 + n2 - 2
        mean_diff = m1 - m2
        sp2 = ((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2) if df > 0 else np.nan
        se1 = np.sqrt(var1/n1)
        se2 = np.sqrt(var2/n2)
        se_diff = np.sqrt(sp2*(1/n1 + 1/n2)) if df > 0 else np.nan
        
        alpha = self.alpha_var.get()
        tcrit = stats.t.ppf(1 - alpha/2, df) if "양측" in tail else stats.t.ppf(1 - alpha, df)
        ci_low = mean_diff - tcrit*se_diff
        ci_high = mean_diff + tcrit*se_diff
        
        self.results_text.insert(tk.END, f"t 통계량: {tstat:.4f}\n")
        self.results_text.insert(tk.END, f"자유도 df: {df:.2f}\n")
        self.results_text.insert(tk.END, f"p 값: {p_val:.4f}\n")
        self.results_text.insert(tk.END, f"평균차 (A-B): {mean_diff:.2f}\n")
        self.results_text.insert(tk.END, f"신뢰구간 (95%): [{ci_low:.2f}, {ci_high:.2f}]\n\n")
        
        decision = "유의함(H0 기각)" if p_val < alpha else "유의하지 않음(H0 기각 불가)"
        self.results_text.insert(tk.END, f"결론: {decision} (α={alpha}, p={p_val:.4f})\n\n")
        
        # Narrative
        self.results_text.insert(tk.END, "4) 해석(리포트 문장)\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        
        if "양측" in tail:
            tail_txt = "양측검정"
        elif "A > B" in tail:
            tail_txt = "단측검정(H1: A>B)"
        else:
            tail_txt = "단측검정(H1: A<B)"
        
        report = (f"{tail_txt} 기준으로 {self.g1}의 평균({m1:.2f})과 {self.g2}의 평균({m2:.2f})을 비교한 결과, "
                f"t={tstat:.2f}, df={df:.0f}, p={p_val:.4f}로 "
                f"{'통계적으로 유의한 차이가 있었다' if p_val < alpha else '유의한 차이가 없었다'}. "
                f"평균차({self.g1}-{self.g2})={mean_diff:.2f}, 95% CI [{ci_low:.2f}, {ci_high:.2f}] 입니다.")
        
        # Insert narrative with formatting
        start_pos = self.results_text.index(tk.END + "-1c")
        self.results_text.insert(tk.END, report + "\n")
        end_pos = self.results_text.index(tk.END + "-1c")
        
        # Apply bold and red formatting to the narrative
        self.results_text.tag_add("narrative", start_pos, end_pos)
        self.results_text.tag_configure("narrative", font=("Arial", 10, "bold"), foreground="red")
        
        # Plot
        if self.show_plots_var.get():
            self.create_plot()
    
    def create_plot(self):
        # Clear previous plot
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        if self.x is None or self.y is None:
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        n1, m1, sd1, var1 = self.descriptives(self.x)
        n2, m2, sd2, var2 = self.descriptives(self.y)
        
        alpha = self.alpha_var.get()
        tail = self.tail_var.get()
        df = n1 + n2 - 2
        tcrit = stats.t.ppf(1 - alpha/2, df) if "양측" in tail else stats.t.ppf(1 - alpha, df)
        
        se1 = np.sqrt(var1/n1)
        se2 = np.sqrt(var2/n2)
        
        ax.bar([self.g1, self.g2], [m1, m2], width=0.2)
        ax.errorbar([self.g1, self.g2], [m1, m2], yerr=[tcrit*se1, tcrit*se2], fmt='none', capsize=6)
        ax.set_ylabel("값(평균)")
        ax.set_title("평균 ± 신뢰구간(95%)")
        
        # Embed plot in tkinter
        canvas = FigureCanvasTkAgg(fig, self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = TTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
