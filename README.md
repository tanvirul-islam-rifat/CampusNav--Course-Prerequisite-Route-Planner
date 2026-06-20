# CampusNav — Course Prerequisite & Route Planner

A real-world academic planning tool that models a university curriculum as a **directed graph of prerequisites**, then applies graph algorithms to compute valid completion orders, detect impossible (circular) course plans, and generate a semester-by-semester roadmap to graduation.

This is the exact problem every CS student silently solves by hand each registration period — CampusNav solves it programmatically and provably correctly.

---

## The Real-World Problem

University curricula are dependency graphs: *CSE110 → CSE111 → CSE220 → CSE221*, and so on. Two questions matter in practice:

1. **Is this curriculum even completable?** A poorly designed prerequisite chain can accidentally contain a cycle (Course A requires B, B requires C, C requires A) — making it literally impossible to graduate. Catching this is a cycle-detection problem.
2. **What order should I take these courses in, and how many semesters will it take?** This is a topological sort and graph-layering problem.

CampusNav solves both, using three different algorithmic approaches so they can be directly compared.

---

## Features

- **Build a Course Catalog** — Add courses with credit values and prerequisite links, forming a directed graph
- **DFS Topological Sort** — Computes a valid course order using 3-color (white/gray/black) DFS marking; a gray node revisited means a cycle
- **BFS Topological Sort (Kahn's Algorithm)** — Computes a valid order using in-degree tracking and a queue
- **Lexicographically Smallest Order** — Uses a min-heap instead of a plain queue to always pick the alphabetically earliest available course, producing one deterministic, smallest valid sequence
- **Cycle Detection** — Both DFS and BFS approaches detect and report exactly which courses are part of an impossible circular dependency
- **Semester-by-Semester Planner** — Layers courses into semesters using a greedy BFS-by-level approach, respecting a configurable max-credits-per-semester cap
- **Sample Curriculum Loader** — Pre-loads a realistic BRAC-style CS course graph (13 courses, 13 prerequisite links) to try immediately

---

## How to Run

```bash
# Clone the repository
git clone https://github.com/tanvirul-islam-rifat/CampusNav--Course-Prerequisite-Route-Planner.git
cd campusnav-course-planner

# Run the application (Python 3 required, no external libraries needed)
python3 campusnav.py
```

On first run, choose option **8** to load a sample BRAC-style curriculum, then try options 4–7 to see the algorithms in action.

---

## Sample Output

```
-- DFS Topological Sort --
Valid completion order found:
  1. CSE110 — Programming Language I
  2. CSE230 — Discrete Mathematics
  3. CSE111 — Programming Language II
  ...

-- Lexicographically Smallest Valid Order --
CSE110 -> CSE111 -> CSE220 -> CSE230 -> CSE221 -> CSE260 -> ...

-- Semester-by-Semester Plan (cap: 15.0 credits) --

Semester 1 (9.0 credits):
   - CSE110: Programming Language I
   - CSE230: Discrete Mathematics
   - CSE260: Digital Logic Design

Semester 2 (3.0 credits):
   - CSE111: Programming Language II
...

Total: 6 semester(s), 40.0 credits
```

When a cycle is introduced (e.g. A requires B, B requires C, C requires A):

```
-- DFS Topological Sort --
IMPOSSIBLE — circular prerequisite dependency detected.
Courses involved in the cycle: ['A', 'B', 'C']
```

---

## Project Structure

```
campusnav-course-planner/
├── campusnav.py          # Graph model + 3 algorithms + CLI
├── data/
│   ├── courses.txt       # Persisted course catalog (auto-generated)
│   └── prerequisites.txt # Persisted prerequisite edges (auto-generated)
└── README.md
```

---

## Technical Architecture

- **Language:** Python 3.x
- **Paradigm:** Graph-based algorithm design with object-oriented data modeling
- **Core Data Structure:** Directed graph via adjacency list (`dict[str, list[str]]`)
- **Data Storage:** Flat-file text database (`.txt`) for courses and prerequisite edges
- **Interface:** Command Line Interface (CLI)

## Core Engineering Practices Demonstrated

- **Three Independent Graph Algorithms, One Problem:** DFS-based topological sort, Kahn's BFS-based topological sort, and a heap-based lexicographic variant are all implemented separately so their trade-offs can be directly compared, not just one "correct" implementation
- **Cycle Detection via Graph Coloring:** The DFS approach uses the classic white/gray/black node-coloring technique — a gray (in-progress) node being revisited is the formal proof of a cycle, and the exact cycle membership is reported back to the user
- **Kahn's Algorithm with In-Degree Tracking:** The BFS approach maintains live in-degree counts per node, decrementing them as dependencies are satisfied — a direct, from-scratch implementation rather than a library call
- **Heap-based Lexicographic Ordering:** Swapping a plain queue for a `heapq` min-heap while keeping the rest of Kahn's algorithm identical demonstrates how a single data structure swap changes the output's tie-breaking behavior without changing the algorithm's correctness
- **Greedy Layered Scheduling:** The semester planner extends topological sort into a real constraint-satisfaction problem — packing the maximum valid courses into each semester under a credit ceiling, a simplified bin-packing-adjacent greedy strategy
- **Graceful Failure Reporting:** Every algorithm distinguishes between "no valid order exists" and "here is the valid order," and reports precisely which courses are unreachable due to a cycle, rather than failing silently or crashing

## Author

**Md. Tanvirul Islam Rifat**

* **GitHub:** [@tanvirul-islam-rifat](https://github.com/tanvirul-islam-rifat)
* **LinkedIn:** [Tanvirul Islam Rifat](https://www.linkedin.com/in/tanvirul-islam-rifat)
