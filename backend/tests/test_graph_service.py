"""
Unit tests for Graph Service

Tests DAG operations, traversal, prerequisite detection, and unlocking logic.
"""

import pytest
from app.services.graph_service import GraphService
from app.models.knowledge_graph import ConceptNode, BKTParams
from app.models.user_mastery import ConceptMastery


class TestDepthCalculation:
    """Test depth calculation for topological ordering."""
    
    def test_simple_linear_chain(self):
        """Test depth calculation for A -> B -> C."""
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["C"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["B"], children=[]),
        }
        
        service = GraphService(None)
        nodes_with_depth = service._calculate_depths(nodes)
        
        assert nodes_with_depth["A"].depth == 0
        assert nodes_with_depth["B"].depth == 1
        assert nodes_with_depth["C"].depth == 2
    
    def test_multiple_roots(self):
        """Test depth calculation with multiple root nodes."""
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["C"]),
            "B": ConceptNode(concept_id="B", name="B", parents=[], children=["C"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["A", "B"], children=[]),
        }
        
        service = GraphService(None)
        nodes_with_depth = service._calculate_depths(nodes)
        
        assert nodes_with_depth["A"].depth == 0
        assert nodes_with_depth["B"].depth == 0
        assert nodes_with_depth["C"].depth == 1  # max(depth(A), depth(B)) + 1
    
    def test_diamond_structure(self):
        """Test depth calculation for diamond: A -> B,C -> D."""
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B", "C"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["D"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["A"], children=["D"]),
            "D": ConceptNode(concept_id="D", name="D", parents=["B", "C"], children=[]),
        }
        
        service = GraphService(None)
        nodes_with_depth = service._calculate_depths(nodes)
        
        assert nodes_with_depth["A"].depth == 0
        assert nodes_with_depth["B"].depth == 1
        assert nodes_with_depth["C"].depth == 1
        assert nodes_with_depth["D"].depth == 2
    
    def test_complex_hierarchy(self):
        """Test depth calculation for complex calculus hierarchy."""
        nodes = {
            "limits": ConceptNode(concept_id="limits", name="Limits", parents=[], children=["derivatives", "continuity"]),
            "derivatives": ConceptNode(concept_id="derivatives", name="Derivatives", parents=["limits"], children=["chain_rule", "product_rule"]),
            "continuity": ConceptNode(concept_id="continuity", name="Continuity", parents=["limits"], children=[]),
            "chain_rule": ConceptNode(concept_id="chain_rule", name="Chain Rule", parents=["derivatives"], children=["related_rates"]),
            "product_rule": ConceptNode(concept_id="product_rule", name="Product Rule", parents=["derivatives"], children=[]),
            "related_rates": ConceptNode(concept_id="related_rates", name="Related Rates", parents=["chain_rule"], children=[]),
        }
        
        service = GraphService(None)
        nodes_with_depth = service._calculate_depths(nodes)
        
        assert nodes_with_depth["limits"].depth == 0
        assert nodes_with_depth["derivatives"].depth == 1
        assert nodes_with_depth["continuity"].depth == 1
        assert nodes_with_depth["chain_rule"].depth == 2
        assert nodes_with_depth["product_rule"].depth == 2
        assert nodes_with_depth["related_rates"].depth == 3


class TestGetPrerequisites:
    """Test prerequisite retrieval."""
    
    @pytest.fixture
    def sample_graph(self):
        """Create a sample knowledge graph."""
        from app.models.knowledge_graph import KnowledgeGraph
        from bson import ObjectId
        from datetime import datetime
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["C"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["B"], children=["D"]),
            "D": ConceptNode(concept_id="D", name="D", parents=["C"], children=[]),
        }
        
        return KnowledgeGraph(
            _id=str(ObjectId()),
            subject_id="test_subject",
            created_by="user1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            nodes=nodes,
            root_concepts=["A"]
        )
    
    def test_direct_prerequisites(self, sample_graph):
        """Test getting direct prerequisites only."""
        service = GraphService(None)
        
        prereqs = service.get_prerequisites(sample_graph, "C", recursive=False)
        assert prereqs == ["B"]
        
        prereqs = service.get_prerequisites(sample_graph, "A", recursive=False)
        assert prereqs == []  # Root node has no prerequisites
    
    def test_recursive_prerequisites(self, sample_graph):
        """Test getting all ancestors recursively."""
        service = GraphService(None)
        
        prereqs = service.get_prerequisites(sample_graph, "D", recursive=True)
        assert set(prereqs) == {"A", "B", "C"}
        
        prereqs = service.get_prerequisites(sample_graph, "C", recursive=True)
        assert set(prereqs) == {"A", "B"}
    
    def test_nonexistent_concept(self, sample_graph):
        """Test getting prerequisites for non-existent concept."""
        service = GraphService(None)
        
        prereqs = service.get_prerequisites(sample_graph, "Z", recursive=False)
        assert prereqs == []


class TestGetDependents:
    """Test dependent (children) retrieval."""
    
    @pytest.fixture
    def sample_graph(self):
        from app.models.knowledge_graph import KnowledgeGraph
        from bson import ObjectId
        from datetime import datetime
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B", "C"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["D"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["A"], children=["D"]),
            "D": ConceptNode(concept_id="D", name="D", parents=["B", "C"], children=[]),
        }
        
        return KnowledgeGraph(
            _id=str(ObjectId()),
            subject_id="test_subject",
            created_by="user1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            nodes=nodes,
            root_concepts=["A"]
        )
    
    def test_direct_dependents(self, sample_graph):
        """Test getting direct children only."""
        service = GraphService(None)
        
        deps = service.get_dependents(sample_graph, "A", recursive=False)
        assert set(deps) == {"B", "C"}
        
        deps = service.get_dependents(sample_graph, "D", recursive=False)
        assert deps == []  # Leaf node has no dependents
    
    def test_recursive_dependents(self, sample_graph):
        """Test getting all descendants recursively."""
        service = GraphService(None)
        
        deps = service.get_dependents(sample_graph, "A", recursive=True)
        assert set(deps) == {"B", "C", "D"}


class TestFindWeakPrerequisite:
    """Test regression logic for finding weak prerequisites."""
    
    @pytest.fixture
    def calculus_graph(self):
        from app.models.knowledge_graph import KnowledgeGraph
        from bson import ObjectId
        from datetime import datetime
        
        nodes = {
            "limits": ConceptNode(concept_id="limits", name="Limits", parents=[], children=["derivatives"]),
            "derivatives": ConceptNode(concept_id="derivatives", name="Derivatives", parents=["limits"], children=["chain_rule"]),
            "chain_rule": ConceptNode(concept_id="chain_rule", name="Chain Rule", parents=["derivatives"], children=["related_rates"]),
            "related_rates": ConceptNode(concept_id="related_rates", name="Related Rates", parents=["chain_rule"], children=[]),
        }
        
        return KnowledgeGraph(
            _id=str(ObjectId()),
            subject_id="calculus",
            created_by="user1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            nodes=nodes,
            root_concepts=["limits"]
        )
    
    def test_weak_direct_prerequisite(self, calculus_graph):
        """Test finding a weak direct prerequisite."""
        service = GraphService(None)
        
        mastery_state = {
            "limits": ConceptMastery(P_L=0.90),  # Strong
            "derivatives": ConceptMastery(P_L=0.30),  # Weak
            "chain_rule": ConceptMastery(P_L=0.20),  # Very weak
        }
        
        # Failed chain_rule, should regress to derivatives (weak)
        weak = service.find_weak_prerequisite(
            calculus_graph, mastery_state, "chain_rule", threshold=0.40
        )
        assert weak == "derivatives"
    
    def test_deep_regression(self, calculus_graph):
        """Test regression that goes multiple levels deep."""
        service = GraphService(None)
        
        mastery_state = {
            "limits": ConceptMastery(P_L=0.25),  # Very weak (root cause!)
            "derivatives": ConceptMastery(P_L=0.35),  # Weak
            "chain_rule": ConceptMastery(P_L=0.20),  # Very weak
        }
        
        # Failed chain_rule, should regress all the way to limits
        weak = service.find_weak_prerequisite(
            calculus_graph, mastery_state, "chain_rule", threshold=0.40
        )
        # Should find derivatives first (direct prerequisite)
        assert weak == "derivatives"
    
    def test_all_prerequisites_strong(self, calculus_graph):
        """Test when all prerequisites are strong (no regression needed)."""
        service = GraphService(None)
        
        mastery_state = {
            "limits": ConceptMastery(P_L=0.90),
            "derivatives": ConceptMastery(P_L=0.85),
            "chain_rule": ConceptMastery(P_L=0.30),  # Weak but prerequisites are strong
        }
        
        # Failed chain_rule but prerequisites are strong - no regression
        weak = service.find_weak_prerequisite(
            calculus_graph, mastery_state, "chain_rule", threshold=0.40
        )
        assert weak is None  # No weak prerequisites
    
    def test_missing_mastery_data(self, calculus_graph):
        """Test when prerequisite has no mastery data (never attempted)."""
        service = GraphService(None)
        
        mastery_state = {
            "chain_rule": ConceptMastery(P_L=0.20),
            # derivatives and limits not in mastery state
        }
        
        # Should detect that prerequisites haven't been attempted
        weak = service.find_weak_prerequisite(
            calculus_graph, mastery_state, "chain_rule", threshold=0.40
        )
        assert weak == "derivatives"  # Should recommend the missing prerequisite
    
    def test_root_concept_failure(self, calculus_graph):
        """Test failing a root concept (no prerequisites to regress to)."""
        service = GraphService(None)
        
        mastery_state = {
            "limits": ConceptMastery(P_L=0.20),
        }
        
        # Failed limits (root) - no prerequisites to regress to
        weak = service.find_weak_prerequisite(
            calculus_graph, mastery_state, "limits", threshold=0.40
        )
        assert weak is None


class TestGetNextUnlockableConcepts:
    """Test concept unlocking logic."""
    
    @pytest.fixture
    def unlock_graph(self):
        from app.models.knowledge_graph import KnowledgeGraph
        from bson import ObjectId
        from datetime import datetime
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B", "C"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["D"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["A"], children=["D"]),
            "D": ConceptNode(concept_id="D", name="D", parents=["B", "C"], children=[]),
        }
        
        return KnowledgeGraph(
            _id=str(ObjectId()),
            subject_id="test",
            created_by="user1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            nodes=nodes,
            root_concepts=["A"]
        )
    
    def test_initial_unlock_root_only(self, unlock_graph):
        """Test that initially only root concepts can be unlocked."""
        service = GraphService(None)
        
        unlockable = service.get_next_unlockable_concepts(
            unlock_graph,
            mastered_concepts=set(),
            unlocked_concepts=set()
        )
        assert unlockable == ["A"]  # Only root
    
    def test_unlock_after_mastering_root(self, unlock_graph):
        """Test unlocking children after mastering root."""
        service = GraphService(None)
        
        unlockable = service.get_next_unlockable_concepts(
            unlock_graph,
            mastered_concepts={"A"},
            unlocked_concepts={"A"}
        )
        assert set(unlockable) == {"B", "C"}
    
    def test_unlock_requires_all_prerequisites(self, unlock_graph):
        """Test that D requires BOTH B and C to be mastered."""
        service = GraphService(None)
        
        # Only B mastered - D should not unlock
        unlockable = service.get_next_unlockable_concepts(
            unlock_graph,
            mastered_concepts={"A", "B"},
            unlocked_concepts={"A", "B", "C"}
        )
        assert "D" not in unlockable
        
        # Both B and C mastered - D should unlock
        unlockable = service.get_next_unlockable_concepts(
            unlock_graph,
            mastered_concepts={"A", "B", "C"},
            unlocked_concepts={"A", "B", "C"}
        )
        assert "D" in unlockable
    
    def test_no_duplicates(self, unlock_graph):
        """Test that already unlocked concepts are not returned."""
        service = GraphService(None)
        
        unlockable = service.get_next_unlockable_concepts(
            unlock_graph,
            mastered_concepts={"A"},
            unlocked_concepts={"A", "B"}  # B already unlocked
        )
        assert "A" not in unlockable  # Already unlocked
        assert "B" not in unlockable  # Already unlocked
        assert "C" in unlockable  # Can be unlocked


class TestDAGValidation:
    """Test cycle detection."""
    
    def test_valid_dag(self):
        """Test that a valid DAG passes validation."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["C"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["B"], children=[]),
        }
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is True
        assert error is None
    
    def test_self_loop(self):
        """Test detection of self-loop (A -> A)."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["A"]),  # Self-loop
        }
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is False
        assert "cycle" in error.lower()
    
    def test_simple_cycle(self):
        """Test detection of simple cycle (A -> B -> A)."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=["B"], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["A"]),
        }
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is False
        assert "cycle" in error.lower()
    
    def test_complex_cycle(self):
        """Test detection of cycle in larger graph (A -> B -> C -> A)."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=["C"], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=["C"]),
            "C": ConceptNode(concept_id="C", name="C", parents=["B"], children=["A"]),
        }
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is False
        assert "cycle" in error.lower()
    
    def test_disconnected_valid_graph(self):
        """Test that disconnected components are valid if no cycles."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=["B"]),
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=[]),
            "C": ConceptNode(concept_id="C", name="C", parents=[], children=["D"]),
            "D": ConceptNode(concept_id="D", name="D", parents=["C"], children=[]),
        }
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is True
        assert error is None


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_graph(self):
        """Test operations on empty graph."""
        service = GraphService(None)
        
        nodes = {}
        nodes_with_depth = service._calculate_depths(nodes)
        assert nodes_with_depth == {}
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is True
    
    def test_single_node_graph(self):
        """Test operations on single-node graph."""
        service = GraphService(None)
        
        nodes = {
            "A": ConceptNode(concept_id="A", name="A", parents=[], children=[]),
        }
        
        nodes_with_depth = service._calculate_depths(nodes)
        assert nodes_with_depth["A"].depth == 0
        
        is_valid, error = service.validate_graph_is_dag(nodes)
        assert is_valid is True
    
    def test_missing_parent_reference(self):
        """Test when node references a parent that doesn't exist."""
        service = GraphService(None)
        
        nodes = {
            "B": ConceptNode(concept_id="B", name="B", parents=["A"], children=[]),
            # "A" is missing
        }
        
        # Should handle gracefully
        nodes_with_depth = service._calculate_depths(nodes)
        assert "B" in nodes_with_depth
        # B's depth should be calculated despite missing parent
        assert nodes_with_depth["B"].depth >= 0
