"""
SurvivalRAG - Retrieval Augmented Generation for Survival Knowledge
Reduces hallucinations by grounding AI responses in real survival manuals
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pickle

logger = logging.getLogger(__name__)


class SurvivalRAG:
    """
    Survival Knowledge Retrieval System

    Features:
    - 70+ survival and first-aid manuals
    - Fast local search (no internet needed)
    - Reduces AI hallucinations
    - Ultra-low latency mode
    - Works over mesh networks (Meshtastic compatible)
    """

    def __init__(self, manuals_dir: str = "survival_manuals"):
        self.manuals_dir = Path(manuals_dir)
        self.index = None
        self.documents = []
        self.manual_metadata = {}

    async def initialize(self):
        """Load survival manuals and build search index"""
        logger.info("Initializing SurvivalRAG system...")

        try:
            # Load pre-built index if available
            index_path = self.manuals_dir / "survival_index.pkl"
            if index_path.exists():
                logger.info("Loading pre-built survival knowledge index...")
                with open(index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.manual_metadata = data['metadata']
                    self.index = data.get('index')
                logger.info(f"Loaded {len(self.documents)} survival knowledge chunks")
            else:
                logger.info("Building survival knowledge index from manuals...")
                await self._build_index_from_manuals()

        except Exception as e:
            logger.warning(f"Could not load SurvivalRAG index: {e}")
            logger.warning("Running without survival knowledge augmentation")

    async def _build_index_from_manuals(self):
        """Build search index from survival manual files"""
        if not self.manuals_dir.exists():
            logger.warning(f"Manuals directory not found: {self.manuals_dir}")
            return

        # Load all manual chunks
        manual_files = list(self.manuals_dir.glob("*.json"))

        for manual_file in manual_files:
            try:
                with open(manual_file, 'r') as f:
                    manual_data = json.load(f)

                manual_name = manual_data.get('name', manual_file.stem)
                chunks = manual_data.get('chunks', [])

                self.manual_metadata[manual_name] = {
                    'file': str(manual_file),
                    'description': manual_data.get('description', ''),
                    'categories': manual_data.get('categories', []),
                    'chunk_count': len(chunks)
                }

                self.documents.extend(chunks)

                logger.info(f"Loaded {len(chunks)} chunks from {manual_name}")

            except Exception as e:
                logger.error(f"Error loading manual {manual_file}: {e}")

        logger.info(f"Total survival knowledge chunks: {len(self.documents)}")

        # Save index
        self._save_index()

    def _save_index(self):
        """Save built index for faster loading"""
        index_path = self.manuals_dir / "survival_index.pkl"
        try:
            with open(index_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.manual_metadata,
                    'index': self.index
                }, f)
            logger.info(f"Saved survival knowledge index to {index_path}")
        except Exception as e:
            logger.error(f"Could not save index: {e}")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search survival manuals for relevant information

        Args:
            query: User's question or topic
            top_k: Number of top results to return

        Returns:
            List of relevant manual chunks with metadata
        """
        if not self.documents:
            return []

        # Simple keyword-based search (fast, no ML needed)
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_docs = []
        for doc in self.documents:
            content = doc.get('content', '').lower()
            title = doc.get('title', '').lower()

            # Calculate relevance score
            score = 0

            # Exact phrase match
            if query_lower in content or query_lower in title:
                score += 10

            # Word matches in content
            content_words = set(content.split())
            common_words = query_words & content_words
            score += len(common_words)

            # Title matches are worth more
            title_words = set(title.split())
            title_matches = query_words & title_words
            score += len(title_matches) * 3

            if score > 0:
                scored_docs.append({
                    'content': doc.get('content', ''),
                    'title': doc.get('title', ''),
                    'manual': doc.get('manual', 'Unknown'),
                    'page': doc.get('page'),
                    'score': score
                })

        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:top_k]

    def augment_prompt(
        self,
        user_query: str,
        system_prompt: str,
        ultra_low_latency: bool = False
    ) -> str:
        """
        Augment the system prompt with relevant survival knowledge

        Args:
            user_query: User's question
            system_prompt: Original system prompt
            ultra_low_latency: If True, request 1-2 sentence answers

        Returns:
            Enhanced system prompt with survival knowledge context
        """
        # Search for relevant manual content
        relevant_docs = self.search(user_query, top_k=3)

        if not relevant_docs:
            # No relevant survival knowledge found
            if ultra_low_latency:
                return system_prompt + "\n\nIMPORTANT: Give a concise 1-2 sentence answer. Be brief and direct."
            return system_prompt

        # Build RAG context
        rag_context = "\n\n=== SURVIVAL KNOWLEDGE REFERENCE ===\n"
        rag_context += "The following information is from verified survival and first-aid manuals:\n\n"

        for i, doc in enumerate(relevant_docs, 1):
            rag_context += f"{i}. From '{doc['manual']}':\n"
            rag_context += f"   {doc['content']}\n"
            if doc.get('page'):
                rag_context += f"   (Source: Page {doc['page']})\n"
            rag_context += "\n"

        rag_context += "=== END REFERENCE ===\n\n"

        # Add instructions
        instructions = (
            "Use the above survival manual excerpts to answer the question accurately. "
            "If the manuals provide relevant information, cite them. "
            "If the manuals don't cover the topic, say so and provide general knowledge. "
            "Never make up medical or survival advice - lives depend on accuracy."
        )

        if ultra_low_latency:
            instructions += "\n\nIMPORTANT: Give a concise 1-2 sentence answer. Emergency situation - be brief and direct."

        # Combine everything
        enhanced_prompt = system_prompt + "\n\n" + rag_context + instructions

        return enhanced_prompt

    def get_manual_list(self) -> List[str]:
        """Get list of available survival manuals"""
        return list(self.manual_metadata.keys())

    def get_categories(self) -> List[str]:
        """Get list of survival topic categories"""
        categories = set()
        for manual in self.manual_metadata.values():
            categories.update(manual.get('categories', []))
        return sorted(list(categories))

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        return {
            'total_manuals': len(self.manual_metadata),
            'total_chunks': len(self.documents),
            'categories': self.get_categories(),
            'manuals': self.get_manual_list()
        }
