"""
Celery tasks for document processing
"""

from celery import current_task
from tasks.celery_app import celery_app
from database.connection import get_sync_database
import time


@celery_app.task(bind=True)
def process_document(self, document_id: str):
    """Process a document through the GraphRAG pipeline"""
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting document processing..."}
        )
        
        # Get database connection
        db = get_sync_database()
        
        # Update document status to processing
        db.documents.update_one(
            {"_id": document_id},
            {"$set": {"status": "processing"}}
        )
        
        # Simulate processing steps
        steps = [
            "Parsing document...",
            "Extracting text sections...",
            "Generating embeddings...",
            "Extracting entities...",
            "Extracting relationships...",
            "Building knowledge graph...",
            "Finalizing..."
        ]
        
        for i, step in enumerate(steps):
            time.sleep(2)  # Simulate processing time
            progress = int((i + 1) / len(steps) * 100)
            
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": progress,
                    "total": 100,
                    "status": step
                }
            )
        
        # Update document status to processed
        db.documents.update_one(
            {"_id": document_id},
            {"$set": {"status": "processed"}}
        )
        
        return {
            "current": 100,
            "total": 100,
            "status": "Document processed successfully!",
            "result": f"Document {document_id} has been processed"
        }
        
    except Exception as e:
        # Update document status to failed
        db = get_sync_database()
        db.documents.update_one(
            {"_id": document_id},
            {"$set": {"status": "failed"}}
        )
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task
def cleanup_old_documents():
    """Clean up old processed documents (placeholder)"""
    # This would implement cleanup logic
    return "Cleanup completed"

