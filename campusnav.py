"""
CampusNav — Course Prerequisite & Route Planner
A real-world academic planning tool that models a university course catalog
as a directed graph of prerequisites, then uses graph algorithms to compute
valid completion orders, detect impossible (cyclic) curricula, and estimate
the minimum number of semesters needed to graduate.

"""

import os
import heapq
from collections import deque

COURSES_FILE = "data/courses.txt"
PREREQS_FILE = "data/prerequisites.txt"


# ═══════════════════════════════════════════════════════
# COURSE CATALOG (the graph itself)
# ═══════════════════════════════════════════════════════

class CourseCatalog:
    """
    Models a university curriculum as a directed graph.
    Each course is a node; an edge A -> B means "A must be completed before B".
    """

    def __init__(self):
        self.courses = {}          # code -> course name
        self.adj = {}              # code -> list of courses that depend on it (A -> B)
        self.credits = {}          # code -> credit value
        self._load()

    # ── Persistence ──

    def _load(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(COURSES_FILE):
            with open(COURSES_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",", 2)
                    code, credit, name = parts[0], float(parts[1]), parts[2]
                    self.courses[code] = name
                    self.credits[code] = credit
                    self.adj.setdefault(code, [])

        if os.path.exists(PREREQS_FILE):
            with open(PREREQS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    a, b = line.split(",")
                    self.adj.setdefault(a, []).append(b)
                    self.adj.setdefault(b, [])

    def _save_courses(self):
        with open(COURSES_FILE, "w") as f:
            for code, name in self.courses.items():
                f.write(f"{code},{self.credits[code]},{name}\n")

    def _save_prereqs(self):
        with open(PREREQS_FILE, "w") as f:
            for a in self.adj:
                for b in self.adj[a]:
                    f.write(f"{a},{b}\n")

    # ── Catalog Management ──

    def add_course(self, code, name, credit=3.0):
        if code in self.courses:
            return False, f"Course {code} already exists."
        self.courses[code] = name
        self.credits[code] = credit
        self.adj.setdefault(code, [])
        self._save_courses()
        return True, f"Added course {code} — {name} ({credit} credits)."

    def add_prerequisite(self, before, after):
        """Add edge: `before` must be completed before `after`."""
        if before not in self.courses or after not in self.courses:
            return False, "Both courses must exist in the catalog first."
        if after in self.adj.get(before, []):
            return False, "This prerequisite already exists."
        self.adj.setdefault(before, []).append(after)
        self._save_prereqs()
        return True, f"{before} is now a prerequisite of {after}."

    def list_courses(self):
        return sorted(self.courses.keys())

    def get_course_name(self, code):
        return self.courses.get(code, "Unknown Course")

    def all_nodes(self):
        return list(self.courses.keys())


# ═══════════════════════════════════════════════════════
# TOPOLOGICAL SORT — DFS APPROACH (with cycle detection)
# ═══════════════════════════════════════════════════════

def topo_sort_dfs(catalog):
    """
    Computes a valid course order using DFS-based topological sort.
    Uses 3-color marking (white/gray/black) to detect cycles —
    a gray node revisited means an impossible (circular) prerequisite chain.
    Returns (order, cycle_found, cycle_courses)
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in catalog.all_nodes()}
    stack_order = []
    cycle_found = [False]
    cycle_nodes = set()

    def visit(u, path):
        color[u] = GRAY
        path.append(u)
        for v in catalog.adj.get(u, []):
            if color[v] == GRAY:
                cycle_found[0] = True
                # Capture the cycle segment for reporting
                idx = path.index(v)
                cycle_nodes.update(path[idx:])
            elif color[v] == WHITE:
                visit(v, path)
        path.pop()
        color[u] = BLACK
        stack_order.append(u)

    for node in catalog.all_nodes():
        if color[node] == WHITE:
            visit(node, [])

    if cycle_found[0]:
        return None, True, cycle_nodes

    stack_order.reverse()
    return stack_order, False, set()


# ═══════════════════════════════════════════════════════
# TOPOLOGICAL SORT — BFS APPROACH (Kahn's Algorithm)
# ═══════════════════════════════════════════════════════

def topo_sort_bfs(catalog, lexicographic=False):
    """
    Computes a valid course order using Kahn's BFS-based algorithm.
    If lexicographic=True, uses a min-heap instead of a plain queue
    to always pick the alphabetically smallest available course next —
    producing the lexicographically smallest valid sequence.
    Returns (order, possible)
    """
    nodes = catalog.all_nodes()
    in_degree = {node: 0 for node in nodes}
    for u in nodes:
        for v in catalog.adj.get(u, []):
            in_degree[v] += 1

    if lexicographic:
        heap = [node for node in nodes if in_degree[node] == 0]
        heapq.heapify(heap)
    else:
        heap = deque(sorted(node for node in nodes if in_degree[node] == 0))

    order = []
    while heap:
        if lexicographic:
            u = heapq.heappop(heap)
        else:
            u = heap.popleft()
        order.append(u)
        for v in catalog.adj.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                if lexicographic:
                    heapq.heappush(heap, v)
                else:
                    heap.append(v)

    possible = len(order) == len(nodes)
    return order, possible


# ═══════════════════════════════════════════════════════
# SEMESTER PLANNER (level-by-level BFS layering)
# ═══════════════════════════════════════════════════════

def plan_semesters(catalog, max_credits_per_semester=15.0):
    """
    Groups courses into semesters using a layered BFS approach:
    a course can be taken in the earliest semester where all its
    prerequisites have already been completed in prior semesters,
    subject to a maximum credit load per semester.
    """
    nodes = catalog.all_nodes()
    in_degree = {node: 0 for node in nodes}
    for u in nodes:
        for v in catalog.adj.get(u, []):
            in_degree[v] += 1

    available = sorted(node for node in nodes if in_degree[node] == 0)
    semesters = []
    completed = set()

    while available or any(in_degree[n] > 0 for n in nodes if n not in completed):
        if not available:
            # Remaining courses have unmet prerequisites that can never clear -> cycle
            remaining = [n for n in nodes if n not in completed]
            return semesters, False, remaining

        this_semester = []
        credit_used = 0.0
        still_available = []

        for course in available:
            cost = catalog.credits.get(course, 3.0)
            if credit_used + cost <= max_credits_per_semester:
                this_semester.append(course)
                credit_used += cost
            else:
                still_available.append(course)

        if not this_semester:
            # Single course exceeds the credit cap; take it alone
            this_semester = [available[0]]
            still_available = available[1:]

        for course in this_semester:
            completed.add(course)

        next_available = list(still_available)
        for course in this_semester:
            for nxt in catalog.adj.get(course, []):
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    next_available.append(nxt)

        semesters.append(sorted(this_semester))
        available = sorted(set(next_available))

    return semesters, True, []


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def seed_sample_catalog(catalog):
    """Pre-load a sample curriculum modeled after a BRAC CS-style course path."""
    sample_courses = [
        ("CSE110", "Programming Language I", 3.0),
        ("CSE111", "Programming Language II", 3.0),
        ("CSE220", "Data Structures", 3.0),
        ("CSE221", "Algorithms", 3.0),
        ("CSE230", "Discrete Mathematics", 3.0),
        ("CSE260", "Digital Logic Design", 3.0),
        ("CSE320", "Data Communications", 3.0),
        ("CSE321", "Operating Systems", 3.0),
        ("CSE370", "Database Systems", 3.0),
        ("CSE331", "Automata and Computability", 3.0),
        ("CSE422", "Artificial Intelligence", 3.0),
        ("CSE470", "Software Engineering", 3.0),
        ("CSE400", "Project & Thesis", 4.0),
    ]
    sample_prereqs = [
        ("CSE110", "CSE111"),
        ("CSE111", "CSE220"),
        ("CSE220", "CSE221"),
        ("CSE220", "CSE320"),
        ("CSE221", "CSE331"),
        ("CSE221", "CSE422"),
        ("CSE230", "CSE221"),
        ("CSE260", "CSE320"),
        ("CSE320", "CSE321"),
        ("CSE111", "CSE370"),
        ("CSE221", "CSE470"),
        ("CSE470", "CSE400"),
        ("CSE422", "CSE400"),
    ]
    for code, name, credit in sample_courses:
        if code not in catalog.courses:
            catalog.add_course(code, name, credit)
    for a, b in sample_prereqs:
        catalog.add_prerequisite(a, b)


def print_menu():
    print("\n" + "=" * 52)
    print("     CampusNav — Course Prerequisite Planner")
    print("=" * 52)
    print("  1. Add a Course")
    print("  2. Add a Prerequisite Link")
    print("  3. List All Courses")
    print("  4. Compute Valid Order (DFS Topological Sort)")
    print("  5. Compute Valid Order (BFS / Kahn's Algorithm)")
    print("  6. Compute Lexicographically Smallest Order")
    print("  7. Generate Semester-by-Semester Plan")
    print("  8. Load Sample BRAC-style Curriculum")
    print("  0. Exit")
    print("=" * 52)


def main():
    os.makedirs("data", exist_ok=True)
    catalog = CourseCatalog()
    print("\nWelcome to CampusNav — model your curriculum as a graph")
    print("and let graph algorithms tell you how to complete it.")

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print("\n-- Add Course --")
            code = input("Course Code (e.g. CSE221): ").strip().upper()
            name = input("Course Name: ").strip()
            try:
                credit = float(input("Credits (default 3.0): ").strip() or 3.0)
            except ValueError:
                credit = 3.0
            ok, msg = catalog.add_course(code, name, credit)
            print(msg)

        elif choice == "2":
            print("\n-- Add Prerequisite --")
            print("Format: Course A must be completed BEFORE Course B")
            before = input("Course A (prerequisite): ").strip().upper()
            after = input("Course B (depends on A): ").strip().upper()
            ok, msg = catalog.add_prerequisite(before, after)
            print(msg)

        elif choice == "3":
            courses = catalog.list_courses()
            if not courses:
                print("\nNo courses in the catalog yet. Try option 8 to load a sample.")
            else:
                print(f"\n{'Code':<10}{'Credits':<10}{'Name'}")
                print("-" * 50)
                for code in courses:
                    print(f"{code:<10}{catalog.credits[code]:<10}{catalog.courses[code]}")

        elif choice == "4":
            order, cycle, cycle_nodes = topo_sort_dfs(catalog)
            print("\n-- DFS Topological Sort --")
            if cycle:
                print("IMPOSSIBLE — circular prerequisite dependency detected.")
                print(f"Courses involved in the cycle: {sorted(cycle_nodes)}")
            else:
                print("Valid completion order found:")
                for i, code in enumerate(order, 1):
                    print(f"  {i}. {code} — {catalog.get_course_name(code)}")

        elif choice == "5":
            order, possible = topo_sort_bfs(catalog, lexicographic=False)
            print("\n-- BFS Topological Sort (Kahn's Algorithm) --")
            if not possible:
                print("IMPOSSIBLE — circular prerequisite dependency detected.")
                unresolved = [c for c in catalog.all_nodes() if c not in order]
                print(f"Courses that could never be unlocked: {sorted(unresolved)}")
            else:
                print("Valid completion order found:")
                for i, code in enumerate(order, 1):
                    print(f"  {i}. {code} — {catalog.get_course_name(code)}")

        elif choice == "6":
            order, possible = topo_sort_bfs(catalog, lexicographic=True)
            print("\n-- Lexicographically Smallest Valid Order --")
            if not possible:
                print("IMPOSSIBLE — circular prerequisite dependency detected.")
            else:
                print(" -> ".join(order))

        elif choice == "7":
            try:
                cap = float(input("\nMax credits per semester (default 15): ").strip() or 15.0)
            except ValueError:
                cap = 15.0
            semesters, possible, remaining = plan_semesters(catalog, cap)
            print(f"\n-- Semester-by-Semester Plan (cap: {cap} credits) --")
            if not possible:
                print("IMPOSSIBLE to complete — circular dependency blocks these courses:")
                print(f"  {sorted(remaining)}")
            total_credits = 0.0
            for i, sem in enumerate(semesters, 1):
                sem_credits = sum(catalog.credits.get(c, 3.0) for c in sem)
                total_credits += sem_credits
                print(f"\nSemester {i} ({sem_credits} credits):")
                for code in sem:
                    print(f"   - {code}: {catalog.get_course_name(code)}")
            if possible:
                print(f"\nTotal: {len(semesters)} semester(s), {total_credits} credits")

        elif choice == "8":
            seed_sample_catalog(catalog)
            print("\nSample BRAC-style curriculum loaded (13 courses, 13 prerequisite links).")

        elif choice == "0":
            print("\nGoodbye! Plan well and graduate on time.\n")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
