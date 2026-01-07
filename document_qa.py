"""
Document Q&A System with RAG

This script allows you to load a specific JSON file and PDF, then ask questions
about the content. It uses RAG (Retrieval-Augmented Generation) to find relevant
content from the document.

Usage:
    python document_qa.py --json path/to/file.json --pdf path/to/file.pdf
    
Or use interactively within the script.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
import argparse


class DocumentQA:
    """Question-Answering system for a single document using RAG"""
    
    def __init__(self, json_path: str, pdf_path: str = None):
        """
        Initialize the Document Q&A system
        
        Args:
            json_path: Path to the JSON file containing structured content
            pdf_path: Optional path to the PDF file (for reference)
        """
        self.json_path = Path(json_path)
        self.pdf_path = Path(pdf_path) if pdf_path else None
        
        # Validate files
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        if self.pdf_path and not self.pdf_path.exists():
            print(f"⚠️  Warning: PDF file not found: {pdf_path}")
            self.pdf_path = None
        
        # Load data
        print(f"📄 Loading document: {self.json_path.name}")
        self.data = self._load_json()
        self.unit_name = self.json_path.stem
        
        # Initialize embedding model
        print("🔧 Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Create in-memory vector database
        print("🗄️  Creating vector database...")
        self.documents = self._create_documents()
        self.collection = self._create_vector_db()
        
        print(f"✅ Loaded {len(self.documents)} content chunks from {self.unit_name}")
        print(f"📚 Topics: {self._get_topic_names()}\n")
    
    def _load_json(self) -> List[Dict]:
        """Load and parse the JSON file"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single topic and array of topics
        if isinstance(data, dict):
            return [data]
        return data
    
    def _get_topic_names(self) -> str:
        """Get comma-separated list of topic names"""
        topics = set()
        for topic in self.data:
            topic_name = topic.get("topic_name", "Unknown")
            topics.add(topic_name)
        return ", ".join(sorted(topics))
    
    def _create_documents(self) -> List[Dict]:
        """Convert JSON data to RAG documents"""
        documents = []
        doc_id = 0
        
        for topic in self.data:
            topic_id = topic.get("topic_id", "")
            topic_name = topic.get("topic_name", "")
            unit = topic.get("unit", self.unit_name)
            
            # Base metadata
            base_metadata = {
                "unit": unit,
                "topic_id": topic_id,
                "topic_name": topic_name,
                "source_file": self.json_path.name
            }
            
            # 1. Topic overview
            documents.append({
                "id": str(doc_id),
                "text": f"Topic: {topic_name}",
                "metadata": {**base_metadata, "doc_type": "topic_overview"}
            })
            doc_id += 1
            
            # 2. Learning objectives
            for lo in topic.get("learning_objectives", []):
                documents.append({
                    "id": str(doc_id),
                    "text": f"Learning Objective: {lo}",
                    "metadata": {**base_metadata, "doc_type": "learning_objective"}
                })
                doc_id += 1
            
            # 3. Allowed concepts
            allowed = topic.get("allowed_concepts", [])
            if allowed:
                documents.append({
                    "id": str(doc_id),
                    "text": f"Allowed concepts for {topic_name}: {', '.join(allowed)}",
                    "metadata": {**base_metadata, "doc_type": "allowed_concepts"}
                })
                doc_id += 1
            
            # 4. Disallowed concepts
            disallowed = topic.get("disallowed_concepts", [])
            if disallowed:
                documents.append({
                    "id": str(doc_id),
                    "text": f"Disallowed concepts (too advanced): {', '.join(disallowed)}",
                    "metadata": {**base_metadata, "doc_type": "disallowed_concepts"}
                })
                doc_id += 1
            
            # 5. Content blocks
            for block in topic.get("content_blocks", []):
                block_text = block.get("text", "")
                if block_text.strip():
                    documents.append({
                        "id": str(doc_id),
                        "text": block_text,
                        "metadata": {
                            **base_metadata,
                            "doc_type": f"content_{block.get('type', 'unknown')}",
                            "block_id": block.get("block_id", "")
                        }
                    })
                    doc_id += 1
        
        return documents
    
    def _create_vector_db(self):
        """Create in-memory ChromaDB collection"""
        # Use ephemeral client (in-memory, no persistence)
        client = chromadb.EphemeralClient()
        
        # Create collection with unique name using timestamp
        import time
        collection_name = f"doc_{int(time.time() * 1000)}"
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": f"Document Q&A for {self.unit_name}"}
        )
        
        # Create embeddings
        texts = [doc["text"] for doc in self.documents]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        
        # Add to collection
        ids = [doc["id"] for doc in self.documents]
        metadatas = [doc["metadata"] for doc in self.documents]
        
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )
        
        return collection
    
    def ask(self, question: str, n_results: int = 10, topic_filter: str = None) -> Dict:
        """
        Ask a question about the document
        
        Args:
            question: The question to ask
            n_results: Number of relevant chunks to retrieve
            topic_filter: Optional topic name to filter results
            
        Returns:
            Dictionary with retrieved content organized by type
        """
        # Create query embedding
        query_embedding = self.model.encode(question)
        
        # Build filter
        where_filter = {}
        if topic_filter:
            where_filter["topic_name"] = topic_filter
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results * 2 if topic_filter else n_results,
            where=where_filter if where_filter else None
        )
        
        # Organize results
        organized = {
            "question": question,
            "topic_overview": [],
            "learning_objectives": [],
            "allowed_concepts": [],
            "disallowed_concepts": [],
            "content_blocks": [],
            "all_results": []  # For LLM context
        }
        
        if results["documents"] and len(results["documents"]) > 0:
            count = 0
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Apply topic filter if specified
                if topic_filter and meta.get("topic_name", "").lower() != topic_filter.lower():
                    continue
                
                if count >= n_results:
                    break
                count += 1
                
                doc_type = meta.get("doc_type", "")
                
                result_item = {
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                    "distance": distance
                }
                
                # Categorize
                if doc_type == "topic_overview":
                    organized["topic_overview"].append(result_item)
                elif doc_type == "learning_objective":
                    organized["learning_objectives"].append(result_item)
                elif doc_type == "allowed_concepts":
                    organized["allowed_concepts"].append(result_item)
                elif doc_type == "disallowed_concepts":
                    organized["disallowed_concepts"].append(result_item)
                else:
                    organized["content_blocks"].append(result_item)
                
                # Add to all results for LLM context
                organized["all_results"].append(result_item)
        
        return organized
    
    def format_for_llm(self, results: Dict) -> str:
        """
        Format retrieved results as context for an LLM
        
        Args:
            results: Results from ask() method
            
        Returns:
            Formatted string ready for LLM prompt
        """
        context_parts = []
        
        # Header with clear explanation of what this data represents
        pdf_name = self.pdf_path.name if self.pdf_path else f"{self.unit_name}.pdf"
        
        context_parts.append("=" * 70)
        context_parts.append("CONTEXT FROM NCERT TEXTBOOK")
        context_parts.append("=" * 70)
        context_parts.append(f"\nSOURCE DOCUMENT: {pdf_name}")
        context_parts.append(f"UNIT/CHAPTER: {self.unit_name}")
        context_parts.append(f"\nNOTE: The following content has been extracted and structured from the")
        context_parts.append(f"      PDF textbook. It includes topics, learning objectives, concepts,")
        context_parts.append(f"      and actual content (definitions, explanations, examples) from the book.")
        context_parts.append("\n" + "=" * 70)
        context_parts.append(f"\nSTUDENT QUESTION: {results['question']}")
        context_parts.append("=" * 70)
        
        # Topic overview
        if results["topic_overview"]:
            context_parts.append("\n📚 TOPIC(S) FROM THE TEXTBOOK:")
            context_parts.append("-" * 70)
            for item in results["topic_overview"]:
                topic_name = item['text'].replace("Topic: ", "")
                context_parts.append(f"• {topic_name}")
        
        # Learning objectives
        if results["learning_objectives"]:
            context_parts.append("\n🎯 LEARNING OBJECTIVES (What students should learn):")
            context_parts.append("-" * 70)
            for item in results["learning_objectives"]:
                lo_text = item['text'].replace("Learning Objective: ", "")
                context_parts.append(f"• {lo_text}")
        
        # Allowed concepts
        if results["allowed_concepts"]:
            context_parts.append("\n✅ CONCEPTS COVERED IN THIS CHAPTER (Age-appropriate):")
            context_parts.append("-" * 70)
            for item in results["allowed_concepts"]:
                concepts_text = item['text']
                # Extract just the concepts part
                if "Allowed concepts for" in concepts_text:
                    concepts_text = concepts_text.split(": ", 1)[1] if ": " in concepts_text else concepts_text
                context_parts.append(f"• {concepts_text}")
        
        # Disallowed concepts
        if results["disallowed_concepts"]:
            context_parts.append("\n❌ ADVANCED CONCEPTS (NOT to be taught at this level):")
            context_parts.append("-" * 70)
            for item in results["disallowed_concepts"]:
                concepts_text = item['text']
                # Extract just the concepts part
                if "Disallowed concepts" in concepts_text:
                    concepts_text = concepts_text.split(": ", 1)[1] if ": " in concepts_text else concepts_text
                context_parts.append(f"• {concepts_text}")
        
        # Content blocks - the actual textbook content
        if results["content_blocks"]:
            context_parts.append("\n📖 RELEVANT CONTENT FROM THE TEXTBOOK:")
            context_parts.append("-" * 70)
            context_parts.append("(This is the actual text extracted from the PDF)")
            context_parts.append("")
            
            for i, item in enumerate(results["content_blocks"], 1):
                doc_type = item["metadata"]["doc_type"].replace("content_", "")
                topic_name = item["metadata"].get("topic_name", "Unknown")
                relevance = item['relevance_score']
                
                # Format based on content type
                if doc_type == "definition":
                    context_parts.append(f"\n[DEFINITION #{i}] from topic '{topic_name}' (Relevance: {relevance:.1%})")
                elif doc_type == "explanation":
                    context_parts.append(f"\n[EXPLANATION #{i}] from topic '{topic_name}' (Relevance: {relevance:.1%})")
                elif doc_type == "example":
                    context_parts.append(f"\n[EXAMPLE #{i}] from topic '{topic_name}' (Relevance: {relevance:.1%})")
                else:
                    context_parts.append(f"\n[CONTENT #{i}] from topic '{topic_name}' (Relevance: {relevance:.1%})")
                
                context_parts.append(f"{item['text']}")
        
        context_parts.append("\n" + "=" * 70)
        context_parts.append("END OF TEXTBOOK CONTEXT")
        context_parts.append("=" * 70)
        
        return "\n".join(context_parts)
    
    def interactive_qa(self):
        """Interactive Q&A session"""
        print("=" * 60)
        print("📖 DOCUMENT Q&A - INTERACTIVE MODE")
        print("=" * 60)
        print(f"Document: {self.json_path.name}")
        print(f"Topics: {self._get_topic_names()}")
        print("\nType 'quit' or 'exit' to stop")
        print("Type 'topics' to see all topics")
        print("=" * 60)
        
        while True:
            print("\n" + "-" * 60)
            question = input("❓ Your Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == 'topics':
                print(f"\n📚 Available Topics:")
                for i, topic in enumerate(self.data, 1):
                    print(f"  {i}. {topic.get('topic_name', 'Unknown')}")
                continue
            
            if not question:
                print("⚠️  Please enter a question")
                continue
            
            # Optional topic filter
            topic_filter = input("🎯 Filter by topic (optional, press Enter to skip): ").strip() or None
            
            # Get number of results
            n_input = input("📊 Number of results (default 10): ").strip()
            n_results = int(n_input) if n_input.isdigit() else 10
            
            # Ask question
            print("\n🔍 Searching...")
            results = self.ask(question, n_results=n_results, topic_filter=topic_filter)
            
            # Display results
            self._display_results(results)
            
            # Show LLM context
            show_llm = input("\n💡 Show LLM-ready context? (y/n): ").strip().lower()
            if show_llm in ['y', 'yes']:
                print("\n" + "=" * 60)
                print("LLM CONTEXT")
                print("=" * 60)
                print(self.format_for_llm(results))
    
    def _display_results(self, results: Dict):
        """Display results in a formatted way"""
        print("\n" + "=" * 60)
        print("📋 RESULTS")
        print("=" * 60)
        
        total = len(results["all_results"])
        print(f"\nFound {total} relevant chunks:\n")
        
        # Topic overview
        if results["topic_overview"]:
            print("[TOPIC OVERVIEW]")
            for item in results["topic_overview"]:
                print(f"  • {item['text']}")
                print(f"    Relevance: {item['relevance_score']:.2%}")
        
        # Learning objectives
        if results["learning_objectives"]:
            print("\n[LEARNING OBJECTIVES]")
            for item in results["learning_objectives"]:
                print(f"  • {item['text']}")
                print(f"    Relevance: {item['relevance_score']:.2%}")
        
        # Allowed concepts
        if results["allowed_concepts"]:
            print("\n[ALLOWED CONCEPTS]")
            for item in results["allowed_concepts"]:
                print(f"  • {item['text']}")
        
        # Disallowed concepts
        if results["disallowed_concepts"]:
            print("\n[DISALLOWED CONCEPTS]")
            for item in results["disallowed_concepts"]:
                print(f"  • {item['text']}")
        
        # Content blocks
        if results["content_blocks"]:
            print(f"\n[CONTENT] (Top {min(5, len(results['content_blocks']))} of {len(results['content_blocks'])})")
            for i, item in enumerate(results["content_blocks"][:5], 1):
                doc_type = item["metadata"]["doc_type"].replace("content_", "").upper()
                topic = item["metadata"]["topic_name"]
                print(f"\n  {i}. [{doc_type}] - {topic}")
                print(f"     Relevance: {item['relevance_score']:.2%}")
                text = item['text']
                if len(text) > 300:
                    text = text[:300] + "..."
                print(f"     {text}")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Document Q&A with RAG")
    parser.add_argument("--json", type=str, help="Path to JSON file")
    parser.add_argument("--pdf", type=str, help="Path to PDF file (optional)")
    parser.add_argument("--question", type=str, help="Question to ask (non-interactive mode)")
    parser.add_argument("--n-results", type=int, default=10, help="Number of results to retrieve")
    
    args = parser.parse_args()
    
    # If no arguments, use default example
    if not args.json:
        print("=" * 60)
        print("📖 DOCUMENT Q&A SYSTEM")
        print("=" * 60)
        print("\nNo arguments provided. Using example file...\n")
        
        # Default to the example file
        json_path = "ncert_maths_6-10/class6/json_output/fegp101.json"
        pdf_path = "ncert_maths_6-10/class6/fegp101.pdf"
        
        if not Path(json_path).exists():
            print(f"❌ Example file not found: {json_path}")
            print("\nUsage:")
            print("  python document_qa.py --json path/to/file.json --pdf path/to/file.pdf")
            print("\nOr run interactively:")
            print("  python document_qa.py")
            return
    else:
        json_path = args.json
        pdf_path = args.pdf
    
    try:
        # Initialize Q&A system
        qa = DocumentQA(json_path, pdf_path)
        
        if args.question:
            # Non-interactive mode
            results = qa.ask(args.question, n_results=args.n_results)
            qa._display_results(results)
            print("\n" + "=" * 60)
            print("LLM-READY CONTEXT")
            print("=" * 60)
            print(qa.format_for_llm(results))
        else:
            # Interactive mode
            qa.interactive_qa()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
