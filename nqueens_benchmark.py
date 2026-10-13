import os
import time
import pandas as pd

# Thư viện PySAT
from pysat.card import CardEnc, EncType
from pysat.formula import CNF
from pysat.solvers import Solver, NoSuchSolverError

# Thư viện Google OR-Tools
from ortools.sat.python import cp_model

# Thư viện Gurobi (Tránh crash nếu chưa cài đặt)
try:
    import gurobipy as gp
    from gurobipy import GRB

    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False


class NQueensSATSolver:
    def __init__(self, n, amo_encoding_name='product'):
        self.n = n
        self.amo_name = amo_encoding_name
        self.cnf = CNF()
        self.top_id = n * n

        # Bọc getattr() để truy xuất an toàn trên mọi phiên bản PySAT
        self.enc_map = {
            'pairwise': getattr(EncType, 'pairwise', 0),
            'seqcounter': getattr(EncType, 'seqcounter', 1),
            'binary': getattr(EncType, 'bitwise', getattr(EncType, 'binary', 2)),
            'commander': getattr(EncType, 'commander', getattr(EncType, 'seqcounter', 1)),
            'product': getattr(EncType, 'product', getattr(EncType, 'ladder', 1))
        }
        self.enc_type = self.enc_map.get(amo_encoding_name, self.enc_map['seqcounter'])

    def _var(self, r, c):
        return r * self.n + c + 1

    def build_cnf(self):
        n = self.n

        # 1. Hàng (Row Constraints)
        for r in range(n):
            lits = [self._var(r, c) for c in range(n)]
            self.cnf.append(lits)
            amo_cnf = CardEnc.atmost(lits=lits, bound=1, top_id=self.top_id, encoding=self.enc_type)
            self.cnf.extend(amo_cnf.clauses)
            if amo_cnf.nv > self.top_id:
                self.top_id = amo_cnf.nv

        # 2. Cột (Column Constraints)
        for c in range(n):
            lits = [self._var(r, c) for c in range(n)]
            self.cnf.append(lits)
            amo_cnf = CardEnc.atmost(lits=lits, bound=1, top_id=self.top_id, encoding=self.enc_type)
            self.cnf.extend(amo_cnf.clauses)
            if amo_cnf.nv > self.top_id:
                self.top_id = amo_cnf.nv

        # 3. Đường chéo chính (Main Diagonals)
        for k in range(-(n - 1), n):
            lits = [self._var(r, r - k) for r in range(n) if 0 <= r - k < n]
            if len(lits) > 1:
                amo_cnf = CardEnc.atmost(lits=lits, bound=1, top_id=self.top_id, encoding=self.enc_type)
                self.cnf.extend(amo_cnf.clauses)
                if amo_cnf.nv > self.top_id:
                    self.top_id = amo_cnf.nv

        # 4. Đường chéo phụ (Anti Diagonals)
        for k in range(2 * n - 1):
            lits = [self._var(r, k - r) for r in range(n) if 0 <= k - r < n]
            if len(lits) > 1:
                amo_cnf = CardEnc.atmost(lits=lits, bound=1, top_id=self.top_id, encoding=self.enc_type)
                self.cnf.extend(amo_cnf.clauses)
                if amo_cnf.nv > self.top_id:
                    self.top_id = amo_cnf.nv

    def _get_working_solver(self):
        # Danh sách các solver ưu tiên thử nghiệm trên Windows
        candidates = ['cadical', 'g4', 'g3', 'm22', 'glucose4', 'minisat22']
        for s_name in candidates:
            try:
                s = Solver(name=s_name, bootstrap_with=self.cnf)
                return s
            except NoSuchSolverError:
                continue
        # Rơi về Solver mặc định của hệ thống
        return Solver(bootstrap_with=self.cnf)

    def solve(self):
        start_time = time.time()
        self.build_cnf()
        build_time = time.time() - start_time

        start_solve = time.time()

        # Tự động chọn Solver tương thích
        solver = self._get_working_solver()
        with solver:
            solved = solver.solve()
            solve_time = time.time() - start_solve

        return {
            'N': self.n,
            'Encoding': self.amo_name,
            'Vars': self.top_id,
            'Clauses': len(self.cnf.clauses),
            'Build_Time': round(build_time, 4),
            'Solve_Time': round(solve_time, 4),
            'Total_Time': round(build_time + solve_time, 4),
            'Status': "SAT" if solved else "UNSAT"
        }


def solve_ortools_cp(n):
    model = cp_model.CpModel()
    queens = [model.NewIntVar(0, n - 1, f'q_{i}') for i in range(n)]

    model.AddAllDifferent(queens)
    model.AddAllDifferent([queens[i] + i for i in range(n)])
    model.AddAllDifferent([queens[i] - i for i in range(n)])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0

    start = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start

    return round(elapsed, 4) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else "Timeout/Error"


def solve_gurobi_ilp(n):
    if not HAS_GUROBI:
        return "N/A"
    try:
        env = gp.Env(empty=True)
        env.setParam('OutputFlag', 0)
        env.start()
        model = gp.Model("NQueens", env=env)
        model.setParam('TimeLimit', 300)

        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

        for i in range(n):
            model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)
            model.addConstr(gp.quicksum(x[j, i] for j in range(n)) == 1)

        for k in range(-(n - 1), n):
            diag = [x[r, r - k] for r in range(n) if 0 <= r - k < n]
            if len(diag) > 1:
                model.addConstr(gp.quicksum(diag) <= 1)

        for k in range(2 * n - 1):
            anti_diag = [x[r, k - r] for r in range(n) if 0 <= k - r < n]
            if len(anti_diag) > 1:
                model.addConstr(gp.quicksum(anti_diag) <= 1)

        start = time.time()
        model.optimize()
        elapsed = time.time() - start

        if model.status == GRB.OPTIMAL:
            return round(elapsed, 4)
        else:
            return "Timeout"
    except Exception:
        return "Error"


def run_benchmarks():
    os.makedirs("results", exist_ok=True)

    print("==================================================")
    print("1. THỰC NGHIỆM SO SÁNH CÁC KĨ THUẬT MÃ HÓA AMO")
    print("==================================================")

    encodings = ['pairwise', 'seqcounter', 'binary', 'commander', 'product']
    n_values_amo = [4, 16, 32, 64, 128, 256, 512]
    amo_results = []

    for n in n_values_amo:
        for enc in encodings:
            if enc == 'pairwise' and n > 256:
                amo_results.append({'N': n, 'Encoding': enc, 'Vars': 'OOM', 'Clauses': 'OOM', 'Total_Time': 'Timeout'})
                continue
            solver = NQueensSATSolver(n, amo_encoding_name=enc)
            res = solver.solve()
            amo_results.append(res)
            print(
                f"N={n:3d} | Encoding: {enc:10s} | Vars: {str(res['Vars']):8s} | Clauses: {str(res['Clauses']):10s} | Time: {res['Total_Time']}s")

    df_amo = pd.DataFrame(amo_results)
    df_amo.to_csv("results/results_amo_encodings.csv", index=False)

    print("\n==================================================")
    print("2. THỰC NGHIỆM SO SÁNH ĐỐI ĐẦU CÁC BỘ GIẢI (SOLVERS)")
    print("==================================================")

    n_values_solvers = [16, 32, 64, 128, 256, 512, 1000]
    solver_results = []

    for n in n_values_solvers:
        pysat_solver = NQueensSATSolver(n, 'product')
        pysat_res = pysat_solver.solve()
        pysat_time = pysat_res['Total_Time']

        ortools_time = solve_ortools_cp(n)
        gurobi_time = solve_gurobi_ilp(n) if n <= 256 else "Timeout"

        row = {
            'N': n,
            'PySAT (Product/Solver)': pysat_time,
            'Google OR-Tools (CP-SAT)': ortools_time,
            'Gurobi (ILP)': gurobi_time
        }
        solver_results.append(row)
        print(f"N={n:4d} | PySAT: {pysat_time}s | OR-Tools: {ortools_time}s | Gurobi: {gurobi_time}")

    df_solvers = pd.DataFrame(solver_results)
    df_solvers.to_csv("results/results_solvers_benchmark.csv", index=False)
    print("\n✅ Đã hoàn tất và lưu số liệu vào thư mục results/")


if __name__ == "__main__":
    run_benchmarks()