"""
Google Cloud Run 배포용 FastAPI 백엔드 서버
파일: main.py
목적: BFS(너비 우선 탐색) 및 DFS(깊이 우선 탐색) 단계별 스냅샷 데이터 제공
"""

from typing import List, Dict, Any, Optional
from collections import deque
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="BFS & DFS Graph Traversal API",
    description="Google Cloud Run용 BFS & DFS 그래프 탐색 알고리즘 시각화 백엔드",
    version="1.0.0"
)

# CORS 설정 (Google Apps Script 및 외부 웹앱 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TraversalRequest(BaseModel):
    algorithm: str = Field(..., description="알고리즘 종류: 'BFS' 또는 'DFS'", example="BFS")
    start_node: str = Field(..., description="탐색 시작 노드 식별자", example="A")
    edges: List[List[str]] = Field(
        ...,
        description="간선 목록 [[출발, 도착], ...]",
        example=[["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"], ["E", "F"]]
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algo(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("BFS", "DFS"):
            raise ValueError("알고리즘은 'BFS' 또는 'DFS'이어야 합니다.")
        return upper

    @field_validator("start_node")
    @classmethod
    def validate_start(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("시작 노드는 비어 있을 수 없습니다.")
        return v.strip()


class StepDetail(BaseModel):
    step_num: int
    current: Optional[str]
    queue_or_stack: List[str]
    visited: List[str]
    message: str


class TraversalResponse(BaseModel):
    algorithm: str
    start_node: str
    total_steps: int
    visit_order: List[str]
    steps: List[Dict[str, Any]]


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "BFS & DFS Graph Traversal Service",
        "docs_url": "/docs"
    }


@app.get("/health")
def healthcheck():
    return {"status": "healthy"}


@app.post("/traverse", response_model=TraversalResponse)
def traverse(request: TraversalRequest):
    # 인접 리스트 (Adjacency List) 생성 (양방향 무방향 그래프 기준)
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

    # 결정론적(사전순) 정렬
    for k in adj:
        adj[k].sort()

    start = request.start_node
    if start not in nodes_set:
        nodes_set.add(start)
        adj.setdefault(start, [])

    steps: List[Dict[str, Any]] = []
    visited_order: List[str] = []

    if request.algorithm == "BFS":
        # BFS (너비 우선 탐색 - Queue 기반)
        queue = deque([start])
        visited_set = {start}

        steps.append({
            "step_num": 1,
            "current": start,
            "queue": list(queue),
            "visited": list(visited_set),
            "action": f"시작 노드 [{start}] 큐에 삽입 및 방문 예약"
        })

        step_counter = 2
        while queue:
            curr = queue.popleft()
            visited_order.append(curr)

            steps.append({
                "step_num": step_counter,
                "current": curr,
                "queue": list(queue),
                "visited": list(visited_order),
                "action": f"노드 [{curr}] 방문 완료 (큐에서 추출)"
            })
            step_counter += 1

            for neighbor in adj.get(curr, []):
                if neighbor not in visited_set:
                    visited_set.add(neighbor)
                    queue.append(neighbor)
                    steps.append({
                        "step_num": step_counter,
                        "current": curr,
                        "queue": list(queue),
                        "visited": list(visited_order),
                        "action": f"인접 노드 [{neighbor}] 발견 ➜ 큐에 추가"
                    })
                    step_counter += 1

    else:
        # DFS (깊이 우선 탐색 - Stack 기반)
        stack = [start]
        visited_set = set()

        step_counter = 1
        steps.append({
            "step_num": step_counter,
            "current": start,
            "queue": list(stack),
            "visited": list(visited_order),
            "action": f"시작 노드 [{start}] 스택에 푸시"
        })
        step_counter += 1

        while stack:
            curr = stack.pop()
            if curr not in visited_set:
                visited_set.add(curr)
                visited_order.append(curr)

                steps.append({
                    "step_num": step_counter,
                    "current": curr,
                    "queue": list(stack),
                    "visited": list(visited_order),
                    "action": f"노드 [{curr}] 방문 완료 (스택에서 팝)"
                })
                step_counter += 1

                # 역순으로 스택에 넣어야 사전순으로 먼저 꺼내짐
                neighbors = adj.get(curr, [])
                for neighbor in reversed(neighbors):
                    if neighbor not in visited_set:
                        stack.append(neighbor)
                        steps.append({
                            "step_num": step_counter,
                            "current": curr,
                            "queue": list(stack),
                            "visited": list(visited_order),
                            "action": f"인접 노드 [{neighbor}] 발견 ➜ 스택에 푸시"
                        })
                        step_counter += 1

    return TraversalResponse(
        algorithm=request.algorithm,
        start_node=start,
        total_steps=len(steps),
        visit_order=visited_order,
        steps=steps
    )
