import customtkinter as ctk
import sqlite3
import os
import pandas as pd
import shutil
from datetime import datetime
from tkinter import messagebox, filedialog
from tkcalendar import Calendar

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ExpenseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Xpense Desktop - Quản lý Chi tiêu")
        self.geometry("950x850")
        
        # Database setup
        self.init_db()

        self.editing_id = None
        self.current_filter = None

        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # 1. Header & Summary
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Xpense Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(0, 20))

        self.summary_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.summary_frame.pack(fill="x")
        self.summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.thu_card = self.create_card(self.summary_frame, "TỔNG THU", "#10b981", 0)
        self.chi_card = self.create_card(self.summary_frame, "TỔNG CHI", "#ef4444", 1)
        self.lai_card = self.create_card(self.summary_frame, "SỐ DƯ (LÃI)", "#6366f1", 2)

        # 2. Form Section
        self.form_frame = ctk.CTkFrame(self, corner_radius=15, border_width=1, border_color="#334155")
        self.form_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.form_title = ctk.CTkLabel(self.form_frame, text="Ghi chép giao dịch", font=ctk.CTkFont(weight="bold"))
        self.form_title.pack(pady=(10, 5))

        self.input_inner = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.input_inner.pack(padx=20, pady=5, fill="x")

        self.input_font = ctk.CTkFont(size=15)

        self.desc_entry = ctk.CTkEntry(self.input_inner, placeholder_text="Nội dung...", height=40, font=self.input_font)
        self.desc_entry.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.amount_var = ctk.StringVar()
        self.amount_var.trace_add("write", self.format_amount_input)
        self.amount_entry = ctk.CTkEntry(self.input_inner, placeholder_text="Số tiền...", textvariable=self.amount_var, height=40, font=self.input_font)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.type_menu = ctk.CTkOptionMenu(self.input_inner, values=["Thu", "Chi"], width=120, height=40, font=self.input_font)
        self.type_menu.grid(row=0, column=2, padx=5, pady=10)
        self.type_menu.set("Chi")

        # Date Entry with Picker
        self.date_frame = ctk.CTkFrame(self.input_inner, fg_color="transparent")
        self.date_frame.grid(row=0, column=3, padx=5, pady=5)
        
        self.date_entry = ctk.CTkEntry(self.date_frame, placeholder_text="YYYY-MM-DD", width=120, height=40, font=self.input_font)
        self.date_entry.pack(side="left")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        self.date_picker_btn = ctk.CTkButton(self.date_frame, text="📅", width=40, height=40, font=self.input_font, command=lambda: self.pick_date(self.date_entry))
        self.date_picker_btn.pack(side="left", padx=(5, 0))

        self.input_inner.grid_columnconfigure((0, 1), weight=2)

        self.btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.submit_btn = ctk.CTkButton(self.btn_frame, text="Lưu giao dịch", width=150, height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.save_transaction)
        self.submit_btn.pack(side="left", padx=10)

        self.export_btn = ctk.CTkButton(self.btn_frame, text="Xuất Excel", width=150, height=45, font=ctk.CTkFont(size=14), fg_color="#1e293b", hover_color="#334155", command=self.export_to_excel)
        self.export_btn.pack(side="left", padx=10)

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Hủy", width=150, height=45, font=ctk.CTkFont(size=14), fg_color="gray", command=self.reset_form)
        self.cancel_btn.pack(side="left", padx=10)
        self.cancel_btn.configure(state="disabled")

        # System/Admin Section
        self.system_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.system_frame.grid(row=2, column=0, padx=20, pady=(0, 2), sticky="ew")
        
        self.backup_btn = ctk.CTkButton(self.system_frame, text="Sao lưu (Backup)", width=120, height=32, font=ctk.CTkFont(size=12), fg_color="#334155", command=self.backup_data)
        self.backup_btn.pack(side="right", padx=5)
        
        self.import_btn = ctk.CTkButton(self.system_frame, text="Nhập dữ liệu (Import)", width=120, height=32, font=ctk.CTkFont(size=12), fg_color="#334155", command=self.import_data)
        self.import_btn.pack(side="right", padx=5)

        # 3. Filter Section
        self.filter_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.filter_frame.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")
        
        ctk.CTkLabel(self.filter_frame, text="Lọc dữ liệu theo khoảng thời gian:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 10))
        
        # Start Date Filter
        self.f_start_frame = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.f_start_frame.pack(side="left", padx=5)
        self.start_date_filter = ctk.CTkEntry(self.f_start_frame, placeholder_text="Từ (YYYY-MM-DD)", width=110)
        self.start_date_filter.pack(side="left")
        ctk.CTkButton(self.f_start_frame, text="📅", width=32, command=lambda: self.pick_date(self.start_date_filter)).pack(side="left", padx=(2, 0))
        
        ctk.CTkLabel(self.filter_frame, text="→").pack(side="left", padx=2)

        # End Date Filter
        self.f_end_frame = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.f_end_frame.pack(side="left", padx=5)
        self.end_date_filter = ctk.CTkEntry(self.f_end_frame, placeholder_text="Đến (YYYY-MM-DD)", width=110)
        self.end_date_filter.pack(side="left")
        ctk.CTkButton(self.f_end_frame, text="📅", width=32, command=lambda: self.pick_date(self.end_date_filter)).pack(side="left", padx=(2, 0))
        
        self.apply_filter_btn = ctk.CTkButton(self.filter_frame, text="Lọc", width=80, command=self.apply_filter)
        self.apply_filter_btn.pack(side="left", padx=5)
        
        self.reset_filter_btn = ctk.CTkButton(self.filter_frame, text="Xóa lọc", width=80, fg_color="gray", command=self.reset_filter)
        self.reset_filter_btn.pack(side="left", padx=5)

        # 4. List Section
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Lịch sử giao dịch")
        self.list_frame.grid(row=4, column=0, padx=20, pady=5, sticky="nsew")

        self.list_header = ctk.CTkFrame(self.list_frame, fg_color="#1e293b")
        self.list_header.pack(fill="x", pady=2)
        ctk.CTkLabel(self.list_header, text="Ngày", width=100).pack(side="left", padx=10)
        ctk.CTkLabel(self.list_header, text="Nội dung", width=250).pack(side="left", padx=10)
        ctk.CTkLabel(self.list_header, text="Loại", width=80).pack(side="left", padx=10)
        ctk.CTkLabel(self.list_header, text="Số tiền", width=120).pack(side="left", padx=10)
        ctk.CTkLabel(self.list_header, text="Hành động", width=100).pack(side="left", padx=10)

        self.load_data()

    def create_card(self, parent, label, color, col):
        card = ctk.CTkFrame(parent, corner_radius=15, border_width=1, border_color=color)
        card.grid(row=0, column=col, padx=10, sticky="ew")
        
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(pady=(10, 0))
        value_label = ctk.CTkLabel(card, text="0₫", font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        value_label.pack(pady=(0, 10))
        return value_label

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                type TEXT,
                description TEXT,
                date TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def pick_date(self, target_entry):
        # Popup window for calendar
        window = ctk.CTkToplevel(self)
        window.title("Chọn ngày")
        window.geometry("300x350")
        window.grab_set() # Modal
        
        cal = Calendar(window, selectmode='day', 
                      year=datetime.now().year, 
                      month=datetime.now().month, 
                      day=datetime.now().day,
                      date_pattern='yyyy-mm-dd')
        cal.pack(pady=20, padx=20, fill="both", expand=True)

        def set_date():
            target_entry.delete(0, 'end')
            target_entry.insert(0, cal.get_date())
            window.destroy()

        ctk.CTkButton(window, text="Chọn", command=set_date).pack(pady=10)

    def apply_filter(self):
        start = self.start_date_filter.get().strip()
        end = self.end_date_filter.get().strip()
        
        if not start or not end:
            messagebox.showwarning("Thông báo", "Vui lòng nhập đầy đủ khoảng thời gian")
            return
            
        self.current_filter = (start, end)
        self.load_data()
        
    def reset_filter(self):
        self.start_date_filter.delete(0, 'end')
        self.end_date_filter.delete(0, 'end')
        self.current_filter = None
        self.load_data()

    def load_data(self):
        for widget in self.list_frame.winfo_children():
            if widget != self.list_header: widget.destroy()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM expenses"
        params = []
        if self.current_filter:
            query += " WHERE date BETWEEN ? AND ?"
            params = [self.current_filter[0], self.current_filter[1]]
            
        query += " ORDER BY date DESC, id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        total_thu = 0
        total_chi = 0

        for row in rows:
            id, amount, dtype, desc, date = row
            is_thu = dtype.lower() == "thu"
            if is_thu: total_thu += amount
            else: total_chi += amount

            row_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=date, width=100).pack(side="left", padx=10)
            ctk.CTkLabel(row_frame, text=desc, width=250, anchor="w").pack(side="left", padx=10)
            badge_color = "#10b981" if is_thu else "#ef4444"
            ctk.CTkLabel(row_frame, text=dtype.upper(), width=80, text_color=badge_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            amount_str = f"{'+' if is_thu else '-'}{amount:,.0f}₫"
            ctk.CTkLabel(row_frame, text=amount_str, width=120, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

            actions = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions.pack(side="left", padx=10)
            ctk.CTkButton(actions, text="Sửa", width=40, height=24, command=lambda r=row: self.start_edit(r)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Xóa", width=40, height=24, fg_color="#ef4444", hover_color="#dc2626", 
                         command=lambda r_id=id: self.delete_transaction(r_id)).pack(side="left", padx=2)
        conn.close()

        self.thu_card.configure(text=f"{total_thu:,.0f}₫")
        self.chi_card.configure(text=f"{total_chi:,.0f}₫")
        balance = total_thu - total_chi
        self.lai_card.configure(text=f"{balance:,.0f}₫", text_color="#10b981" if balance >= 0 else "#ef4444")

    def save_transaction(self):
        desc = self.desc_entry.get()
        amount_raw = self.amount_var.get().replace(",", "")
        dtype = self.type_menu.get().lower()
        date = self.date_entry.get()

        if not desc or not amount_raw or not date:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin!")
            return

        try:
            amount_val = float(amount_raw)
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền phải là số!")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if self.editing_id:
            cursor.execute("UPDATE expenses SET description=?, amount=?, type=?, date=? WHERE id=?",
                          (desc, amount_val, dtype, date, self.editing_id))
        else:
            cursor.execute("INSERT INTO expenses (description, amount, type, date) VALUES (?, ?, ?, ?)",
                          (desc, amount_val, dtype, date))
        conn.commit()
        conn.close()
        self.reset_form()
        self.load_data()

    def start_edit(self, row):
        id, amount, dtype, desc, date = row
        self.editing_id = id
        self.desc_entry.delete(0, 'end')
        self.desc_entry.insert(0, desc)
        self.amount_var.set(f"{amount:,.0f}")
        self.type_menu.set(dtype.capitalize())
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, date)
        self.form_title.configure(text="Sửa thông tin giao dịch", text_color="#6366f1")
        self.submit_btn.configure(text="Cập nhật")
        self.cancel_btn.configure(state="normal")

    def delete_transaction(self, id):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa giao dịch này?"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id=?", (id,))
            conn.commit()
            conn.close()
            self.load_data()

    def reset_form(self):
        self.editing_id = None
        self.desc_entry.delete(0, 'end')
        self.amount_var.set("")
        self.type_menu.set("Chi")
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.form_title.configure(text="Ghi chép giao dịch", text_color="white")
        self.submit_btn.configure(text="Lưu giao dịch")
        self.cancel_btn.configure(state="disabled")

    def format_amount_input(self, *args):
        # Remove commas, get numeric part
        value = self.amount_var.get().replace(",", "")
        if value == "": return
        
        try:
            # Handle only numbers
            numeric_value = int(''.join(filter(str.isdigit, value)))
            # Set formatted value back
            formatted = f"{numeric_value:,}"
            self.amount_var.set(formatted)
        except:
            # If invalid, just don't format or keep old numeric parts
            pass

    def export_to_excel(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM expenses"
            params = []
            if self.current_filter:
                query += " WHERE date BETWEEN ? AND ?"
                params = [self.current_filter[0], self.current_filter[1]]
            query += " ORDER BY date DESC"
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                messagebox.showwarning("Thông báo", "Không có dữ liệu!")
                return

            df.columns = ["ID", "Số tiền (VNĐ)", "Phân loại", "Nội dung", "Ngày"]
            total_thu = df[df["Phân loại"] == "thu"]["Số tiền (VNĐ)"].sum()
            total_chi = df[df["Phân loại"] == "chi"]["Số tiền (VNĐ)"].sum()
            balance = total_thu - total_chi

            df_summary = pd.DataFrame({
                "Hạng mục": ["Tổng thu", "Tổng chi", "Số dư/Lãi", "Thời gian"],
                "Giá trị": [total_thu, total_chi, balance, f"{self.current_filter[0]} -> {self.current_filter[1]}" if self.current_filter else "Tất cả"]
            })

            file_name = f"Bao_cao_chi_tieu_{datetime.now().strftime('%Y%m%d')}"
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=f"{file_name}.xlsx")
            if not file_path: return

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Chi tiết', index=False)
                df_summary.to_excel(writer, sheet_name='Tổng hợp', index=False)
            messagebox.showinfo("Thành công", f"Đã xuất file Excel thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

    def backup_data(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("SQLite Database", "*.db")],
                initialfile=f"Backup_TaiChinh_{datetime.now().strftime('%Y%m%d')}.db"
            )
            if not file_path: return
            
            shutil.copy2(DB_PATH, file_path)
            messagebox.showinfo("Thành công", f"Đã sao lưu dữ liệu tại:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi sao lưu: {str(e)}")

    def import_data(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Supported Files", "*.xlsx *.db"), ("Excel files", "*.xlsx"), ("Database files", "*.db")]
        )
        if not file_path: return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            imported_count = 0

            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
                # Kiểm tra cột (Dựa trên format xuất của app)
                # "Số tiền (VNĐ)", "Phân loại", "Nội dung", "Ngày" (Hoặc tên cột tương ứng)
                for _, row in df.iterrows():
                    # Attempt to map columns - support both original and export names
                    amount = row.get("Số tiền (VNĐ)") or row.get("amount")
                    dtype = (row.get("Phân loại") or row.get("type")).lower()
                    desc = row.get("Nội dung") or row.get("description")
                    date = row.get("Ngày") or row.get("date")

                    if amount and dtype and desc and date:
                        cursor.execute("INSERT INTO expenses (amount, type, description, date) VALUES (?, ?, ?, ?)",
                                      (float(amount), dtype, str(desc), str(date)))
                        imported_count += 1

            elif file_path.endswith('.db'):
                # Merge from another database
                other_conn = sqlite3.connect(file_path)
                other_cursor = other_conn.cursor()
                other_cursor.execute("SELECT amount, type, description, date FROM expenses")
                other_rows = other_cursor.fetchall()
                for r in other_rows:
                    cursor.execute("INSERT INTO expenses (amount, type, description, date) VALUES (?, ?, ?, ?)", r)
                    imported_count += 1
                other_conn.close()

            conn.commit()
            conn.close()
            self.load_data()
            messagebox.showinfo("Thành công", f"Đã nhập thành công {imported_count} giao dịch mới!")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể nhập dữ liệu: {str(e)}")

if __name__ == "__main__":
    app = ExpenseApp()
    app.mainloop()
