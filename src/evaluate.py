"""Evaluation script to automate RAG testing."""
import os
import sys
import csv

# Ensure the root directory is in the path so we can import src
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.retrieve import hybrid_retrieve
from src.generate import generate_answer
from src.ingest import load_pdf, chunk_pages
from src.embed import embed_and_store

def run_evaluation(pdf_path: str = None):
    csv_path = os.path.join(ROOT, "eval", "test_questions.csv")
    
    if not os.path.exists(csv_path):
        print(f"[Error] {csv_path} not found. Please create it first.")
        return

    # 1. Option to ingest PDF if provided
    if pdf_path:
        if not os.path.exists(pdf_path):
            print(f"[Error] PDF not found at {pdf_path}")
            return
        print(f"Ingesting PDF: {pdf_path}...")
        pages = load_pdf(pdf_path)
        chunks = chunk_pages(pages)
        embed_and_store(chunks)
        print("Ingestion complete. Starting evaluation...\n")

    # 2. Read questions from CSV
    rows = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    if not rows:
        print("[Warning] No questions found in the CSV file.")
        return

    print(f"Running {len(rows)} evaluation questions through the RAG pipeline...")

    # 3. Query RAG and update actual_answer
    updated_count = 0
    for idx, row in enumerate(rows, 1):
        question = row.get("question")
        if not question or question.startswith("Placeholder"):
            continue

        print(f"\n[{idx}/{len(rows)}] Question: {question}")
        try:
            # Retrieve chunks
            chunks = hybrid_retrieve(question, collection_name="textbook", top_k=5)
            
            # Generate answer
            result = generate_answer(question, chunks)
            actual_answer = result.get("answer", "")
            
            # Save actual answer
            row["actual_answer"] = actual_answer
            updated_count += 1
            
            print(f"Answer: {actual_answer}")
            
            # Print citations for quick verification
            sources = result.get("sources", [])
            cited_pages = [str(s["page"]) for s in sources]
            print(f"Cited pages: {', '.join(cited_pages)}")
            
        except Exception as e:
            print(f"[Error] {e}")
            row["actual_answer"] = f"Error: {e}"

    # 4. Write back to CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n\nDone! Updated {updated_count} actual answers in {csv_path}")
    print("Next step: Open the CSV file and manually fill in the 'correctness' (1-3) and 'citation_correct' (yes/no) columns.")

if __name__ == "__main__":
    # If a PDF path is passed as command line argument, ingest it first
    pdf_to_ingest = sys.argv[1] if len(sys.argv) > 1 else None
    run_evaluation(pdf_to_ingest)
