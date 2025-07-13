import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

# Arabic supplier names mapped to letters
SUPPLIER_MAP = {
    'A': 'المخزن',
    'B': 'الوكاله للسيارات',
    'C': 'رواسي',
    'D': 'نجم الرمال',
    'E': 'الغفيلي',
    'F': 'الشرق',
    'G': 'ركن الراقي',
    'H': 'توكيلات الجزيره',
    'I': 'المهري',
    'J': 'بيت التزامن',
    'K': 'الوان العربه',
    'L': 'ساماكو',
    'M': 'تشليح الحائر',
    'N': 'الحاج حسين',
    'O': 'المغلوث',
    'P': 'اهل الخبرة',
    'Q': 'اوتوبانوراما',
    'R': 'شمس الاصناف',
    'S': 'ضياء البشائر',
    'T': 'مصدر الزيوت',
    'U': 'الإطار الكبير',
    'V': 'الوعلان',
    'W': 'رينيو(وكيل رينيو السابق)',
    'X': 'امبوبه',
    'Y': 'العمودي',
    'Z': 'منيف النهدي',
    'AA': 'القحطاني',
    'AB': 'الناغي',
    'AC': 'نجمة نيسان',
    'AD': 'ابداع الشبكة'
}

class SupplyChainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام مقارنة طرق سلاسل الإمداد")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.distance_matrix = None
        self.selected_suppliers = ['A']  # Always include warehouse 'A'
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        # Main container with scrollable capability
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg='#f0f0f0')
        header_frame.pack(pady=(0, 20), fill="x")
        
        tk.Label(header_frame, text="نظام مقارنة طرق سلاسل الإمداد", 
                font=('Arial', 18, 'bold'), bg='#f0f0f0').pack()
        
        tk.Label(header_frame, text="مشروع التخرج - تحسين سلاسل الإمداد لقطع الغيار", 
                font=('Arial', 12), bg='#f0f0f0').pack()
        
        # File Selection Frame
        file_frame = tk.LabelFrame(main_container, text="مادة البيانات للمسافات", 
                                 font=('Arial', 10, 'bold'), bg='#f0f0f0')
        file_frame.pack(pady=(0, 10), fill="x")
        
        # File path entry and buttons
        file_inner_frame = tk.Frame(file_frame, bg='#f0f0f0')
        file_inner_frame.pack(fill="x", padx=10, pady=10)
        
        self.file_path = tk.StringVar()
        tk.Entry(file_inner_frame, textvariable=self.file_path, width=50, 
                font=('Arial', 10), bd=2, relief=tk.GROOVE).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_frame = tk.Frame(file_inner_frame, bg='#f0f0f0')
        btn_frame.pack(side="right")
        
        # Modern styled buttons
        self.create_button(btn_frame, "استعراض", self.browse_file, '#2196F3', '#0b7dda').pack(side="left", padx=(0, 5))
        self.create_button(btn_frame, "تحميل البيانات", self.load_data, '#4CAF50', '#45a049').pack(side="left")
        
        # Content Frame (for supplier selection and results)
        content_frame = tk.Frame(main_container, bg='#f0f0f0')
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Left Panel - Supplier Selection
        left_panel = tk.Frame(content_frame, bg='#f0f0f0')
        left_panel.pack(side="left", fill="both", expand=False, padx=(0, 10))
        
        supplier_frame = tk.LabelFrame(left_panel, text="اختيار الموردين", 
                                    font=('Arial', 10, 'bold'), bg='#f0f0f0')
        supplier_frame.pack(fill="both", expand=True)
        
        # Supplier Listbox with Scrollbar
        listbox_frame = tk.Frame(supplier_frame, bg='#f0f0f0')
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.supplier_listbox = tk.Listbox(listbox_frame, selectmode="multiple", 
                                          height=15, width=40, font=('Arial', 10), bd=2, relief=tk.GROOVE)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.supplier_listbox.yview)
        self.supplier_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate listbox with suppliers (excluding warehouse 'A')
        for code, name in sorted(SUPPLIER_MAP.items()):
            if code != 'A':
                self.supplier_listbox.insert(tk.END, f"{code}: {name}")
        
        self.supplier_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Selection Buttons
        selection_btn_frame = tk.Frame(supplier_frame, bg='#f0f0f0')
        selection_btn_frame.pack(pady=10)
        
        self.create_button(selection_btn_frame, "تحديد الكل", self.select_all, '#607D8B', '#546E7A').pack(side="left", padx=5)
        self.create_button(selection_btn_frame, "إلغاء التحديد", self.deselect_all, '#f44336', '#d32f2f').pack(side="left", padx=5)
        
        # Right Panel - Results
        right_panel = tk.Frame(content_frame, bg='#f0f0f0')
        right_panel.pack(side="right", fill="both", expand=True)
        
        results_frame = tk.LabelFrame(right_panel, text="النتائج", 
                                    font=('Arial', 10, 'bold'), bg='#f0f0f0')
        results_frame.pack(fill="both", expand=True)
        
        # Results text area
        results_inner_frame = tk.Frame(results_frame, bg='#f0f0f0')
        results_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.results_text = tk.Text(results_inner_frame, wrap="word", 
                                  font=('Arial', 10), bd=2, relief=tk.GROOVE)
        results_scrollbar = ttk.Scrollbar(results_inner_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")
        
        # Action Buttons Frame - Fixed at bottom
        action_frame = tk.Frame(main_container, bg='#f0f0f0')
        action_frame.pack(pady=20, fill="x")
        
        # Center the buttons
        button_container = tk.Frame(action_frame, bg='#f0f0f0')
        button_container.pack()
        
        self.create_button(button_container, "عرض النتائج", self.compare_methods, '#9C27B0', '#7B1FA2').pack(side="left", padx=10)
        self.create_button(button_container, "مسح النتائج", self.clear_results, '#FF9800', '#F57C00').pack(side="left", padx=10)
        self.create_button(button_container, "خروج", self.root.quit, '#607D8B', '#546E7A').pack(side="left", padx=10)
    
    def create_button(self, parent, text, command, bg_color, hover_color):
        btn = tk.Button(parent, text=text, command=command, 
                       font=('Arial', 10, 'bold'), fg='white', bg=bg_color,
                       activebackground=hover_color, bd=0, padx=20, pady=8,
                       relief=tk.RAISED, cursor="hand2")
        
        # Add hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
        
        return btn
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path.set(file_path)
    
    def load_data(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showerror("خطأ", "يرجى تحديد ملف الإكسل أولاً")
            return
        
        try:
            self.distance_matrix = self.read_distance_matrix_from_excel(file_path)
            messagebox.showinfo("نجاح", "تم تحميل البيانات بنجاح")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في قراءة البيانات من ملف الإكسل: {e}")
    
    def read_distance_matrix_from_excel(self, file_path, sheet_name=0):
        """Reads distance matrix from Excel file"""
        df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0, engine='openpyxl')
        
        # Get column names and index names (should be supplier codes)
        columns = df.columns.tolist()
        indices = df.index.tolist()
        
        # Convert to dictionary format using the actual column/index names
        distance_matrix = {}
        
        for i, from_supplier in enumerate(indices):
            from_supplier_str = str(from_supplier).strip().upper()
            distance_matrix[from_supplier_str] = {}
            
            for j, to_supplier in enumerate(columns):
                to_supplier_str = str(to_supplier).strip().upper()
                distance_matrix[from_supplier_str][to_supplier_str] = df.iloc[i, j]
        
        return distance_matrix
    
    def select_all(self):
        self.supplier_listbox.selection_set(0, tk.END)
    
    def deselect_all(self):
        self.supplier_listbox.selection_clear(0, tk.END)
    
    def get_selected_suppliers(self):
        selected_indices = self.supplier_listbox.curselection()
        selected_suppliers = ['A']  # Always include warehouse 'A'
        
        for index in selected_indices:
            item = self.supplier_listbox.get(index)
            code = item.split(":")[0].strip()
            selected_suppliers.append(code)
        
        return list(set(selected_suppliers))  # Remove duplicates
    
    def compare_methods(self):
        if not self.distance_matrix:
            messagebox.showerror("خطأ", "يرجى تحميل بيانات المسافات أولاً")
            return
        
        selected_suppliers = self.get_selected_suppliers()
        if len(selected_suppliers) < 2:
            messagebox.showerror("خطأ", "يرجى اختيار مورد واحد على الأقل بالإضافة للمخزن")
            return
        
        # Validate that selected suppliers exist in distance matrix
        missing_suppliers = [s for s in selected_suppliers if s not in self.distance_matrix]
        if missing_suppliers:
            messagebox.showerror("خطأ", f"الموردين التالية غير موجودة في ملف الإكسل: {', '.join(missing_suppliers)}")
            return
        
        self.results_text.delete(1.0, tk.END)
        
        # Method 1: Company car visits all suppliers (TSP)
        route, company_distance = self.solve_tsp_for_suppliers(selected_suppliers)
        
        if route:
            # Ensure route starts and ends with 'A' (warehouse)
            if route[0] != 'A':
                # Rotate route so it starts with 'A'
                idx = route.index('A')
                route = route[idx:] + route[:idx]
            if route[-1] != 'A':
                route.append('A')  # Explicitly close the cycle for display
            route_names = [SUPPLIER_MAP[letter] for letter in route]
            self.results_text.insert(tk.END, "🚛 الطريقة الأولى: سيارة الشركة تمر بجميع الموردين\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n")
            self.results_text.insert(tk.END, "المسار الأمثل:\n")
            # Display ranked suppliers
            for i, name in enumerate(route_names, 1):
                self.results_text.insert(tk.END, f"{i}. {name}\n")
            self.results_text.insert(tk.END, f"\nإجمالي المسافة: {company_distance:.1f} كم\n\n")
        else:
            self.results_text.insert(tk.END, "لم يتم العثور على حل للمسار الأمثل\n")
            return
        
        # Method 2: Each supplier ships individually
        individual_distance, shipping_details = self.calculate_individual_shipping_distance(selected_suppliers)
        
        self.results_text.insert(tk.END, "📦 الطريقة الثانية: كل مورد يرسل بشكل منفصل\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n")
        
        for detail in shipping_details:
            self.results_text.insert(tk.END, f"{detail['supplier_name']}: {detail['distance']:.1f} كم\n")
        
        self.results_text.insert(tk.END, f"\nإجمالي المسافة: {individual_distance:.1f} كم\n\n")
        
        # Comparison and Recommendation
        savings = individual_distance - company_distance
        savings_percentage = (savings / individual_distance) * 100 if individual_distance > 0 else 0
        
        self.results_text.insert(tk.END, "📊 المقارنة والتوصية\n")
        self.results_text.insert(tk.END, "=" * 30 + "\n")
        self.results_text.insert(tk.END, f"مسافة سيارة الشركة: {company_distance:.1f} كم\n")
        self.results_text.insert(tk.END, f"مسافة الشحن المنفصل: {individual_distance:.1f} كم\n")
        self.results_text.insert(tk.END, f"الفرق في المسافة: {abs(savings):.1f} كم\n")
        self.results_text.insert(tk.END, f"نسبة التوفير: {abs(savings_percentage):.1f}%\n\n")
        
        self.results_text.insert(tk.END, "🎯 التوصية:\n")
        if savings > 0:
            self.results_text.insert(tk.END, f"✅ استخدم سيارة الشركة - توفير {savings:.1f} كم ({savings_percentage:.1f}%)\n")
            self.results_text.insert(tk.END, "   السبب: المسار الأمثل أقصر من الشحن المنفصل\n")
        elif savings < 0:
            self.results_text.insert(tk.END, f"✅ استخدم الشحن المنفصل - توفير {abs(savings):.1f} كم ({abs(savings_percentage):.1f}%)\n")
            self.results_text.insert(tk.END, "   السبب: الشحن المنفصل أقصر من المسار الأمثل\n")
        else:
            self.results_text.insert(tk.END, "⚖️ التكلفة متساوية - اختر حسب العوامل الأخرى\n")
    
    def solve_tsp_for_suppliers(self, supplier_letters):
        """Solves TSP for selected suppliers using Gurobi"""
        try:
            model = gp.Model("Supplier_TSP")
            model.setParam('OutputFlag', 0)  # Suppress Gurobi output
            
            edges = [(i, j) for i in supplier_letters for j in supplier_letters if i != j]
            x = model.addVars(edges, vtype=GRB.BINARY, name="x")
            u = model.addVars(supplier_letters, vtype=GRB.CONTINUOUS, name="u")
            n = len(supplier_letters)
            
            # Each node has exactly one outgoing and one incoming edge
            model.addConstrs((gp.quicksum(x[i,j] for j in supplier_letters if i != j) == 1 for i in supplier_letters), name="outgoing")
            model.addConstrs((gp.quicksum(x[j,i] for j in supplier_letters if i != j) == 1 for i in supplier_letters), name="incoming")
            
            # Subtour elimination constraints (Miller-Tucker-Zemlin)
            for i in supplier_letters:
                for j in supplier_letters:
                    if i != j and i != supplier_letters[0] and j != supplier_letters[0]:
                        model.addConstr(u[i] - u[j] + (n-1)*x[i,j] <= n-2, name=f"subtour_{i}_{j}")
            
            # Set bounds for u variables
            for i in supplier_letters[1:]:
                u[i].LB = 1
                u[i].UB = n-1
            
            # Force the route to start and end with 'A'
            model.addConstr(gp.quicksum(x['A',j] for j in supplier_letters if j != 'A') == 1, name="start_at_A")
            model.addConstr(gp.quicksum(x[i,'A'] for i in supplier_letters if i != 'A') == 1, name="end_at_A")
            
            # Objective: minimize total distance
            model.setObjective(gp.quicksum(x[i,j]*self.distance_matrix[i][j] for i,j in edges), GRB.MINIMIZE)
            model.optimize()
            
            if model.status == GRB.OPTIMAL:
                # Reconstruct the route
                solution = []
                remaining = set(supplier_letters)
                current = 'A'  # Start from warehouse (A)
                solution.append(current)
                remaining.remove(current)
                
                while remaining:
                    for j in supplier_letters:
                        if j in remaining and x[current,j].x > 0.5:
                            current = j
                            solution.append(current)
                            remaining.remove(current)
                            break
                
                # Ensure the route ends at 'A'
                if solution[-1] != 'A':
                    solution.append('A')
                
                # Calculate total distance
                total_dist = sum(self.distance_matrix[solution[i]][solution[i+1]] for i in range(len(solution)-1))
                return solution, total_dist
            else:
                return None, None
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حل مسألة التوجيه: {e}")
            return None, None
    
    def calculate_individual_shipping_distance(self, supplier_letters, warehouse='A'):
        """Calculate total distance if each supplier ships individually to warehouse"""
        total_distance = 0
        shipping_details = []
        
        for supplier in supplier_letters:
            if supplier != warehouse:  # Don't count warehouse to itself
                distance = self.distance_matrix[supplier][warehouse]
                total_distance += distance
                shipping_details.append({
                    'supplier': supplier,
                    'supplier_name': SUPPLIER_MAP[supplier],
                    'distance': distance
                })
        
        return total_distance, shipping_details
    
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SupplyChainApp(root)
    root.mainloop()