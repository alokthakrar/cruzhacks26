"""
Knowledge Graph Service

Handles knowledge graph CRUD operations and DAG traversal for prerequisite/dependency logic.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.knowledge_graph import KnowledgeGraph, ConceptNode
from ..models.user_mastery import UserMastery, ConceptMastery
from bson import ObjectId


class GraphService:
    """Service for knowledge graph management and traversal."""
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.graphs_collection = db["knowledge_graphs"] if db is not None else None
        self.mastery_collection = db["user_mastery"] if db is not None else None
    
    # ===== Graph CRUD Operations =====
    
    async def create_graph(
        self,
        subject_id: str,
        created_by: str,
        nodes: Dict[str, ConceptNode]
    ) -> str:
        """
        Create a new knowledge graph for a subject.
        
        Args:
            subject_id: Subject this graph belongs to
            created_by: User ID who created the graph
            nodes: Dictionary of concept_id -> ConceptNode
        
        Returns:
            Graph ID (str)
        """
        # Calculate root concepts (nodes with no parents)
        root_concepts = [
            concept_id
            for concept_id, node in nodes.items()
            if not node.parents
        ]
        
        # Calculate depth for each node (topological ordering)
        nodes_with_depth = self._calculate_depths(nodes)
        
        graph_doc = {
            "_id": str(ObjectId()),
            "subject_id": subject_id,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "nodes": {
                concept_id: node.model_dump(by_alias=False)
                for concept_id, node in nodes_with_depth.items()
            },
            "root_concepts": root_concepts
        }
        
        await self.graphs_collection.insert_one(graph_doc)
        return graph_doc["_id"]
    
    async def get_graph(self, subject_id: str) -> Optional[KnowledgeGraph]:
        """Get knowledge graph for a subject."""
        graph_doc = await self.graphs_collection.find_one({"subject_id": subject_id})
        if not graph_doc:
            return None
        
        # Convert dict nodes back to ConceptNode objects
        nodes = {
            concept_id: ConceptNode(**node_data)
            for concept_id, node_data in graph_doc["nodes"].items()
        }
        graph_doc["nodes"] = nodes
        
        return KnowledgeGraph(**graph_doc)
    
    async def update_graph(
        self,
        subject_id: str,
        nodes: Dict[str, ConceptNode]
    ) -> bool:
        """Update an existing knowledge graph."""
        # Recalculate depths and roots
        nodes_with_depth = self._calculate_depths(nodes)
        root_concepts = [
            concept_id
            for concept_id, node in nodes_with_depth.items()
            if not node.parents
        ]
        
        result = await self.graphs_collection.update_one(
            {"subject_id": subject_id},
            {
                "$set": {
                    "nodes": {
                        concept_id: node.model_dump(by_alias=False)
                        for concept_id, node in nodes_with_depth.items()
                    },
                    "root_concepts": root_concepts,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def delete_graph(self, subject_id: str) -> bool:
        """Delete a knowledge graph."""
        result = await self.graphs_collection.delete_one({"subject_id": subject_id})
        return result.deleted_count > 0
    
    # ===== DAG Traversal Operations =====
    
    def _calculate_depths(self, nodes: Dict[str, ConceptNode]) -> Dict[str, ConceptNode]:
        """
        Calculate depth for each node using topological sort.
        
        Depth = maximum distance from any root node.
        Root nodes have depth 0.
        """
        depths = {}
        visited = set()
        
        def dfs(concept_id: str) -> int:
            if concept_id in depths:
                return depths[concept_id]
            
            if concept_id in visited:
                # Cycle detected - shouldn't happen in DAG, but handle gracefully
                return 0
            
            visited.add(concept_id)
            node = nodes.get(concept_id)
            
            if not node or not node.parents:
                # Root node or missing node
                depth = 0
            else:
                # Depth = max(parent depths) + 1
                parent_depths = [dfs(parent_id) for parent_id in node.parents if parent_id in nodes]
                depth = max(parent_depths, default=0) + 1
            
            depths[concept_id] = depth
            visited.remove(concept_id)
            return depth
        
        # Calculate depth for all nodes
        for concept_id in nodes.keys():
            dfs(concept_id)
        
        # Update node objects with calculated depths
        result = {}
        for concept_id, node in nodes.items():
            node_dict = node.model_dump()
            node_dict["depth"] = depths.get(concept_id, 0)
            result[concept_id] = ConceptNode(**node_dict)
        
        return result
    
    def get_prerequisites(
        self,
        graph: KnowledgeGraph,
        concept_id: str,
        recursive: bool = False
    ) -> List[str]:
        """
        Get prerequisite concepts (parents in the DAG).
        
        Args:
            graph: Knowledge graph
            concept_id: Concept to get prerequisites for
            recursive: If True, get all ancestors; if False, only direct parents
        
        Returns:
            List of prerequisite concept_ids
        """
        if concept_id not in graph.nodes:
            return []
        
        if not recursive:
            return graph.nodes[concept_id].parents
        
        # Recursive: get all ancestors via BFS
        prerequisites = set()
        queue = [concept_id]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            if current in graph.nodes:
                parents = graph.nodes[current].parents
                prerequisites.update(parents)
                queue.extend(parents)
        
        return list(prerequisites)
    
    def get_dependents(
        self,
        graph: KnowledgeGraph,
        concept_id: str,
        recursive: bool = False
    ) -> List[str]:
        """
        Get dependent concepts (children in the DAG).
        
        Args:
            graph: Knowledge graph
            concept_id: Concept to get dependents for
            recursive: If True, get all descendants; if False, only direct children
        
        Returns:
            List of dependent concept_ids
        """
        if concept_id not in graph.nodes:
            return []
        
        if not recursive:
            return graph.nodes[concept_id].children
        
        # Recursive: get all descendants via BFS
        dependents = set()
        queue = [concept_id]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            if current in graph.nodes:
                children = graph.nodes[current].children
                dependents.update(children)
                queue.extend(children)
        
        return list(dependents)
    
    def find_weak_prerequisite(
        self,
        graph: KnowledgeGraph,
        mastery_state: Dict[str, ConceptMastery],
        failed_concept_id: str,
        threshold: float = 0.40
    ) -> Optional[str]:
        """
        Find the root cause of failure by traversing up the prerequisite tree.
        
        This implements the "regression" logic: if a student fails a concept,
        check if any prerequisite is weak. If so, return that prerequisite.
        
        Args:
            graph: Knowledge graph
            mastery_state: Current user mastery state (concept_id -> ConceptMastery)
            failed_concept_id: Concept the student failed
            threshold: Mastery threshold (default 0.40, the "learning" threshold)
        
        Returns:
            concept_id of the weakest prerequisite, or None if all prerequisites are strong
        
        Algorithm:
            1. Get all direct prerequisites
            2. Find the one with lowest P(L)
            3. If P(L) < threshold, return it (needs work)
            4. Otherwise, recursively check that prerequisite's prerequisites
        """
        if failed_concept_id not in graph.nodes:
            return None
        
        prerequisites = self.get_prerequisites(graph, failed_concept_id, recursive=False)
        
        if not prerequisites:
            # No prerequisites - this is a root concept
            return None
        
        # Find weakest prerequisite
        weakest_concept = None
        weakest_mastery = float('inf')
        
        for prereq_id in prerequisites:
            if prereq_id not in mastery_state:
                # Not yet attempted - consider this weak
                return prereq_id
            
            P_L = mastery_state[prereq_id].P_L
            if P_L < weakest_mastery:
                weakest_mastery = P_L
                weakest_concept = prereq_id
        
        # If weakest is below threshold, recommend it
        if weakest_mastery < threshold:
            return weakest_concept
        
        # If all direct prerequisites are strong, recursively check their prerequisites
        if weakest_concept:
            deeper_weak = self.find_weak_prerequisite(
                graph, mastery_state, weakest_concept, threshold
            )
            if deeper_weak:
                return deeper_weak
        
        # All prerequisites are strong - problem is with the failed concept itself
        return None
    
    def get_next_unlockable_concepts(
        self,
        graph: KnowledgeGraph,
        mastered_concepts: Set[str],
        unlocked_concepts: Set[str]
    ) -> List[str]:
        """
        Determine which concepts can be unlocked based on mastered prerequisites.
        
        CASCADE UNLOCK LOGIC:
        When a concept is mastered, this checks ALL concepts in the graph to see
        if they can now be unlocked. A concept becomes unlockable when ALL of its
        parent concepts have been mastered.
        
        This creates a cascade effect: mastering one concept can unlock multiple
        child concepts if they have no other unmastered prerequisites.
        
        Args:
            graph: Knowledge graph
            mastered_concepts: Set of concept_ids that have been mastered
            unlocked_concepts: Set of concept_ids already unlocked
        
        Returns:
            List of concept_ids that can be newly unlocked (sorted by depth for BFS)
        """
        unlockable = []
        
        for concept_id, node in graph.nodes.items():
            # Skip if already unlocked or mastered
            if concept_id in unlocked_concepts or concept_id in mastered_concepts:
                continue
            
            # Check if all prerequisites are mastered
            if not node.parents:
                # Root node - can always be unlocked (shouldn't happen, roots auto-unlock on init)
                unlockable.append(concept_id)
            else:
                # Check if ALL parents are mastered (this is the cascade condition)
                all_prerequisites_mastered = all(
                    parent_id in mastered_concepts
                    for parent_id in node.parents
                )
                if all_prerequisites_mastered:
                    unlockable.append(concept_id)
        
        # Sort by depth to unlock concepts in breadth-first order
        unlockable.sort(key=lambda cid: graph.nodes[cid].depth)
        
        return unlockable
    
    def validate_graph_is_dag(self, nodes: Dict[str, ConceptNode]) -> Tuple[bool, Optional[str]]:
        """
        Validate that the graph is a Directed Acyclic Graph (no cycles).
        
        Returns:
            (is_valid, error_message)
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(concept_id: str) -> bool:
            if concept_id in rec_stack:
                return True  # Cycle detected
            
            if concept_id in visited:
                return False  # Already checked this path
            
            visited.add(concept_id)
            rec_stack.add(concept_id)
            
            # Check all children
            node = nodes.get(concept_id)
            if node:
                for child_id in node.children:
                    if child_id in nodes and has_cycle(child_id):
                        return True
            
            rec_stack.remove(concept_id)
            return False
        
        # Check for cycles starting from each node
        for concept_id in nodes.keys():
            if concept_id not in visited:
                if has_cycle(concept_id):
                    return False, f"Cycle detected involving concept '{concept_id}'"
        
        return True, None
