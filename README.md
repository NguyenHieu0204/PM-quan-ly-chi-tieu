# Phần mềm Quản lý Chi tiêu (Xpense)

Ứng dụng quản lý thu chi cá nhân với cả giao diện Web (Flask) và Desktop (CustomTkinter).

## Tính năng
- Ghi chép các giao dịch thu/chi.
- Hiển thị tổng quan số dư, tổng thu, tổng chi.
- Lọc giao dịch theo khoảng thời gian.
- Xuất báo cáo ra file Excel.
- Sao lưu và nhập dữ liệu từ file Database (.db) hoặc Excel.

## Cài đặt

1. Tạo môi trường ảo (khuyến nghị):
```bash
python -m venv venv
source venv/bin/activate  # Trên Windows dùng: venv\Scripts\activate
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Khởi tạo cơ sở dữ liệu:
```bash
python init_db.py
```

## Cách sử dụng

### Phiên bản Desktop
Chạy file sau để mở ứng dụng giao diện cửa sổ:
```bash
python desktop_app.py
```

### Phiên bản Web
Chạy file sau và truy cập vào `http://127.0.0.1:5001`:
```bash
python app.py
```

## Đóng góp
Mọi đóng góp nhằm cải thiện ứng dụng đều được hoan nghênh.
