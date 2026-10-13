# Tối Ưu Hóa Mã Hóa SAT Cho Bài Toán N-Queens

Dự án này triển khai mô hình hóa bài toán **N-Queens** sang **Boolean Satisfiability (SAT)**, đánh giá thực nghiệm **5 kỹ thuật mã hóa At-Most-One (AMO)** và so sánh đối đầu hiệu năng với các bộ giải Lập trình Ràng buộc (CP) và Quy hoạch Tuyến tính Nguyên (ILP).

## 🛠️ Môi trường Thực nghiệm
- **CPU:** 12th Gen Intel Core i5-12450HX
- **RAM:** 16 GB
- **OS:** Windows / Linux / macOS
- **Python:** 3.10+

## 🚀 Cài đặt & Hướng dẫn Sử dụng

1. **Cài đặt thư viện phụ thuộc:**
```bash
pip install -r requirements.txt
```

2. **Chạy benchmark thu thập số liệu:**
```bash
python nqueens_benchmark.py
```

3. **Tạo các đồ thị phân tích:**
```bash
python generate_plots.py
```

## 📊 Cấu trúc Thư mục
```text
N-Queens-SAT-Solver/
├── .gitignore
├── README.md
├── requirements.txt
├── nqueens_benchmark.py
├── generate_plots.py
├── paper/
└── results/
```