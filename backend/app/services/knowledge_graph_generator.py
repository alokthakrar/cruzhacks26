"""
Knowledge Graph Generator Service

Uses Gemini to auto-generate knowledge graphs based on subject names.
Supports both Google AI Studio (API key) and Vertex AI (service account).
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..config import get_settings
from ..database import get_knowledge_graphs_collection


class KnowledgeGraphGenerator:
    """Service for generating knowledge graphs using Gemini."""

    def __init__(self):
        self.gemini_model = None
        self.use_google_ai = False  # True = Google AI Studio, False = Vertex AI

    def load_model(self):
        """Configure Gemini model at startup. Tries Google AI Studio first, then Vertex AI."""
        settings = get_settings()

        # Try Google AI Studio first (simpler API key auth)
        if settings.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
                self.use_google_ai = True
                print("Knowledge Graph Generator: Using Google AI Studio (gemini-2.5-flash)")
                return
            except Exception as e:
                print(f"Knowledge Graph Generator: Failed to init Google AI Studio: {e}")

        # Fall back to Vertex AI (service account auth)
        if settings.gcp_project_id:
            try:
                from vertexai.generative_models import GenerativeModel
                # Vertex AI is already initialized by other services (ocr, pdf_extractor)
                self.gemini_model = GenerativeModel("gemini-2.5-flash")
                self.use_google_ai = False
                print("Knowledge Graph Generator: Using Vertex AI (gemini-2.5-flash)")
                return
            except Exception as e:
                print(f"Knowledge Graph Generator: Failed to init Vertex AI: {e}")

        print("Knowledge Graph Generator: No API configured, generation disabled")

    async def generate_graph(self, subject_name: str, subject_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a knowledge graph for a subject using Gemini.

        Args:
            subject_name: Name of the subject (e.g., "Calculus", "Physics")
            subject_id: MongoDB ID of the subject
            user_id: User who created the subject

        Returns:
            The created knowledge graph document, or None if generation failed
        """
        if not self.gemini_model:
            print(f"Skipping graph generation for '{subject_name}' - Gemini not configured")
            return None

        prompt = f'''You are an expert curriculum designer. Generate a knowledge graph for the subject: "{subject_name}"

Create a structured learning path with 6-10 concepts that cover the fundamentals of this subject.
Each concept should have clear prerequisites and build towards more advanced topics.

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "concepts": [
        {{
            "concept_id": "unique_snake_case_id",
            "name": "Display Name",
            "description": "Brief description of what this concept covers",
            "parents": ["parent_concept_id"],
            "depth": 0,
            "P_L0": 0.10,
            "P_T": 0.10,
            "P_G": 0.25,
            "P_S": 0.10
        }}
    ]
}}

Rules:
- concept_id should be snake_case and unique
- depth starts at 0 for root concepts (no parents) and increments for each level
- parents array contains concept_ids of prerequisites (empty for root concepts)
- P_L0: initial knowledge probability (0.05-0.15, lower for harder concepts)
- P_T: learning rate per question (0.05-0.15, lower for harder concepts)
- P_G: guess probability (0.10-0.30, lower for harder concepts)
- P_S: slip probability (0.08-0.20, higher for concepts where mistakes are common)
- Order concepts from foundational to advanced
- Ensure the graph is connected (no orphan concepts)
- Make concepts specific to {subject_name}, not generic math/learning concepts'''

        try:
            response = self.gemini_model.generate_content(prompt)
            
            # Check if response was blocked by safety filters
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"Knowledge graph generation blocked for '{subject_name}' (safety filters)")
                return None
            
            if not response.text:
                print(f"Knowledge graph generation failed for '{subject_name}' (empty response)")
                return None

            response_text = response.text.strip()

            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text)
            concepts = data.get("concepts", [])

            if not concepts:
                print(f"No concepts generated for '{subject_name}'")
                return None

            # Build nodes dict and compute children
            nodes = {}
            for concept in concepts:
                concept_id = concept["concept_id"]
                nodes[concept_id] = {
                    "concept_id": concept_id,
                    "name": concept["name"],
                    "description": concept.get("description", ""),
                    "parents": concept.get("parents", []),
                    "children": [],  # Will be filled in
                    "default_params": {
                        "P_L0": concept.get("P_L0", 0.10),
                        "P_T": concept.get("P_T", 0.10),
                        "P_G": concept.get("P_G", 0.25),
                        "P_S": concept.get("P_S", 0.10)
                    },
                    "depth": concept.get("depth", 0)
                }

            # Compute children from parents
            for concept_id, node in nodes.items():
                for parent_id in node["parents"]:
                    if parent_id in nodes:
                        nodes[parent_id]["children"].append(concept_id)

            # Find root concepts (no parents)
            root_concepts = [cid for cid, node in nodes.items() if not node["parents"]]

            # Create the graph document
            now = datetime.utcnow()
            graph_doc = {
                "_id": f"graph_{subject_id}",
                "subject_id": subject_id,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
                "nodes": nodes,
                "root_concepts": root_concepts
            }

            # Save to MongoDB
            collection = get_knowledge_graphs_collection()
            await collection.replace_one(
                {"_id": graph_doc["_id"]},
                graph_doc,
                upsert=True
            )

            # Log the generated concepts
            print(f"\n{'='*60}")
            print(f"Generated knowledge graph for '{subject_name}'")
            print(f"Subject ID: {subject_id}")
            print(f"Graph ID: {graph_doc['_id']}")
            print(f"Concepts ({len(nodes)}):")
            for concept_id, node in nodes.items():
                parents = node.get('parents', [])
                parent_str = f" (requires: {', '.join(parents)})" if parents else " (root)"
                print(f"  - {concept_id}: {node['name']}{parent_str}")
            print(f"Root concepts: {root_concepts}")
            print(f"{'='*60}\n")

            return graph_doc

        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response for '{subject_name}': {e}")
            return None
        except Exception as e:
            print(f"Error generating graph for '{subject_name}': {e}")
            return None

    async def get_graph_for_subject(self, subject_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a knowledge graph by subject ID."""
        collection = get_knowledge_graphs_collection()
        graph = await collection.find_one({"subject_id": subject_id})
        return graph

    async def get_concept_ids(self, subject_id: str) -> list:
        """Get list of all concept IDs for a subject."""
        graph = await self.get_graph_for_subject(subject_id)
        if graph and "nodes" in graph:
            return list(graph["nodes"].keys())
        return []

    async def tag_question_concept(
        self,
        question_text: str,
        subject_id: str,
        latex_content: Optional[str] = None
    ) -> Optional[str]:
        """
        Tag a question with the most appropriate concept from the subject's knowledge graph.

        Args:
            question_text: The question text content
            subject_id: The subject ID to get the knowledge graph from
            latex_content: Optional LaTeX content for math expressions

        Returns:
            The concept_id that best matches the question, or None if tagging failed
        """
        if not self.gemini_model:
            return None

        # Get the knowledge graph for this subject
        graph = await self.get_graph_for_subject(subject_id)
        if not graph or "nodes" not in graph:
            print(f"No knowledge graph found for subject {subject_id}")
            return None

        # Build concept list for the prompt
        concepts_desc = []
        for concept_id, node in graph["nodes"].items():
            concepts_desc.append(f"- {concept_id}: {node['name']} - {node.get('description', '')}")

        concepts_list = "\n".join(concepts_desc)

        question_content = question_text
        if latex_content:
            question_content += f"\n\nMathematical content: {latex_content}"

        prompt = f'''You are a curriculum expert. Classify the following question into ONE of the available concepts.

Question:
{question_content}

Available concepts:
{concepts_list}

Return ONLY the concept_id (no explanation, no quotes, just the snake_case id).
If the question doesn't fit any concept well, return the most foundational/general concept that applies.'''

        try:
            response = self.gemini_model.generate_content(prompt)
            
            # Check if response was blocked by safety filters
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"Question tagging blocked by safety filters, using fallback")
                if graph.get("root_concepts"):
                    return graph["root_concepts"][0]
                return None
            
            concept_id = response.text.strip().lower().replace('"', '').replace("'", "")

            # Validate that the concept exists
            if concept_id in graph["nodes"]:
                return concept_id
            else:
                # Return first root concept as fallback
                if graph.get("root_concepts"):
                    return graph["root_concepts"][0]
                return None

        except Exception as e:
            print(f"Error tagging question concept: {e}")
            return None

    async def tag_questions_batch(
        self,
        questions: list,
        subject_id: str
    ) -> list:
        """
        Tag multiple questions with concepts in a single batch call.

        Args:
            questions: List of dicts with 'text_content' and optional 'latex_content'
            subject_id: The subject ID

        Returns:
            List of concept_ids in the same order as input questions
        """
        if not self.gemini_model or not questions:
            return [None] * len(questions)

        graph = await self.get_graph_for_subject(subject_id)
        if not graph or "nodes" not in graph:
            return [None] * len(questions)

        # Build concept list
        concepts_desc = []
        for concept_id, node in graph["nodes"].items():
            concepts_desc.append(f"- {concept_id}: {node['name']} - {node.get('description', '')}")
        concepts_list = "\n".join(concepts_desc)

        # Build questions list
        questions_list = []
        for i, q in enumerate(questions):
            q_text = q.get("text_content", "")
            if q.get("latex_content"):
                q_text += f" [{q['latex_content']}]"
            questions_list.append(f"{i+1}. {q_text}")

        questions_text = "\n".join(questions_list)

        prompt = f'''You are a curriculum expert. Classify each of the following questions into ONE of the available concepts.

Questions:
{questions_text}

Available concepts:
{concepts_list}

Return ONLY a JSON array of concept_ids in order, like: ["concept_1", "concept_2", ...]
No explanation, just the JSON array.'''

        try:
            response = self.gemini_model.generate_content(prompt)
            
            # Check if response was blocked by safety filters
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"Batch tagging blocked by safety filters. Falling back to individual tagging.")
                # Fall back to tagging each question individually
                result = []
                for q in questions:
                    concept_id = await self.tag_question_concept(
                        q.get("text_content", ""),
                        subject_id,
                        q.get("latex_content")
                    )
                    result.append(concept_id)
                return result
            
            response_text = response.text.strip()

            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            concept_ids = json.loads(response_text)

            # Validate and return
            valid_concepts = set(graph["nodes"].keys())
            fallback = graph["root_concepts"][0] if graph.get("root_concepts") else None

            result = []
            for cid in concept_ids:
                if cid in valid_concepts:
                    result.append(cid)
                else:
                    result.append(fallback)

            # Pad if needed
            while len(result) < len(questions):
                result.append(fallback)

            return result[:len(questions)]

        except Exception as e:
            print(f"Error batch tagging questions: {e}")
            return [None] * len(questions)


# Singleton instance
knowledge_graph_generator = KnowledgeGraphGenerator()
