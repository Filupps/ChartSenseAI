from typing import Dict, Any, List, Optional, Set


class AlgorithmGenerator:
    """
    Генератор структурированного алгоритма из графа диаграммы
    с корректной обработкой ветвлений (IF-ELSE)
    """
    
    def __init__(self):
        self.nodes_map = {}
        self.edges_by_from = {}
        self.edges_by_to = {}
    
    def generate_algorithm(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация структурированного алгоритма с ветвлениями
        
        Returns:
            {
                "steps": [...],           # Плоский список шагов
                "structured": [...],      # Структурированный алгоритм с IF-ELSE
                "structure": {...}        # Метаданные
            }
        """
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        decisions = graph.get("decisions", [])
        
        if not nodes:
            return {"steps": [], "structured": [], "structure": {}}
        
        # Индексируем данные
        self.nodes_map = {n["id"]: n for n in nodes}
        self.edges_by_from = {}
        self.edges_by_to = {}
        
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            if from_id:
                self.edges_by_from.setdefault(from_id, []).append(edge)
            if to_id:
                self.edges_by_to.setdefault(to_id, []).append(edge)
        
        # Находим начальный узел
        start_node = self._find_start_node(nodes)
        if not start_node:
            start_node = min(nodes, key=lambda n: n.get("y_position", 0))
        
        # Генерируем структурированный алгоритм
        visited = set()
        structured = self._traverse_graph(start_node["id"], visited)
        
        # Генерируем плоский список шагов
        steps = self._flatten_structured(structured)
        
        return {
            "steps": steps,
            "structured": structured,
            "decisions": decisions,
            "structure": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "decision_count": len(decisions),
                "visited_nodes": len(visited)
            }
        }
    
    def _traverse_graph(
        self, 
        node_id: str, 
        visited: Set[str],
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Рекурсивный обход графа с обработкой ветвлений
        
        Returns:
            Список структурированных шагов
        """
        if node_id in visited or depth > 50:
            return []
        
        visited.add(node_id)
        node = self.nodes_map.get(node_id)
        if not node:
            return []
        
        result = []
        
        if node["type"] == "decision":
            # Обрабатываем ветвление
            result.append(self._create_decision_step(node, visited, depth))
        else:
            # Обычный узел
            result.append(self._create_step(node))
            
            # Переходим к следующему узлу
            outgoing = self.edges_by_from.get(node_id, [])
            if outgoing:
                next_edge = outgoing[0]
                next_id = next_edge.get("to")
                if next_id and next_id not in visited:
                    result.extend(self._traverse_graph(next_id, visited, depth))
        
        return result
    
    def _create_decision_step(
        self, 
        node: Dict[str, Any],
        visited: Set[str],
        depth: int
    ) -> Dict[str, Any]:
        """Создаёт шаг с ветвлением IF-ELSE"""
        node_id = node["id"]
        outgoing = self.edges_by_from.get(node_id, [])
        
        # Сортируем ветки: left/no идут в else, right/yes/down в then
        branches = {"then": None, "else": None}
        branch_labels = {"then": "", "else": ""}
        
        for edge in outgoing:
            branch_type = edge.get("decision_branch", "down")
            branch_label = edge.get("branch_label", "")
            to_id = edge.get("to")
            
            if branch_type in ["left", "no"]:
                branches["else"] = to_id
                branch_labels["else"] = branch_label
            else:
                # right, yes, down → основная ветка
                if branches["then"] is None:
                    branches["then"] = to_id
                    branch_labels["then"] = branch_label
                else:
                    branches["else"] = to_id
                    branch_labels["else"] = branch_label
        
        # Если обе ветки не определены, берём по порядку
        if branches["then"] is None and branches["else"] is None and outgoing:
            if len(outgoing) >= 1:
                branches["then"] = outgoing[0].get("to")
                branch_labels["then"] = outgoing[0].get("branch_label", "")
            if len(outgoing) >= 2:
                branches["else"] = outgoing[1].get("to")
                branch_labels["else"] = outgoing[1].get("branch_label", "")
        
        # Находим точку слияния (merge point)
        merge_point = self._find_merge_point(branches["then"], branches["else"])
        
        # Рекурсивно обходим ветки (до точки слияния)
        then_steps = []
        else_steps = []
        
        visited_copy = visited.copy()  # Не портим visited для второй ветки
        
        if branches["then"]:
            then_steps = self._traverse_branch(
                branches["then"], visited_copy, merge_point, depth + 1
            )
        
        if branches["else"]:
            else_steps = self._traverse_branch(
                branches["else"], visited, merge_point, depth + 1
            )
        
        # Объединяем visited
        visited.update(visited_copy)
        
        step = {
            "type": "decision",
            "id": node_id,
            "condition": node.get("text", "Условие"),
            "then": {
                "label": branch_labels["then"],
                "steps": then_steps
            },
            "else": {
                "label": branch_labels["else"],
                "steps": else_steps
            }
        }
        
        # Добавляем продолжение после слияния
        if merge_point and merge_point not in visited:
            step["merge_point"] = merge_point
            continuation = self._traverse_graph(merge_point, visited, depth)
            step["after_merge"] = continuation
        
        return step
    
    def _traverse_branch(
        self, 
        start_id: str, 
        visited: Set[str], 
        stop_at: Optional[str],
        depth: int
    ) -> List[Dict[str, Any]]:
        """Обходит ветку до точки слияния"""
        result = []
        current_id = start_id
        
        while current_id and current_id not in visited and depth < 50:
            if current_id == stop_at:
                break
            
            visited.add(current_id)
            node = self.nodes_map.get(current_id)
            if not node:
                break
            
            if node["type"] == "decision":
                result.append(self._create_decision_step(node, visited, depth))
                break  # decision сам обрабатывает продолжение
            else:
                result.append(self._create_step(node))
                
                outgoing = self.edges_by_from.get(current_id, [])
                if outgoing:
                    next_id = outgoing[0].get("to")
                    if next_id == stop_at:
                        break
                    current_id = next_id
                else:
                    break
            
            depth += 1
        
        return result
    
    def _find_merge_point(
        self, 
        branch1_start: Optional[str], 
        branch2_start: Optional[str]
    ) -> Optional[str]:
        """Находит точку слияния двух веток"""
        if not branch1_start or not branch2_start:
            return None
        
        # Собираем все узлы, достижимые из каждой ветки
        reachable1 = self._get_reachable_nodes(branch1_start, set(), 20)
        reachable2 = self._get_reachable_nodes(branch2_start, set(), 20)
        
        # Ищем общий узел с минимальной y-позицией (самый верхний общий)
        common = reachable1 & reachable2
        
        if not common:
            return None
        
        # Берём самый верхний общий узел (наименьший y)
        merge_candidates = [
            (self.nodes_map[nid].get("y_position", 0), nid) 
            for nid in common if nid in self.nodes_map
        ]
        
        if merge_candidates:
            merge_candidates.sort()
            return merge_candidates[0][1]
        
        return None
    
    def _get_reachable_nodes(
        self, 
        start_id: str, 
        visited: Set[str],
        max_depth: int
    ) -> Set[str]:
        """Возвращает все узлы, достижимые из start_id"""
        if max_depth <= 0 or start_id in visited:
            return set()
        
        visited.add(start_id)
        result = {start_id}
        
        outgoing = self.edges_by_from.get(start_id, [])
        for edge in outgoing:
            to_id = edge.get("to")
            if to_id:
                result.update(self._get_reachable_nodes(to_id, visited.copy(), max_depth - 1))
        
        return result
    
    def _create_step(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Создаёт простой шаг"""
        return {
            "type": node.get("type", "process"),
            "id": node["id"],
            "text": node.get("text", "") or self._type_to_text(node.get("type", "process"))
        }
    
    def _type_to_text(self, node_type: str) -> str:
        return {
            "start": "Начало",
            "end": "Конец",
            "decision": "Условие",
            "process": "Процесс"
        }.get(node_type, "Шаг")
    
    def _find_start_node(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for node in nodes:
            if node.get("type") == "start":
                return node
        return None
    
    def _flatten_structured(self, structured: List[Dict[str, Any]], indent: int = 0) -> List[str]:
        """Преобразует структурированный алгоритм в плоский список с отступами"""
        result = []
        prefix = "  " * indent
        
        for item in structured:
            if item.get("type") == "decision":
                # IF-ELSE блок
                condition = item.get("condition", "Условие")
                result.append(f"{prefix}ЕСЛИ {condition}:")
                
                then_block = item.get("then", {})
                then_label = then_block.get("label", "Да")
                then_steps = then_block.get("steps", [])
                
                result.append(f"{prefix}  [{then_label or 'Да'}]:")
                result.extend(self._flatten_structured(then_steps, indent + 2))
                
                else_block = item.get("else", {})
                else_label = else_block.get("label", "Нет")
                else_steps = else_block.get("steps", [])
                
                if else_steps:
                    result.append(f"{prefix}  [{else_label or 'Нет'}]:")
                    result.extend(self._flatten_structured(else_steps, indent + 2))
                
                result.append(f"{prefix}КОНЕЦ_ЕСЛИ")
                
                # После слияния
                after_merge = item.get("after_merge", [])
                if after_merge:
                    result.extend(self._flatten_structured(after_merge, indent))
            else:
                # Обычный шаг
                text = item.get("text", "Шаг")
                step_type = item.get("type", "process")
                
                if step_type == "start":
                    result.append(f"{prefix}НАЧАЛО: {text}")
                elif step_type == "end":
                    result.append(f"{prefix}КОНЕЦ: {text}")
                else:
                    result.append(f"{prefix}→ {text}")
        
        return result


def generate_algorithm_from_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    generator = AlgorithmGenerator()
    return generator.generate_algorithm(graph)
