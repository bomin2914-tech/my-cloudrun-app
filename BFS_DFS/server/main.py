"""
Google Cloud Run 배포용 FastAPI 백엔드 서버
파일: main.py
목적: 너비 우선 탐색(BFS) 및 깊이 우선 탐색(DFS) 미로 탈출(Maze Escape) 시뮬레이션 및 그래프 탐색 비교 API
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import deque
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="BFS vs DFS Maze Escape & Graph Traversal API",
    description="Google Cloud Run 배포용 BFS & DFS 미로 탈출 시뮬레이션 및 자료구조(Queue vs Stack) 비교 백엔드",
    version="2.0.0"
)

# CORS 설정 (Google Apps Script 웹앱 및 로컬 테스트 지원)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 미로 탈출 (Maze Escape) 모델 및 데이터 스키마
# ==============================================================================

class MazeRequest(BaseModel):
    grid: List[List[int]] = Field(
        ...,
        description="2차원 미로 배열 (0: 이동 가능 통로, 1: 벽)",
        example=[
            [0, 0, 0, 1, 0],
            [1, 1, 0, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1],
            [0, 0, 0, 0, 0]
        ]
    )
    start: List[int] = Field(..., description="시작점 좌표 [row, col]", example=[0, 0])
    goal: List[int] = Field(..., description="도착점 좌표 [row, col]", example=[4, 4])
    algorithm: Optional[str] = Field("BOTH", description="알고리즘 종류: 'BFS', 'DFS', 'BOTH'")

    @field_validator("start", "goal")
    @classmethod
    def validate_coord(cls, v: List[int]) -> List[int]:
        if len(v) != 2:
            raise ValueError("좌표는 [row, col] 형태의 2개 정수여야 합니다.")
        return v


class MazeStep(BaseModel):
    step_num: int
    current: Optional[List[int]]
    data_structure: List[List[int]]  # Queue or Stack snapshot
    visited: List[List[int]]
    action: str  # "visit", "enqueue", "push", "pop", "backtrack", "goal"


class MazeResult(BaseModel):
    algorithm: str
    data_structure_type: str  # "Queue (FIFO)" or "Stack (LIFO)"
    found: bool
    path: List[List[int]]
    path_length: int
    visited_cells_count: int
    total_steps: int
    peak_memory_size: int  # Max Queue/Stack length
    steps: List[Dict[str, Any]]


class MazeComparisonResponse(BaseModel):
    grid_rows: int
    grid_cols: int
    start: List[int]
    goal: List[int]
    bfs: MazeResult
    dfs: MazeResult
    summary: Dict[str, Any]


# ==============================================================================
# 미로 탐색 핵심 알고리즘 구현 함수
# ==============================================================================

# 이동 방향: 상, 우, 하, 좌 (상하좌우 4방향)
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def solve_maze_bfs(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> MazeResult:
    """너비 우선 탐색 (BFS, Queue 기반): 레벨별 탐색으로 최단 경로 보장"""
    rows, cols = len(grid), len(grid[0])
    sr, sc = start
    gr, gc = goal

    queue = deque([(sr, sc)])
    visited_set = {(sr, sc)}
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {(sr, sc): None}

    steps: List[Dict[str, Any]] = []
    visited_order: List[List[int]] = []
    peak_queue_size = 1
    found = False

    step_counter = 1
    steps.append({
        "step_num": step_counter,
        "current": [sr, sc],
        "data_structure": [[sr, sc]],
        "visited": [[sr, sc]],
        "action": f"시작 노드 ({sr}, {sc}) 큐에 삽입 및 방문 예약"
    })

    while queue:
        peak_queue_size = max(peak_queue_size, len(queue))
        r, c = queue.popleft()
        visited_order.append([r, c])

        steps.append({
            "step_num": step_counter,
            "current": [r, c],
            "data_structure": [list(item) for item in queue],
            "visited": [list(x) for x in visited_order],
            "action": f"큐에서 꺼내어 ({r}, {c}) 방문 처리"
        })
        step_counter += 1

        if (r, c) == (gr, gc):
            found = True
            steps.append({
                "step_num": step_counter,
                "current": [r, c],
                "data_structure": [list(item) for item in queue],
                "visited": [list(x) for x in visited_order],
                "action": f"🎉 목적지 ({gr}, {gc}) 도달! 최단 경로 탐색 성공"
            })
            break

        # 인접 4방향 탐색
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 0 and (nr, nc) not in visited_set:
                    visited_set.add((nr, nc))
                    parent[(nr, nc)] = (r, c)
                    queue.append((nr, nc))
                    steps.append({
                        "step_num": step_counter,
                        "current": [r, c],
                        "data_structure": [list(item) for item in queue],
                        "visited": [list(x) for x in visited_order],
                        "action": f"이동 가능한 이웃 ({nr}, {nc}) 발견 ➜ 큐 뒤에 추가"
                    })
                    step_counter += 1

    # 최단 경로 역추적
    path: List[List[int]] = []
    if found:
        curr: Optional[Tuple[int, int]] = (gr, gc)
        while curr is not None:
            path.append([curr[0], curr[1]])
            curr = parent.get(curr)
        path.reverse()

    return MazeResult(
        algorithm="BFS (너비 우선 탐색)",
        data_structure_type="Queue (FIFO - 선입선출)",
        found=found,
        path=path,
        path_length=len(path),
        visited_cells_count=len(visited_order),
        total_steps=len(steps),
        peak_memory_size=peak_queue_size,
        steps=steps
    )


def solve_maze_dfs(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> MazeResult:
    """깊이 우선 탐색 (DFS, Stack 기반): 한 방향으로 깊게 파고들며 막히면 백트래킹"""
    rows, cols = len(grid), len(grid[0])
    sr, sc = start
    gr, gc = goal

    stack: List[Tuple[int, int]] = [(sr, sc)]
    visited_set = set()
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {(sr, sc): None}

    steps: List[Dict[str, Any]] = []
    visited_order: List[List[int]] = []
    peak_stack_size = 1
    found = False

    step_counter = 1
    steps.append({
        "step_num": step_counter,
        "current": [sr, sc],
        "data_structure": [[sr, sc]],
        "visited": [],
        "action": f"시작 노드 ({sr}, {sc}) 스택에 푸시"
    })

    while stack:
        peak_stack_size = max(peak_stack_size, len(stack))
        r, c = stack.pop()

        if (r, c) in visited_set:
            continue

        visited_set.add((r, c))
        visited_order.append([r, c])

        steps.append({
            "step_num": step_counter,
            "current": [r, c],
            "data_structure": [list(item) for item in stack],
            "visited": [list(x) for x in visited_order],
            "action": f"스택에서 팝하여 ({r}, {c}) 방문 및 깊이 탐색"
        })
        step_counter += 1

        if (r, c) == (gr, gc):
            found = True
            steps.append({
                "step_num": step_counter,
                "current": [r, c],
                "data_structure": [list(item) for item in stack],
                "visited": [list(x) for x in visited_order],
                "action": f"🎉 목적지 ({gr}, {gc}) 도달!"
            })
            break

        # 인접 노드들을 역순으로 스택에 넣어야 정방향(상, 우, 하, 좌)으로 먼저 팝됨
        valid_neighbors = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 0 and (nr, nc) not in visited_set:
                    valid_neighbors.append((nr, nc))

        # 백트래킹 감지
        if not valid_neighbors and stack:
            steps.append({
                "step_num": step_counter,
                "current": [r, c],
                "data_structure": [list(item) for item in stack],
                "visited": [list(x) for x in visited_order],
                "action": f"막다른 길 ({r}, {c}) 도달 ➜ 이전 갈림길로 백트래킹(Backtracking)"
            })
            step_counter += 1

        for neighbor in reversed(valid_neighbors):
            parent[neighbor] = (r, c)
            stack.append(neighbor)
            steps.append({
                "step_num": step_counter,
                "current": [r, c],
                "data_structure": [list(item) for item in stack],
                "visited": [list(x) for x in visited_order],
                "action": f"다음 탐색 후보 ({neighbor[0]}, {neighbor[1]}) 스택에 푸시"
            })
            step_counter += 1

    # 경로 역추적
    path: List[List[int]] = []
    if found:
        curr: Optional[Tuple[int, int]] = (gr, gc)
        while curr is not None:
            path.append([curr[0], curr[1]])
            curr = parent.get(curr)
        path.reverse()

    return MazeResult(
        algorithm="DFS (깊이 우선 탐색)",
        data_structure_type="Stack (LIFO - 후입선출)",
        found=found,
        path=path,
        path_length=len(path),
        visited_cells_count=len(visited_order),
        total_steps=len(steps),
        peak_memory_size=peak_stack_size,
        steps=steps
    )


# ==============================================================================
# API 엔드포인트 정의
# ==============================================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "BFS vs DFS Maze Escape & Graph Traversal Backend",
        "endpoints": {
            "maze_compare": "/maze/compare",
            "maze_solve": "/maze/solve",
            "graph_traverse": "/traverse",
            "health": "/health"
        }
    }


@app.get("/health")
def healthcheck():
    return {"status": "healthy"}


@app.post("/maze/compare", response_model=MazeComparisonResponse)
def compare_maze_algorithms(req: MazeRequest):
    rows = len(req.grid)
    if rows == 0:
        raise HTTPException(status_code=400, detail="미로 그리드가 비어 있습니다.")
    cols = len(req.grid[0])

    sr, sc = req.start[0], req.start[1]
    gr, gc = req.goal[0], req.goal[1]

    if not (0 <= sr < rows and 0 <= sc < cols):
        raise HTTPException(status_code=400, detail="시작점 좌표가 미로 범위를 벗어납니다.")
    if not (0 <= gr < rows and 0 <= gc < cols):
        raise HTTPException(status_code=400, detail="도착점 좌표가 미로 범위를 벗어납니다.")
    if req.grid[sr][sc] == 1:
        raise HTTPException(status_code=400, detail="시작점이 벽(1)에 위치해 있습니다.")
    if req.grid[gr][gc] == 1:
        raise HTTPException(status_code=400, detail="도착점이 벽(1)에 위치해 있습니다.")

    start_tuple = (sr, sc)
    goal_tuple = (gr, gc)

    bfs_res = solve_maze_bfs(req.grid, start_tuple, goal_tuple)
    dfs_res = solve_maze_dfs(req.grid, start_tuple, goal_tuple)

    # 비교 분석 요약
    shortest_path_algo = "BFS" if bfs_res.path_length <= dfs_res.path_length else "DFS"
    less_visited_algo = "BFS" if bfs_res.visited_cells_count < dfs_res.visited_cells_count else "DFS"
    less_memory_algo = "BFS" if bfs_res.peak_memory_size < dfs_res.peak_memory_size else "DFS"

    summary = {
        "shortest_path_winner": shortest_path_algo,
        "path_length_difference": abs(bfs_res.path_length - dfs_res.path_length),
        "visited_cells_difference": abs(bfs_res.visited_cells_count - dfs_res.visited_cells_count),
        "peak_memory_difference": abs(bfs_res.peak_memory_size - dfs_res.peak_memory_size),
        "bfs_guarantees_shortest_path": True,
        "dfs_guarantees_shortest_path": False,
        "key_takeaway": (
            f"BFS는 큐(Queue)를 통해 동심원 형태로 균등하게 탐색하므로 {bfs_res.path_length}칸의 최단 경로를 반드시 보장합니다. "
            f"반면 DFS는 스택(Stack)을 통해 한 경로를 막다른 길까지 파고들며 {dfs_res.path_length}칸의 우회 경로를 생성할 수 있습니다."
        )
    }

    return MazeComparisonResponse(
        grid_rows=rows,
        grid_cols=cols,
        start=req.start,
        goal=req.goal,
        bfs=bfs_res,
        dfs=dfs_res,
        summary=summary
    )


# ==============================================================================
# 기존 그래프 탐색 호환 엔드포인트
# ==============================================================================

class TraversalRequest(BaseModel):
    algorithm: str = Field(..., description="알고리즘 종류: 'BFS' 또는 'DFS'")
    start_node: str = Field(..., description="탐색 시작 노드 식별자")
    edges: List[List[str]] = Field(..., description="간선 목록 [[출발, 도착], ...]")


@app.post("/traverse")
def traverse_graph(request: TraversalRequest):
    adj: Dict[str, List[str]] = {}
    nodes_set = set()

    for edge in request.edges:
        if len(edge) < 2:
            continue
        u, v = str(edge[0]).strip(), str(edge[1]).strip()
        nodes_set.add(u)
        nodes_set.add(v)
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    for k in adj:
        adj[k].sort()

    start = request.start_node
    if start not in nodes_set:
        nodes_set.add(start)
        adj.setdefault(start, [])

    steps = []
    visited_order = []

    if request.algorithm.upper() == "BFS":
        queue = deque([start])
        visited_set = {start}
        while queue:
            curr = queue.popleft()
            visited_order.append(curr)
            for neighbor in adj.get(curr, []):
                if neighbor not in visited_set:
                    visited_set.add(neighbor)
                    queue.append(neighbor)
                    steps.append({"current": curr, "queue": list(queue), "visited": list(visited_order)})
    else:
        stack = [start]
        visited_set = set()
        while stack:
            curr = stack.pop()
            if curr not in visited_set:
                visited_set.add(curr)
                visited_order.append(curr)
                for neighbor in reversed(adj.get(curr, [])):
                    if neighbor not in visited_set:
                        stack.append(neighbor)
                        steps.append({"current": curr, "queue": list(stack), "visited": list(visited_order)})

    return {
        "algorithm": request.algorithm,
        "start_node": start,
        "total_steps": len(steps),
        "visit_order": visited_order,
        "steps": steps
    }
