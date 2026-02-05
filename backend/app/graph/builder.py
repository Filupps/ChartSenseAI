from typing import List, Dict, Any, Tuple, Optional
import math


class GraphBuilder:
    """
    Построитель ориентированного графа из bounding boxes и стрелок
    с улучшенными геометрическими и топологическими эвристиками для ветвлений
    """
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def build_graph(
        self, 
        shape_elements: List[Dict[str, Any]], 
        arrows: List[Dict[str, Any]],
        shape_texts: Dict[str, Dict[str, Any]],
        text_regions: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Построение графа с корректной обработкой ветвлений (diamond/decision)"""
        if text_regions is None:
            text_regions = {}
        
        # Создаем узлы
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
        
        # Определяем START (самый верхний)
        if nodes:
            start_node = min(nodes, key=lambda n: n["y_position"])
            if start_node["type"] == "process":
                start_node["type"] = "start"
                print(f"   Start node: {start_node['id']} - '{start_node['text'][:30]}...' (topmost)")
        
        # Определяем ВСЕ END узлы (по тексту "Конец" или "End")
        for node in nodes:
            text_lower = node.get("text", "").lower()
            if "конец" in text_lower or "end" in text_lower or "финиш" in text_lower or "finish" in text_lower:
                node["type"] = "end"
                print(f"   End node: {node['id']} - '{node['text'][:30]}...'")
        
        # Создаем ребра с улучшенным определением связей
        edges = self._build_edges(arrows, nodes, text_regions)
        
        # FALLBACK: Если узлы не связаны, соединяем их по Y-позиции
        edges = self._connect_orphan_nodes(nodes, edges)
        
        # Валидация
        self._validate_topology(nodes, edges)
        
        # Добавляем метаданные о ветвлениях
        decision_info = self._analyze_decisions(nodes, edges)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "flow_direction": "top-to-bottom",
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
                branch_label = self._find_branch_label(arrow_bbox, text_regions, direction)
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
        """
        Находит from/to узлы для стрелки.
        
        ВАЖНО: bbox стрелки часто пересекается с узлами (особенно с diamond).
        Поэтому ищем 2 ближайших узла к центру стрелки и определяем направление
        по их взаимному расположению.
        """
        if not nodes or len(arrow_bbox) < 4:
            return None, None, "unknown"
        
        ax1, ay1, ax2, ay2 = arrow_bbox
        arrow_center = ((ax1 + ax2) / 2, (ay1 + ay2) / 2)
        
        # Находим все узлы рядом со стрелкой и их расстояния
        nearby = []
        for node in nodes:
            dist = self._distance_to_node_edge(arrow_center, node)
            # Проверяем также пересечение bbox
            if self._bbox_intersects(arrow_bbox, node.get("bbox", [])):
                dist = min(dist, 10)  # Приоритет пересекающимся
            nearby.append((dist, node))
        
        nearby.sort(key=lambda x: x[0])
        
        if len(nearby) < 2:
            return None, None, "unknown"
        
        # Берём 2 ближайших узла
        node_a = nearby[0][1]
        node_b = nearby[1][1]
        
        # Определяем кто from, кто to по Y-позиции (сверху вниз = основной поток)
        # и X-позиции (для горизонтальных стрелок)
        ay_a = node_a["y_position"]
        ay_b = node_b["y_position"]
        ax_a = node_a["x_position"]
        ax_b = node_b["x_position"]
        
        dy = ay_b - ay_a
        dx = ax_b - ax_a
        
        # Определяем направление
        if abs(dy) > abs(dx) * 0.5:
            # Вертикальное движение
            if dy > 0:
                from_node, to_node = node_a, node_b
                direction = "down"
            else:
                from_node, to_node = node_b, node_a
                direction = "down"
        else:
            # Горизонтальное движение
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
        arrow_bbox: List[float],
        text_regions: Dict[str, Dict[str, Any]],
        direction: str
    ) -> str:
        """Ищет label около стрелки (например, "Товар", "Услуга", "Да", "Нет")"""
        if not text_regions:
            return ""
        
        arrow_center = self._get_center(arrow_bbox)
        best_label = ""
        best_dist = 80  # Максимальное расстояние для label
        
        for region in text_regions.values():
            region_bbox = region.get("bbox", [])
            if not region_bbox:
                continue
            
            region_center = self._get_center(region_bbox)
            dist = self._euclidean_distance(arrow_center, region_center)
            
            if dist < best_dist:
                text = region.get("text", "").strip()
                if text and len(text) < 30:  # Label обычно короткий
                    best_dist = dist
                    best_label = text
        
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
        """
        FALLBACK: соединяет узлы без связей с ближайшими по Y-позиции.
        Для decision-узлов ищет ОБЕ ветки сразу.
        """
        new_edges = list(edges)
        
        # Сортируем узлы по Y (сверху вниз)
        sorted_nodes = sorted(nodes, key=lambda n: n["y_position"])
        
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
                # Проверяем, есть ли блок близко под этим узлом (dy < 150, dx < 80)
                has_block_below = False
                for other in sorted_nodes:
                    if other["id"] == node_id or other["type"] == "decision":
                        continue
                    dy = other["y_position"] - node["y_position"]
                    dx = abs(other["x_position"] - node["x_position"])
                    if 0 < dy < 150 and dx < 80:
                        has_block_below = True
                        break
                
                if not has_block_below:
                    print(f"   Leaf node (decision branch): {node_id} - '{node['text'][:25]}...'")
                    continue
            
            if node_id not in has_outgoing:
                next_node = self._find_next_node_below(node, sorted_nodes[i+1:], has_incoming, sorted_nodes)
                if next_node:
                    new_edge = {
                        "from": node_id,
                        "to": next_node["id"],
                        "direction": "down",
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
        """Находит 2 ветки для decision: одну слева, одну справа (или ниже)"""
        dec_x = decision["x_position"]
        dec_y = decision["y_position"]
        
        # Кандидаты: узлы ниже decision
        candidates_left = []
        candidates_right = []
        
        for node in all_nodes:
            if node["id"] == decision["id"]:
                continue
            if node["type"] == "decision":
                continue  # Пропускаем другие decision
            
            dy = node["y_position"] - dec_y
            dx = node["x_position"] - dec_x
            
            # Узел должен быть ниже (или почти на том же уровне)
            if dy < -20:
                continue
            
            dist = abs(dx) + dy * 0.5  # Приоритет ближним по X
            
            if dx < -20:  # Слева
                candidates_left.append((dist, node))
            elif dx > 20:  # Справа
                candidates_right.append((dist, node))
            else:  # По центру (ниже) — это "yes" ветка
                candidates_right.append((dist, node))
        
        result = []
        
        # Берём ближайший слева → "no"
        if candidates_left:
            candidates_left.sort(key=lambda x: x[0])
            result.append((candidates_left[0][1], "no"))
        
        # Берём ближайший справа/снизу → "yes"
        if candidates_right:
            candidates_right.sort(key=lambda x: x[0])
            result.append((candidates_right[0][1], "yes"))
        
        return result
    
    def _find_next_node_below(
        self,
        current: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        has_incoming: set,
        all_nodes: List[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Находит следующий узел ниже текущего.
        
        ВАЖНО: не соединяем узлы с разных веток (левая/правая стороны)
        """
        current_y = current["y_position"]
        current_x = current["x_position"]
        
        # Определяем центральную линию диаграммы
        if all_nodes:
            center_x = sum(n["x_position"] for n in all_nodes) / len(all_nodes)
        else:
            center_x = current_x
        
        # Определяем, на какой стороне находится текущий узел
        current_side = "left" if current_x < center_x - 50 else ("right" if current_x > center_x + 50 else "center")
        
        best = None
        best_score = float('inf')
        
        for node in candidates:
            if node["y_position"] <= current_y:
                continue
            
            # Определяем сторону кандидата
            node_side = "left" if node["x_position"] < center_x - 50 else ("right" if node["x_position"] > center_x + 50 else "center")
            
            # Если текущий узел на краю (left/right), соединяем только с узлами той же стороны или центра
            if current_side == "left" and node_side == "right":
                continue
            if current_side == "right" and node_side == "left":
                continue
            
            dy = node["y_position"] - current_y
            dx = abs(node["x_position"] - current_x)
            
            # Предпочитаем узлы близко по X
            score = dy + dx * 3
            
            # Бонус узлам без входящих связей
            if node["id"] not in has_incoming:
                score *= 0.5
            
            # Бонус узлам на той же стороне
            if current_side == node_side:
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
            
            # Определяем циклы
            for edge in edges:
                if edge["from"] == nid:
                    to_node = next((n for n in nodes if n["id"] == edge["to"]), None)
                    if to_node and to_node["y_position"] < node["y_position"]:
                        edge["is_loop"] = True


def build_graph_from_detections(
    shape_elements: List[Dict[str, Any]],
    arrows: List[Dict[str, Any]],
    shape_texts: Dict[str, Dict[str, Any]],
    text_regions: Dict[str, Dict[str, Any]] = None
) -> Dict[str, Any]:
    builder = GraphBuilder()
    return builder.build_graph(shape_elements, arrows, shape_texts, text_regions)
