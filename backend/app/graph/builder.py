from typing import List, Dict, Any, Tuple, Optional
import math


class GraphBuilder:
    """
    Построитель ориентированного графа из bounding boxes и стрелок.
    Автоматически определяет направление потока (vertical / horizontal).
    """

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.flow = "vertical"

    @staticmethod
    def _detect_flow(nodes: List[Dict[str, Any]], arrows: List[Dict[str, Any]]) -> str:
        if len(nodes) < 2:
            return "vertical"
        xs = [n["x_position"] for n in nodes]
        ys = [n["y_position"] for n in nodes]
        spread_x = max(xs) - min(xs)
        spread_y = max(ys) - min(ys)
        if spread_x > spread_y * 1.6:
            return "horizontal"
        return "vertical"

    def _primary_pos(self, node: Dict[str, Any]) -> float:
        return node["x_position"] if self.flow == "horizontal" else node["y_position"]

    def _secondary_pos(self, node: Dict[str, Any]) -> float:
        return node["y_position"] if self.flow == "horizontal" else node["x_position"]

    def build_graph(
        self,
        shape_elements: List[Dict[str, Any]],
        arrows: List[Dict[str, Any]],
        shape_texts: Dict[str, Dict[str, Any]],
        text_regions: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if text_regions is None:
            text_regions = {}

        nodes = []
        for i, element in enumerate(shape_elements):
            node_id = f"node_{i}"
            bbox = element.get("bbox", [])
            center = self._get_center(bbox)

            shape_id = f"shape_{i}"
            text = shape_texts.get(shape_id, {}).get("text", "")

            if not text:
                text = self._find_associated_text(bbox, text_regions)

            node_type = self._determine_node_type_advanced(element, bbox, center)

            nodes.append({
                "id": node_id,
                "type": node_type,
                "text": text.strip(),
                "bbox": bbox,
                "center": center,
                "y_position": center[1],
                "x_position": center[0],
                "class_name": element.get("class_name", ""),
                "confidence": element.get("confidence", 0.0)
            })

        self.flow = self._detect_flow(nodes, arrows)
        flow_label = "left-to-right" if self.flow == "horizontal" else "top-to-bottom"
        print(f"   Flow direction: {flow_label}")

        if nodes:
            start_node = min(nodes, key=lambda n: self._primary_pos(n))
            if start_node["type"] == "process":
                start_node["type"] = "start"
            qualifier = "leftmost" if self.flow == "horizontal" else "topmost"
            print(f"   Start node: {start_node['id']} - '{start_node['text'][:30]}...' ({qualifier})")

        for node in nodes:
            text_lower = node.get("text", "").lower()
            if "конец" in text_lower or "end" in text_lower or "финиш" in text_lower or "finish" in text_lower:
                node["type"] = "end"
                print(f"   End node: {node['id']} - '{node['text'][:30]}...'")

        edges = self._build_edges(arrows, nodes, text_regions)

        edges = self._connect_orphan_nodes(nodes, edges)

        self._validate_topology(nodes, edges)

        decision_info = self._analyze_decisions(nodes, edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "flow_direction": flow_label,
            "decisions": decision_info
        }
    
    def _build_edges(
        self, 
        arrows: List[Dict[str, Any]], 
        nodes: List[Dict[str, Any]],
        text_regions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Построение рёбер с учётом ветвлений от decision-узлов"""
        edges = []
        
        for arrow in arrows:
            arrow_bbox = arrow.get("bbox", [])
            if len(arrow_bbox) < 4:
                continue
            
            # Определяем связь стрелки
            from_node, to_node, direction = self._find_arrow_connection(arrow_bbox, nodes)
            
            if not from_node or not to_node:
                continue
            
            if from_node["id"] == to_node["id"]:
                continue
            
            edge = {
                "from": from_node["id"],
                "to": to_node["id"],
                "arrow_bbox": arrow_bbox,
                "direction": direction,
                "confidence": arrow.get("confidence", 0.0)
            }
            
            # Для decision-узлов определяем label ветки
            if from_node["type"] == "decision":
                branch_label = self._find_branch_label(from_node, to_node, arrow_bbox, text_regions, direction)
                edge["branch_label"] = branch_label
                edge["decision_branch"] = self._determine_branch_type(
                    from_node, to_node, direction, branch_label
                )
                print(f"   Decision edge: {from_node['id']} --[{branch_label or direction}]--> {to_node['id']}")
            else:
                print(f"   Edge: {from_node['id']} --> {to_node['id']} ({direction})")
            
            edges.append(edge)
        
        return edges
    
    def _find_arrow_connection(
        self,
        arrow_bbox: List[float],
        nodes: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], str]:
        if not nodes or len(arrow_bbox) < 4:
            return None, None, "unknown"

        ax1, ay1, ax2, ay2 = arrow_bbox
        arrow_center = ((ax1 + ax2) / 2, (ay1 + ay2) / 2)

        nearby = []
        for node in nodes:
            dist = self._distance_to_node_edge(arrow_center, node)
            if self._bbox_intersects(arrow_bbox, node.get("bbox", [])):
                dist = min(dist, 10)
            nearby.append((dist, node))

        nearby.sort(key=lambda x: x[0])

        if len(nearby) < 2:
            return None, None, "unknown"

        node_a = nearby[0][1]
        node_b = nearby[1][1]

        dy = node_b["y_position"] - node_a["y_position"]
        dx = node_b["x_position"] - node_a["x_position"]

        if self.flow == "horizontal":
            if abs(dx) > abs(dy) * 0.5:
                if dx > 0:
                    from_node, to_node = node_a, node_b
                    direction = "right"
                else:
                    from_node, to_node = node_b, node_a
                    direction = "right"
            else:
                if dy > 0:
                    from_node, to_node = node_a, node_b
                    direction = "down"
                else:
                    from_node, to_node = node_b, node_a
                    direction = "up"
        else:
            if abs(dy) > abs(dx) * 0.5:
                if dy > 0:
                    from_node, to_node = node_a, node_b
                    direction = "down"
                else:
                    from_node, to_node = node_b, node_a
                    direction = "down"
            else:
                if dx > 0:
                    from_node, to_node = node_a, node_b
                    direction = "right"
                else:
                    from_node, to_node = node_b, node_a
                    direction = "left"

        return from_node, to_node, direction
    
    def _bbox_intersects(self, bbox1: List[float], bbox2: List[float]) -> bool:
        """Проверяет пересечение двух bbox"""
        if len(bbox1) < 4 or len(bbox2) < 4:
            return False
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        return not (x2_1 < x1_2 or x1_1 > x2_2 or y2_1 < y1_2 or y1_1 > y2_2)
    
    def _find_closest_node_to_point(
        self, 
        point: Tuple[float, float], 
        nodes: List[Dict[str, Any]],
        max_distance: float
    ) -> Optional[Dict[str, Any]]:
        """Находит ближайший узел к точке (по краю bbox, не центру)"""
        best_node = None
        best_dist = float('inf')
        
        for node in nodes:
            dist = self._distance_to_node_edge(point, node)
            if dist < best_dist and dist < max_distance:
                best_dist = dist
                best_node = node
        
        return best_node
    
    def _distance_to_node_edge(
        self, 
        point: Tuple[float, float], 
        node: Dict[str, Any]
    ) -> float:
        """Расстояние от точки до ближайшего края bbox узла"""
        bbox = node.get("bbox", [])
        if len(bbox) < 4:
            return self._euclidean_distance(point, node.get("center", (0, 0)))
        
        px, py = point
        x1, y1, x2, y2 = bbox
        
        # Находим ближайшую точку на bbox
        closest_x = max(x1, min(px, x2))
        closest_y = max(y1, min(py, y2))
        
        return self._euclidean_distance(point, (closest_x, closest_y))
    
    def _find_branch_label(
        self,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
        arrow_bbox: List[float],
        text_regions: Dict[str, Dict[str, Any]],
        direction: str
    ) -> str:
        """Ищет label около стрелки или между узлами"""
        if not text_regions:
            return ""
        
        arrow_center = self._get_center(arrow_bbox)
        from_center = from_node["center"]
        to_center = to_node["center"]
        
        mid_point = ((from_center[0] + to_center[0]) / 2, (from_center[1] + to_center[1]) / 2)
        
        best_label = ""
        best_dist = 150
        
        for region in text_regions.values():
            region_bbox = region.get("bbox", [])
            region_text = region.get("text", "").strip()
            
            if not region_bbox or not region_text or len(region_text) > 50:
                continue
            
            region_center = self._get_center(region_bbox)
            
            dist_to_arrow = self._euclidean_distance(arrow_center, region_center)
            dist_to_mid = self._euclidean_distance(mid_point, region_center)
            dist_to_from = self._euclidean_distance(from_center, region_center)
            
            dist = min(dist_to_arrow, dist_to_mid, dist_to_from * 0.8)
            
            if dist < best_dist:
                best_dist = dist
                best_label = region_text
                print(f"      Found label '{region_text}' at distance {dist:.1f}")
        
        return best_label
    
    def _determine_branch_type(
        self,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
        direction: str,
        label: str
    ) -> str:
        """
        Определяет тип ветки decision-узла.
        
        Приоритет:
        1. Явная метка (Да/Нет/Yes/No)
        2. Позиция to_node относительно from_node
        
        Конвенция для flowchart:
        - "no" (Нет) обычно влево или вверх
        - "yes" (Да) обычно вправо или вниз
        """
        label_lower = label.lower() if label else ""
        
        # 1. Явные метки
        if any(w in label_lower for w in ["да", "yes", "true", "истина"]):
            return "yes"
        if any(w in label_lower for w in ["нет", "no", "false", "ложь"]):
            return "no"
        
        # 2. По позиции узлов
        from_x = from_node.get("x_position", 0)
        from_y = from_node.get("y_position", 0)
        to_x = to_node.get("x_position", 0)
        to_y = to_node.get("y_position", 0)
        
        dx = to_x - from_x
        dy = to_y - from_y
        
        # Если to_node СЛЕВА от decision — это обычно "Нет"
        if dx < -30:
            return "no"
        # Если to_node СПРАВА от decision — это обычно "Да"
        elif dx > 30:
            return "yes"
        # Если to_node НИЖЕ (основной поток) — это "Да" (продолжение)
        elif dy > 30:
            return "yes"
        else:
            return "unknown"
    
    def _analyze_decisions(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Анализирует decision-узлы и их ветвления"""
        decisions = []
        
        for node in nodes:
            if node["type"] != "decision":
                continue
            
            node_id = node["id"]
            outgoing = [e for e in edges if e["from"] == node_id]
            
            branches = {}
            for edge in outgoing:
                branch_type = edge.get("decision_branch", "unknown")
                branch_label = edge.get("branch_label", "")
                branches[branch_type] = {
                    "to": edge["to"],
                    "label": branch_label,
                    "direction": edge.get("direction", "")
                }
            
            decisions.append({
                "node_id": node_id,
                "question": node["text"],
                "branches": branches,
                "branch_count": len(outgoing)
            })
            
            print(f"   Decision '{node['text'][:25]}...': {len(outgoing)} branches")
            for bt, info in branches.items():
                print(f"      [{bt}] --> {info['to']} ('{info['label']}')")
        
        return decisions
    
    def _connect_orphan_nodes(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        new_edges = list(edges)

        sorted_nodes = sorted(nodes, key=lambda n: self._primary_pos(n))
        
        # Сначала обрабатываем DECISION узлы — им нужны 2 ветки
        for node in sorted_nodes:
            if node["type"] != "decision":
                continue
            
            node_id = node["id"]
            existing_outgoing = [e for e in new_edges if e["from"] == node_id]
            
            if len(existing_outgoing) >= 2:
                continue  # Уже есть 2 ветки
            
            # Ищем 2 ближайших узла ниже decision (слева и справа)
            branches = self._find_decision_branches(node, sorted_nodes)
            
            existing_to_ids = {e["to"] for e in existing_outgoing}
            
            for branch_node, branch_type in branches:
                if branch_node["id"] in existing_to_ids:
                    continue  # Уже есть такая связь
                
                direction = "left" if branch_node["x_position"] < node["x_position"] else "right"
                new_edge = {
                    "from": node_id,
                    "to": branch_node["id"],
                    "direction": direction,
                    "decision_branch": branch_type,
                    "branch_label": "",
                    "fallback": True,
                    "confidence": 0.5
                }
                new_edges.append(new_edge)
                print(f"   Fallback decision: {node_id} --[{branch_type}]--> {branch_node['id']} ({branch_node['text'][:20]})")
        
        # Собираем узлы, которые являются ПРЯМЫМИ потомками decision (ветки)
        # Эти узлы — "листья", если от них нет ЯВНЫХ (не fallback) стрелок
        decision_branch_targets = set()
        for edge in new_edges:
            if edge.get("decision_branch") or edge.get("fallback"):
                decision_branch_targets.add(edge["to"])
        
        # Проверяем, есть ли ЯВНЫЕ (от YOLO, не fallback) исходящие связи
        has_explicit_outgoing = set()
        for edge in edges:  # Только оригинальные edges от YOLO
            has_explicit_outgoing.add(edge["from"])
        
        # Теперь обрабатываем остальные узлы
        has_incoming = {e["to"] for e in new_edges}
        has_outgoing = {e["from"] for e in new_edges}
        
        for i, node in enumerate(sorted_nodes):
            node_id = node["id"]
            node_type = node["type"]
            
            if node_type in ["end", "decision"]:
                continue
            
            # Если узел — прямой потомок decision И нет явных исходящих → проверяем, есть ли блок прямо под ним
            if node_id in decision_branch_targets and node_id not in has_explicit_outgoing:
                has_block_forward = False
                for other in sorted_nodes:
                    if other["id"] == node_id or other["type"] == "decision":
                        continue
                    dp = self._primary_pos(other) - self._primary_pos(node)
                    ds = abs(self._secondary_pos(other) - self._secondary_pos(node))
                    if 0 < dp < 150 and ds < 80:
                        has_block_forward = True
                        break

                if not has_block_forward:
                    print(f"   Leaf node (decision branch): {node_id} - '{node['text'][:25]}...'")
                    continue
            
            if node_id not in has_outgoing:
                next_node = self._find_next_node_forward(node, sorted_nodes[i+1:], has_incoming, sorted_nodes)
                if next_node:
                    fb_dir = "right" if self.flow == "horizontal" else "down"
                    new_edge = {
                        "from": node_id,
                        "to": next_node["id"],
                        "direction": fb_dir,
                        "fallback": True,
                        "confidence": 0.5
                    }
                    new_edges.append(new_edge)
                    has_outgoing.add(node_id)
                    has_incoming.add(next_node["id"])
                    print(f"   Fallback edge: {node_id} --> {next_node['id']}")
        
        return new_edges
    
    def _find_decision_branches(
        self,
        decision: Dict[str, Any],
        all_nodes: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], str]]:
        dec_p = self._primary_pos(decision)
        dec_s = self._secondary_pos(decision)

        candidates_low = []
        candidates_high = []

        for node in all_nodes:
            if node["id"] == decision["id"] or node["type"] == "decision":
                continue

            dp = self._primary_pos(node) - dec_p
            ds = self._secondary_pos(node) - dec_s

            if dp < -20:
                continue

            dist = abs(ds) + dp * 0.5

            if ds < -20:
                candidates_low.append((dist, node))
            elif ds > 20:
                candidates_high.append((dist, node))
            else:
                candidates_high.append((dist, node))

        result = []
        if candidates_low:
            candidates_low.sort(key=lambda x: x[0])
            result.append((candidates_low[0][1], "no"))
        if candidates_high:
            candidates_high.sort(key=lambda x: x[0])
            result.append((candidates_high[0][1], "yes"))

        return result
    
    def _find_next_node_forward(
        self,
        current: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        has_incoming: set,
        all_nodes: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        cur_p = self._primary_pos(current)
        cur_s = self._secondary_pos(current)

        if all_nodes:
            center_s = sum(self._secondary_pos(n) for n in all_nodes) / len(all_nodes)
        else:
            center_s = cur_s

        cur_side = "low" if cur_s < center_s - 50 else ("high" if cur_s > center_s + 50 else "center")

        best = None
        best_score = float('inf')

        for node in candidates:
            if self._primary_pos(node) <= cur_p:
                continue

            node_s = self._secondary_pos(node)
            node_side = "low" if node_s < center_s - 50 else ("high" if node_s > center_s + 50 else "center")

            if cur_side == "low" and node_side == "high":
                continue
            if cur_side == "high" and node_side == "low":
                continue

            dp = self._primary_pos(node) - cur_p
            ds = abs(self._secondary_pos(node) - cur_s)

            score = dp + ds * 3

            if node["id"] not in has_incoming:
                score *= 0.5
            if cur_side == node_side:
                score *= 0.7

            if score < best_score:
                best_score = score
                best = node

        return best
    
    def _find_alternative_branch(
        self,
        decision: Dict[str, Any],
        all_nodes: List[Dict[str, Any]],
        existing_to: str
    ) -> Optional[Dict[str, Any]]:
        """Находит альтернативную ветку для decision (слева или справа)"""
        dec_y = decision["y_position"]
        dec_x = decision["x_position"]
        
        # Ищем узлы примерно на том же уровне по Y (или чуть ниже)
        candidates = []
        for node in all_nodes:
            if node["id"] == decision["id"] or node["id"] == existing_to:
                continue
            
            dy = node["y_position"] - dec_y
            dx = abs(node["x_position"] - dec_x)
            
            # Узел должен быть ниже decision и не слишком далеко
            if 0 < dy < 200 and dx > 50:
                candidates.append((dy + dx, node))
        
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        
        return None

    def _get_center(self, bbox: List[float]) -> Tuple[float, float]:
        if len(bbox) < 4:
            return (0.0, 0.0)
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _euclidean_distance(
        self, 
        p1: Tuple[float, float], 
        p2: Tuple[float, float]
    ) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _find_associated_text(
        self, 
        element_bbox: List[float], 
        text_regions: Dict[str, Dict[str, Any]]
    ) -> str:
        if not text_regions:
            return ""
        
        element_center = self._get_center(element_bbox)
        min_distance = float('inf')
        closest_text = ""
        
        for region_data in text_regions.values():
            region_bbox = region_data.get("bbox", [])
            if not region_bbox:
                continue
            
            region_center = self._get_center(region_bbox)
            distance = self._euclidean_distance(element_center, region_center)
            
            if self._is_inside(region_bbox, element_bbox) or distance < 80:
                if distance < min_distance:
                    min_distance = distance
                    closest_text = region_data.get("text", "")
        
        return closest_text.strip()
    
    def _is_inside(self, inner: List[float], outer: List[float]) -> bool:
        if len(inner) < 4 or len(outer) < 4:
            return False
        cx, cy = self._get_center(inner)
        ox1, oy1, ox2, oy2 = outer
        return ox1 <= cx <= ox2 and oy1 <= cy <= oy2
    
    def _determine_node_type_advanced(
        self, 
        element: Dict[str, Any], 
        bbox: List[float],
        center: Tuple[float, float]
    ) -> str:
        class_name = element.get("class_name", "").lower()
        
        if "start" in class_name or "begin" in class_name:
            return "start"
        elif "end" in class_name or "stop" in class_name or "finish" in class_name:
            return "end"
        elif "decision" in class_name or "diamond" in class_name or "condition" in class_name:
            return "decision"
        elif "process" in class_name or "rectangle" in class_name:
            return "process"
        elif "circle" in class_name or "ellipse" in class_name:
            return "process"
        else:
            return "process"
    
    def _validate_topology(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ):
        in_degree = {n["id"]: 0 for n in nodes}
        out_degree = {n["id"]: 0 for n in nodes}
        
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            if from_id and to_id:
                out_degree[from_id] = out_degree.get(from_id, 0) + 1
                in_degree[to_id] = in_degree.get(to_id, 0) + 1
        
        for node in nodes:
            nid = node["id"]
            ntype = node["type"]
            out_deg = out_degree.get(nid, 0)
            
            if ntype == "decision" and out_deg < 2:
                print(f"   Warning: Decision {nid} has only {out_deg} outputs (expected 2)")
            
            for edge in edges:
                if edge["from"] == nid:
                    to_node = next((n for n in nodes if n["id"] == edge["to"]), None)
                    if to_node and self._primary_pos(to_node) < self._primary_pos(node):
                        edge["is_loop"] = True


def build_graph_from_detections(
    shape_elements: List[Dict[str, Any]],
    arrows: List[Dict[str, Any]],
    shape_texts: Dict[str, Dict[str, Any]],
    text_regions: Dict[str, Dict[str, Any]] = None
) -> Dict[str, Any]:
    builder = GraphBuilder()
    return builder.build_graph(shape_elements, arrows, shape_texts, text_regions)
