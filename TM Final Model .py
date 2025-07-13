import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from PIL import Image, ImageTk

# Constants
EXCEL_FILE_PATH = "E:\\distances.xlsx"  # Fixed path for distance data

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

# Shipping types and costs
SHIPPING_TYPES = {
    'CARTON': {'name': 'كرتون (15 كج)', 'cost': 20},
    'PALLET': {'name': 'طلبية (500 كج)', 'cost': 220},
    'CARDOOR': {'name': 'قطع سيارات كبيرة', 'cost': 40}
}

VAT_RATE = 0.15  # 15% VAT

class SupplyChainApp:
    def __init__(self, root):
        self.root = root
        # Color palette from logo
        self.primary_color = "#FF0000"   # Red
        self.secondary_color = "#000000" # Black
        self.bg_color = "#FFFFFF"        # White
        self.accent_color = "#F5F5F5"    # Light gray
        
        self.root.title("نظام مقارنة تكلفة سلاسل الإمداد")
        self.root.geometry("1300x900")
        self.root.minsize(1000, 800)
        self.root.configure(bg=self.bg_color)
        
        # Main container
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill="both", expand=True)
        
        # Variables
        self.distance_matrix = None
        self.selected_suppliers = ['A']  # Always include warehouse 'A'
        
        # Updated cost parameters - removed shipping cost
        self.fixed_vehicle_cost_per_km = 0.22  # SAR/km (depreciation + insurance + tires)
        self.driver_cost_per_day = 192.31      # SAR/day (from 5,000 SAR/month)
        
        # Add shipping type tracking
        self.supplier_rows = []  # Will store the supplier selection rows
        self.supplier_shipping_types = {}
        
        # Load distance data on startup
        try:
            self.distance_matrix = self.read_distance_matrix_from_excel(EXCEL_FILE_PATH)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في قراءة البيانات من ملف الإكسل: {e}")
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        main_container = tk.Frame(self.main_container, bg=self.bg_color)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(pady=(0, 20), fill="x")
        
        tk.Label(header_frame, text="نظام مقارنة تكلفة سلاسل الإمداد", 
                font=('Arial', 18, 'bold'), bg=self.bg_color, fg=self.primary_color).pack()
        
        tk.Label(header_frame, text="مشروع التخرج - تحسين التكلفة لسلاسل الإمداد لقطع الغيار", 
                font=('Arial', 12), bg=self.bg_color, fg=self.secondary_color).pack()
        
        # Cost Parameters Frame
        cost_frame = tk.LabelFrame(main_container, text="معاملات التكلفة", 
                                 font=('Arial', 10, 'bold'), bg=self.bg_color, fg=self.primary_color)
        cost_frame.pack(pady=(0, 10), fill="x")
        
        cost_inner_frame = tk.Frame(cost_frame, bg=self.bg_color)
        cost_inner_frame.pack(fill="x", padx=10, pady=10)
        
        cost_grid = tk.Frame(cost_inner_frame, bg=self.bg_color)
        cost_grid.pack(fill="x")
        
        tk.Label(cost_grid, text="التكلفة الثابتة للسيارة (ريال/كم):", font=('Arial', 10), bg=self.bg_color, fg=self.secondary_color).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.fixed_vehicle_cost_var = tk.DoubleVar(value=self.fixed_vehicle_cost_per_km)
        tk.Entry(cost_grid, textvariable=self.fixed_vehicle_cost_var, width=10, font=('Arial', 10), bg=self.accent_color, fg=self.secondary_color).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(cost_grid, text="راتب السائق (ريال/يوم):", font=('Arial', 10), bg=self.bg_color, fg=self.secondary_color).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.driver_cost_var = tk.DoubleVar(value=self.driver_cost_per_day)
        tk.Entry(cost_grid, textvariable=self.driver_cost_var, width=10, font=('Arial', 10), bg=self.accent_color, fg=self.secondary_color).grid(row=0, column=3, padx=5, pady=2)

        # Split Screen Container
        split_container = tk.Frame(main_container, bg=self.bg_color)
        split_container.pack(fill="both", expand=True, pady=(0, 10))
        
        # Left Panel - Supplier Selection
        left_panel = tk.Frame(split_container, bg=self.bg_color)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Supplier Selection TreeView
        supplier_frame = tk.LabelFrame(left_panel, text="اختيار الموردين ونوع الشحن", 
                                     font=('Arial', 10, 'bold'), bg=self.bg_color, fg=self.primary_color)
        supplier_frame.pack(fill="both", expand=True)

        # Create TreeView
        self.tree = ttk.Treeview(supplier_frame, columns=('code', 'name', 'shipping', 'quantity'), show='headings')
        self.tree.heading('code', text='الرمز')
        self.tree.heading('name', text='اسم المورد')
        self.tree.heading('shipping', text='نوع الشحن')
        self.tree.heading('quantity', text='الكمية')
        self.tree.column('code', width=70, anchor='center')
        self.tree.column('name', width=200)
        self.tree.column('shipping', width=150)
        self.tree.column('quantity', width=80, anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(supplier_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack TreeView and scrollbar
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        # Control Panel for TreeView
        control_frame = tk.Frame(supplier_frame, bg=self.bg_color)
        control_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Supplier Selection
        supplier_select_frame = tk.Frame(control_frame, bg=self.bg_color)
        supplier_select_frame.pack(fill="x", pady=5)

        tk.Label(supplier_select_frame, text="المورد:", bg=self.bg_color, font=('Arial', 10)).pack(side="left", padx=5)
        self.supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(supplier_select_frame, textvariable=self.supplier_var,
                                    values=[f"{code}: {name}" for code, name in sorted(SUPPLIER_MAP.items()) if code != 'A'],
                                    width=30, state="readonly", font=('Arial', 10))
        supplier_combo.pack(side="left", padx=5)

        # Shipping Type Selection
        shipping_select_frame = tk.Frame(control_frame, bg=self.bg_color)
        shipping_select_frame.pack(fill="x", pady=5)

        tk.Label(shipping_select_frame, text="نوع الشحن:", bg=self.bg_color, font=('Arial', 10)).pack(side="left", padx=5)
        self.shipping_var = tk.StringVar()
        shipping_combo = ttk.Combobox(shipping_select_frame, textvariable=self.shipping_var,
                                    values=[info['name'] for info in SHIPPING_TYPES.values()],
                                    width=30, state="readonly", font=('Arial', 10))
        shipping_combo.pack(side="left", padx=5)

        # Quantity Selection
        quantity_select_frame = tk.Frame(control_frame, bg=self.bg_color)
        quantity_select_frame.pack(fill="x", pady=5)
        tk.Label(quantity_select_frame, text="الكمية:", bg=self.bg_color, font=('Arial', 10)).pack(side="left", padx=5)
        self.quantity_var = tk.IntVar(value=1)
        quantity_spin = tk.Spinbox(quantity_select_frame, from_=1, to=100, textvariable=self.quantity_var, width=10, font=('Arial', 10))
        quantity_spin.pack(side="left", padx=5)

        # Buttons Frame
        buttons_frame = tk.Frame(control_frame, bg=self.bg_color)
        buttons_frame.pack(fill="x", pady=5)

        add_btn = self.create_button(buttons_frame, "إضافة مورد", self.add_supplier_to_tree, bg_color=self.primary_color, hover_color="#b71c1c", font_size=10)
        add_btn.pack(side="left", padx=5)
        remove_btn = self.create_button(buttons_frame, "حذف المحدد", self.remove_selected_supplier, bg_color="#f44336", hover_color="#d32f2f", font_size=10)
        remove_btn.pack(side="left", padx=5)
        clear_btn = self.create_button(buttons_frame, "مسح الكل", self.clear_suppliers, bg_color="#607D8B", hover_color="#546E7A", font_size=10)
        clear_btn.pack(side="left", padx=5)

        # Right Panel - Results
        right_panel = tk.Frame(split_container, bg=self.bg_color)
        right_panel.pack(side="right", fill="both", expand=True)
        
        results_frame = tk.LabelFrame(right_panel, text="النتائج", 
                                    font=('Arial', 10, 'bold'), bg=self.bg_color, fg=self.primary_color)
        results_frame.pack(fill="both", expand=True)
        
        results_inner_frame = tk.Frame(results_frame, bg=self.bg_color)
        results_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.results_text = tk.Text(results_inner_frame, wrap="word", 
                                  font=('Arial', 10), bd=2, relief=tk.GROOVE, bg=self.accent_color, fg=self.secondary_color)
        results_scrollbar = ttk.Scrollbar(results_inner_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")
        
        # Action Buttons Frame - Fixed at bottom
        action_frame = tk.Frame(main_container, bg=self.bg_color)
        action_frame.pack(pady=20, fill="x")
        
        button_container = tk.Frame(action_frame, bg=self.bg_color)
        button_container.pack()
        
        compare_btn = self.create_button(button_container, "عرض النتائج والتكلفة", self.compare_methods, bg_color=self.primary_color, hover_color="#b71c1c", font_size=10)
        compare_btn.pack(side="left", padx=10)
        clear_btn = self.create_button(button_container, "مسح النتائج", self.clear_results, bg_color="#f44336", hover_color="#d32f2f", font_size=10)
        clear_btn.pack(side="left", padx=10)
        exit_btn = self.create_button(button_container, "خروج", self.root.quit, bg_color="#607D8B", hover_color="#546E7A", font_size=10)
        exit_btn.pack(side="left", padx=10)

    def create_button(self, parent, text, command, bg_color=None, hover_color=None, font_size=10, pad_x=20, pad_y=8):
        btn = tk.Button(parent, text=text, command=command, 
                       font=('Arial', font_size, 'bold'), fg='white', bg=bg_color or self.primary_color,
                       activebackground=hover_color or self.primary_color, bd=0, padx=pad_x, pady=pad_y,
                       relief=tk.RAISED, cursor="hand2")
        if hover_color:
            btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg_color or self.primary_color))
        return btn

    def add_supplier_to_tree(self):
        supplier_text = self.supplier_var.get()
        shipping_text = self.shipping_var.get()
        quantity = self.quantity_var.get()
        if not supplier_text or not shipping_text or quantity < 1:
            messagebox.showerror("خطأ", "يرجى اختيار المورد ونوع الشحن وتحديد الكمية")
            return
        supplier_code = supplier_text.split(':')[0].strip()
        supplier_name = SUPPLIER_MAP[supplier_code]
        # Check if supplier exists with same shipping type
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values[0] == supplier_code and values[2] == shipping_text:
                messagebox.showerror("خطأ", "هذا المورد موجود بالفعل مع نفس نوع الشحن")
                return
        self.tree.insert('', 'end', values=(supplier_code, supplier_name, shipping_text, quantity))
        # Clear selection
        self.supplier_var.set('')
        self.shipping_var.set('')
        self.quantity_var.set(1)

    def remove_selected_supplier(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("تنبيه", "يرجى تحديد مورد للحذف")
            return
        
        for item in selected_items:
            self.tree.delete(item)

    def clear_suppliers(self):
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الموردين؟"):
            for item in self.tree.get_children():
                self.tree.delete(item)

    def get_selected_suppliers(self):
        selected = ['A']  # Always include warehouse
        self.supplier_shipping_types = {}  # Reset the dictionary
        supplier_shipping_dict = {}
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            supplier_code = values[0]
            shipping_text = values[2]
            quantity = int(values[3])
            shipping_type = next(key for key, info in SHIPPING_TYPES.items() if info['name'] == shipping_text)
            if supplier_code not in selected:
                selected.append(supplier_code)
            if supplier_code not in supplier_shipping_dict:
                supplier_shipping_dict[supplier_code] = []
            supplier_shipping_dict[supplier_code].append({'type': shipping_type, 'quantity': quantity})
        self.supplier_shipping_types = supplier_shipping_dict
        return list(set(selected))  # Remove any duplicates

    def update_cost_parameters(self):
        self.fixed_vehicle_cost_per_km = self.fixed_vehicle_cost_var.get()
        self.driver_cost_per_day = self.driver_cost_var.get()

    def compare_methods(self):
        if not self.distance_matrix:
            messagebox.showerror("خطأ", "يرجى تحميل بيانات المسافات أولاً")
            return
        selected_suppliers = self.get_selected_suppliers()
        if len(selected_suppliers) < 2:
            messagebox.showerror("خطأ", "يرجى اختيار مورد واحد على الأقل بالإضافة للمخزن")
            return
        missing_suppliers = [s for s in selected_suppliers if s not in self.distance_matrix]
        if missing_suppliers:
            messagebox.showerror("خطأ", f"الموردين التالية غير موجودة في ملف الإكسل: {', '.join(missing_suppliers)}")
            return
        self.update_cost_parameters()
        self.results_text.delete(1.0, tk.END)
        # Method 1: Company Vehicle
        route, company_distance = self.solve_tsp_for_suppliers(selected_suppliers)
        if route:
            route_names = [SUPPLIER_MAP[letter] for letter in route]
            fixed_vehicle_cost = company_distance * self.fixed_vehicle_cost_per_km
            driver_cost = self.driver_cost_per_day  # 1-day trip assumed
            total_company_cost = fixed_vehicle_cost + driver_cost
            self.results_text.insert(tk.END, "🚛 الطريقة الأولى: سيارة الشركة تمر بجميع الموردين\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n")
            self.results_text.insert(tk.END, "المسار الأمثل:\n")
            for i, name in enumerate(route_names, 1):
                self.results_text.insert(tk.END, f"{i}. {name}\n")
            self.results_text.insert(tk.END, f"\nإجمالي المسافة: {company_distance:.1f} كم\n\n")
            self.results_text.insert(tk.END, "💰 تفاصيل التكلفة:\n")
            self.results_text.insert(tk.END, f"   • التكلفة الثابتة للسيارة: {fixed_vehicle_cost:.2f} ريال ({company_distance:.1f} كم × {self.fixed_vehicle_cost_per_km:.2f} ريال/كم)\n")
            self.results_text.insert(tk.END, f"   • راتب السائق: {driver_cost:.2f} ريال (يوم واحد)\n")
            self.results_text.insert(tk.END, f"   📊 إجمالي التكلفة: {total_company_cost:.2f} ريال\n\n")
        # Method 2: Individual Shipping (updated with new costs)
        total_shipping_cost, shipping_details = self.calculate_shipping_cost(len(selected_suppliers) - 1)
        self.results_text.insert(tk.END, "📦 الطريقة الثانية: كل مورد يرسل بشكل منفصل\n")
        self.results_text.insert(tk.END, "-" * 60 + "\n")
        supplier_groups = {}
        total_individual_distance = 0
        for detail in shipping_details:
            supplier_code = detail['supplier_code']
            if supplier_code not in supplier_groups:
                supplier_groups[supplier_code] = {
                    'name': detail['supplier_name'],
                    'distance': detail['distance'],
                    'shipping_types': [],
                    'total_cost': 0
                }
                if detail['distance'] > 0:
                    total_individual_distance += detail['distance']
            supplier_groups[supplier_code]['shipping_types'].append({
                'type': detail['shipping_type'],
                'cost': detail['cost'],
                'quantity': detail['quantity']
            })
            supplier_groups[supplier_code]['total_cost'] += detail['cost']
        for supplier_code, info in supplier_groups.items():
            self.results_text.insert(tk.END, f"{info['name']}:\n")
            self.results_text.insert(tk.END, f"   • المسافة: {info['distance']:.1f} كم\n")
            self.results_text.insert(tk.END, "   • أنواع الشحن:\n")
            for shipping in info['shipping_types']:
                self.results_text.insert(tk.END, f"     - {shipping['type']} × {shipping['quantity']}: {shipping['cost']:.2f} ريال\n")
            self.results_text.insert(tk.END, f"   • إجمالي التكلفة للمورد: {info['total_cost']:.2f} ريال\n\n")
        self.results_text.insert(tk.END, f"إجمالي المسافة: {total_individual_distance:.1f} كم\n")
        self.results_text.insert(tk.END, "💰 تفاصيل التكلفة:\n")
        self.results_text.insert(tk.END, f"   • إجمالي تكلفة الشحن: {total_shipping_cost:.2f} ريال (شامل ضريبة القيمة المضافة {VAT_RATE*100}%)\n")
        # Comparison
        cost_savings = total_shipping_cost - total_company_cost
        cost_savings_percentage = (cost_savings / total_shipping_cost) * 100 if total_shipping_cost > 0 else 0
        distance_savings = total_individual_distance - company_distance
        distance_savings_percentage = (distance_savings / total_individual_distance) * 100 if total_individual_distance > 0 else 0
        self.results_text.insert(tk.END, "\n📊 مقارنة بين الطريقتين:\n")
        self.results_text.insert(tk.END, f"   • المسافة (سيارة الشركة): {company_distance:.1f} كم\n")
        self.results_text.insert(tk.END, f"   • المسافة (الشحن المنفصل): {total_individual_distance:.1f} كم\n")
        self.results_text.insert(tk.END, f"   • نسبة التوفير في المسافة: {abs(distance_savings_percentage):.1f}% {'توفير' if distance_savings > 0 else 'زيادة'}\n")
        self.results_text.insert(tk.END, f"   • التكلفة (سيارة الشركة): {total_company_cost:.2f} ريال\n")
        self.results_text.insert(tk.END, f"   • التكلفة (الشحن المنفصل): {total_shipping_cost:.2f} ريال\n")
        self.results_text.insert(tk.END, f"   • نسبة التوفير في التكلفة: {abs(cost_savings_percentage):.1f}% {'توفير' if cost_savings > 0 else 'زيادة'}\n")
        self.results_text.insert(tk.END, "\n🎯 التوصية النهائية:\n")
        if cost_savings > 0:
            self.results_text.insert(tk.END, f"✅ استخدم سيارة الشركة - توفير {cost_savings:.2f} ريال ({cost_savings_percentage:.1f}%)\n")
        else:
            self.results_text.insert(tk.END, f"✅ استخدم الشحن المنفصل - توفير {abs(cost_savings):.2f} ريال ({abs(cost_savings_percentage):.1f}%)\n")

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
        df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0, engine='openpyxl')
        distance_matrix = {}
        
        for i, from_supplier in enumerate(df.index.tolist()):
            from_supplier_str = str(from_supplier).strip().upper()
            distance_matrix[from_supplier_str] = {}
            
            for j, to_supplier in enumerate(df.columns.tolist()):
                to_supplier_str = str(to_supplier).strip().upper()
                distance_matrix[from_supplier_str][to_supplier_str] = df.iloc[i, j]
        
        return distance_matrix
    
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
    
    def calculate_shipping_cost(self, num_suppliers):
        total_cost = 0
        shipping_details = []
        processed_suppliers = set()
        for supplier, shipping_types in self.supplier_shipping_types.items():
            distance = self.distance_matrix[supplier]['A']
            for shipping_info in shipping_types:
                shipping_type = shipping_info['type']
                quantity = shipping_info['quantity']
                base_cost = SHIPPING_TYPES[shipping_type]['cost']
                cost_with_vat = base_cost * (1 + VAT_RATE) * quantity
                shipping_details.append({
                    'supplier_code': supplier,
                    'supplier_name': SUPPLIER_MAP[supplier],
                    'distance': distance if supplier not in processed_suppliers else 0,  # Only include distance once
                    'shipping_type': SHIPPING_TYPES[shipping_type]['name'],
                    'cost': cost_with_vat,
                    'quantity': quantity
                })
                total_cost += cost_with_vat
            processed_suppliers.add(supplier)
        return total_cost, shipping_details
    
    def solve_tsp_for_suppliers(self, supplier_letters):
        try:
            model = gp.Model("Supplier_TSP")
            model.setParam('OutputFlag', 0)
            
            edges = [(i, j) for i in supplier_letters for j in supplier_letters if i != j]
            x = model.addVars(edges, vtype=GRB.BINARY, name="x")
            u = model.addVars(supplier_letters, vtype=GRB.CONTINUOUS, name="u")
            n = len(supplier_letters)
            
            model.addConstrs((gp.quicksum(x[i,j] for j in supplier_letters if i != j) == 1 for i in supplier_letters), name="outgoing")
            model.addConstrs((gp.quicksum(x[j,i] for j in supplier_letters if i != j) == 1 for i in supplier_letters), name="incoming")
            
            for i in supplier_letters:
                for j in supplier_letters:
                    if i != j and i != supplier_letters[0] and j != supplier_letters[0]:
                        model.addConstr(u[i] - u[j] + (n-1)*x[i,j] <= n-2, name=f"subtour_{i}_{j}")
            
            for i in supplier_letters[1:]:
                u[i].LB = 1
                u[i].UB = n-1
            
            model.addConstr(gp.quicksum(x['A',j] for j in supplier_letters if j != 'A') == 1, name="start_at_A")
            model.addConstr(gp.quicksum(x[i,'A'] for i in supplier_letters if i != 'A') == 1, name="end_at_A")
            
            model.setObjective(gp.quicksum(x[i,j]*self.distance_matrix[i][j] for i,j in edges), GRB.MINIMIZE)
            model.optimize()
            
            if model.status == GRB.OPTIMAL:
                solution = []
                remaining = set(supplier_letters)
                current = 'A'
                solution.append(current)
                remaining.remove(current)
                
                while remaining:
                    for j in supplier_letters:
                        if j in remaining and x[current,j].x > 0.5:
                            current = j
                            solution.append(current)
                            remaining.remove(current)
                            break
                
                if solution[-1] != 'A':
                    solution.append('A')
                
                total_dist = sum(self.distance_matrix[solution[i]][solution[i+1]] for i in range(len(solution)-1))
                return solution, total_dist
            else:
                return None, None
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حل مسألة التوجيه: {e}")
            return None, None

if __name__ == "__main__":
    root = tk.Tk()
    app = SupplyChainApp(root)
    root.mainloop()