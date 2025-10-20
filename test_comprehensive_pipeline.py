#!/usr/bin/env python3
"""
Comprehensive GraphRAG Pipeline Test
Tests all 8 nodes of the GraphRAG pipeline with detailed logging and database verification
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_database
from app.pipelines.graphrag_pipeline import GraphRAGPipeline
from app.tasks.processing_tasks import process_document_task

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline_test.log')
    ]
)

logger = logging.getLogger(__name__)

class PipelineTestLogger:
    """Enhanced logger for pipeline testing with detailed output"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def log_node_start(self, node_name: str, state: Dict[str, Any]):
        """Log the start of a pipeline node"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTING NODE: {node_name.upper()}")
        logger.info(f"{'='*80}")
        
        # Log current state summary
        self._log_state_summary(state)
        
        # Store node start info
        self.results[node_name] = {
            "start_time": datetime.now().isoformat(),
            "input_state": self._summarize_state(state)
        }
    
    def log_node_end(self, node_name: str, state: Dict[str, Any]):
        """Log the end of a pipeline node"""
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ COMPLETED NODE: {node_name.upper()}")
        logger.info(f"{'='*80}")
        
        # Log detailed results
        self._log_detailed_results(node_name, state)
        
        # Update node results
        if node_name in self.results:
            self.results[node_name]["end_time"] = datetime.now().isoformat()
            self.results[node_name]["output_state"] = self._summarize_state(state)
            self.results[node_name]["duration"] = (
                datetime.fromisoformat(self.results[node_name]["end_time"]) - 
                datetime.fromisoformat(self.results[node_name]["start_time"])
            ).total_seconds()
    
    def _log_state_summary(self, state: Dict[str, Any]):
        """Log a summary of the current state"""
        logger.info(f"📊 STATE SUMMARY:")
        logger.info(f"  Document ID: {state.get('document_id', 'N/A')}")
        logger.info(f"  Sections: {len(state.get('sections', []))}")
        logger.info(f"  Temp Entities: {len(state.get('temp_entities', []))}")
        logger.info(f"  Temp Relationships: {len(state.get('temp_relationships', []))}")
        logger.info(f"  Doc Entities: {len(state.get('doc_entities', []))}")
        logger.info(f"  Doc Relationships: {len(state.get('doc_relationships', []))}")
        logger.info(f"  Final Entities: {len(state.get('final_entities', []))}")
        logger.info(f"  Final Relationships: {len(state.get('final_relationships', []))}")
        logger.info(f"  Errors: {len(state.get('errors', []))}")
    
    def _log_detailed_results(self, node_name: str, state: Dict[str, Any]):
        """Log detailed results for specific nodes"""
        if node_name == "map_entities":
            self._log_entities(state.get('temp_entities', []), "EXTRACTED ENTITIES")
        elif node_name == "map_relationships":
            self._log_relationships(state.get('temp_relationships', []), "EXTRACTED RELATIONSHIPS")
        elif node_name == "combine_entities":
            self._log_entities(state.get('doc_entities', []), "COMBINED ENTITIES")
        elif node_name == "combine_relationships":
            self._log_relationships(state.get('doc_relationships', []), "COMBINED RELATIONSHIPS")
        elif node_name == "reduce_entities":
            self._log_entities(state.get('final_entities', []), "REDUCED ENTITIES")
            self._log_entity_merges(state.get('entity_merges', []))
        elif node_name == "reduce_relationships":
            self._log_relationships(state.get('final_relationships', []), "REDUCED RELATIONSHIPS")
            self._log_contradictions(state.get('contradictions', []))
            self._log_resolutions(state.get('contradiction_resolutions', []))
        elif node_name == "consolidate_relationships":
            self._log_relationships(state.get('final_relationships', []), "CONSOLIDATED RELATIONSHIPS")
            self._log_consolidation_summary(state.get('consolidation_summary', {}))
        elif node_name == "update_global_graph":
            self._log_global_results(state.get('global_processing_results', {}))
        
        # Log errors if any
        errors = state.get('errors', [])
        if errors:
            logger.error(f"❌ ERRORS IN {node_name.upper()}:")
            for error in errors:
                logger.error(f"  - {error}")
    
    def _log_entities(self, entities: List[Dict[str, Any]], title: str):
        """Log entities in detail"""
        logger.info(f"\n📋 {title} ({len(entities)} total):")
        for i, entity in enumerate(entities, 1):
            logger.info(f"  {i}. {entity.get('entity_name', 'N/A')}")
            logger.info(f"     Type: {entity.get('entity_type', 'N/A')}")
            logger.info(f"     Category: {entity.get('entity_category', 'N/A')}")
            logger.info(f"     Description: {entity.get('description', entity.get('entity_description', 'N/A'))[:100]}...")
            logger.info(f"     Frequency: {entity.get('frequency', 1)}")
            logger.info(f"     Aliases: {entity.get('aliases', [])}")
            logger.info(f"     Section IDs: {entity.get('section_ids', [])}")
            logger.info("")
    
    def _log_relationships(self, relationships: List[Dict[str, Any]], title: str):
        """Log relationships in detail"""
        logger.info(f"\n🔗 {title} ({len(relationships)} total):")
        for i, rel in enumerate(relationships, 1):
            logger.info(f"  {i}. {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
            logger.info(f"     Type: {rel.get('relationship_type', 'N/A')}")
            logger.info(f"     Strength: {rel.get('relationship_strength', 'N/A')}")
            logger.info(f"     Description: {rel.get('description', 'N/A')[:100]}...")
            logger.info(f"     Section IDs: {rel.get('section_ids', [])}")
            logger.info("")
    
    def _log_entity_merges(self, merges: List[Dict[str, Any]]):
        """Log entity merge operations"""
        if merges:
            logger.info(f"\n🔄 ENTITY MERGES ({len(merges)} total):")
            for i, merge in enumerate(merges, 1):
                logger.info(f"  {i}. Merge: {merge}")
        else:
            logger.info("\n🔄 ENTITY MERGES: None")
    
    def _log_contradictions(self, contradictions: List[Dict[str, Any]]):
        """Log detected contradictions"""
        if contradictions:
            logger.info(f"\n⚠️ CONTRADICTIONS ({len(contradictions)} total):")
            for i, contradiction in enumerate(contradictions, 1):
                logger.info(f"  {i}. {contradiction}")
        else:
            logger.info("\n⚠️ CONTRADICTIONS: None detected")
    
    def _log_resolutions(self, resolutions: List[Dict[str, Any]]):
        """Log contradiction resolutions"""
        if resolutions:
            logger.info(f"\n✅ CONTRADICTION RESOLUTIONS ({len(resolutions)} total):")
            for i, resolution in enumerate(resolutions, 1):
                logger.info(f"  {i}. {resolution}")
        else:
            logger.info("\n✅ CONTRADICTION RESOLUTIONS: None")
    
    def _log_consolidation_summary(self, summary: Dict[str, Any]):
        """Log relationship consolidation summary"""
        logger.info(f"\n📊 CONSOLIDATION SUMMARY:")
        logger.info(f"  {summary}")
    
    def _log_global_results(self, results: Dict[str, Any]):
        """Log global graph processing results"""
        logger.info(f"\n🌐 GLOBAL GRAPH RESULTS:")
        logger.info(f"  Entities Processed: {results.get('entities_processed', 0)}")
        logger.info(f"  Relationships Processed: {results.get('relationships_processed', 0)}")
        logger.info(f"  New Entities Added: {results.get('new_entities_added', 0)}")
        logger.info(f"  New Relationships Added: {results.get('new_relationships_added', 0)}")
        logger.info(f"  Entities Updated: {results.get('entities_updated', 0)}")
        logger.info(f"  Relationships Updated: {results.get('relationships_updated', 0)}")
    
    def _summarize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the state"""
        return {
            "sections_count": len(state.get('sections', [])),
            "temp_entities_count": len(state.get('temp_entities', [])),
            "temp_relationships_count": len(state.get('temp_relationships', [])),
            "doc_entities_count": len(state.get('doc_entities', [])),
            "doc_relationships_count": len(state.get('doc_relationships', [])),
            "final_entities_count": len(state.get('final_entities', [])),
            "final_relationships_count": len(state.get('final_relationships', [])),
            "errors_count": len(state.get('errors', []))
        }
    
    def log_final_summary(self, final_result: Dict[str, Any]):
        """Log the final pipeline summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 FINAL RESULTS:")
        logger.info(f"  Document ID: {final_result.get('document_id', 'N/A')}")
        logger.info(f"  Success: {final_result.get('success', False)}")
        logger.info(f"  Entities Extracted: {final_result.get('entities_extracted', 0)}")
        logger.info(f"  Relationships Extracted: {final_result.get('relationships_extracted', 0)}")
        logger.info(f"  Final Entities: {len(final_result.get('final_entities', []))}")
        logger.info(f"  Final Relationships: {len(final_result.get('final_relationships', []))}")
        logger.info(f"  Entity Merges: {final_result.get('entity_merges', 0)}")
        logger.info(f"  Contradictions: {final_result.get('contradictions', 0)}")
        logger.info(f"  Resolutions: {final_result.get('contradiction_resolutions', 0)}")
        logger.info(f"  Total Duration: {total_duration:.2f} seconds")
        
        # Log node durations
        logger.info(f"\n⏱️ NODE DURATIONS:")
        for node_name, node_data in self.results.items():
            if "duration" in node_data:
                logger.info(f"  {node_name}: {node_data['duration']:.2f}s")
        
        # Save detailed results to file
        self._save_results_to_file(final_result)
    
    def _save_results_to_file(self, final_result: Dict[str, Any]):
        """Save detailed results to JSON file"""
        results_data = {
            "test_timestamp": self.start_time.isoformat(),
            "final_result": final_result,
            "node_results": self.results,
            "total_duration": (datetime.now() - self.start_time).total_seconds()
        }
        
        with open('pipeline_test_results.json', 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"📁 Detailed results saved to: pipeline_test_results.json")

async def test_comprehensive_pipeline():
    """Test the complete GraphRAG pipeline with detailed logging"""
    logger.info("🚀 Starting Comprehensive GraphRAG Pipeline Test")
    
    # Initialize test logger
    test_logger = PipelineTestLogger()
    
    try:
        # Create test document sections
        document_id = "test_doc_001"
        sections = [
            {
                "_id": "section_001",
                "title": "Abstract",
                "text": "CRISPR-Cas9 genome editing has revolutionized cancer research by enabling precise modifications to oncogenes and tumor suppressor genes. This study demonstrates the successful application of CRISPR-Cas9 to target TP53 mutations in colorectal cancer cell lines, resulting in significant apoptosis induction and tumor growth inhibition. The methodology combines single-guide RNA (sgRNA) design optimization with high-efficiency delivery systems, achieving 85% editing efficiency across multiple cell lines. Results show that CRISPR-Cas9-mediated TP53 restoration leads to 40% reduction in tumor proliferation rates and enhanced sensitivity to chemotherapeutic agents. These findings support the potential of CRISPR-Cas9 as a therapeutic approach for cancer treatment, particularly in cases with specific genetic mutations.",
                "type": "abstract",
                "position": 1
            },
            {
                "_id": "section_002", 
                "title": "Methods",
                "text": "We employed a comprehensive CRISPR-Cas9 workflow targeting TP53 mutations in HCT116 colorectal cancer cells. The experimental design included three main components: sgRNA design and validation, Cas9 delivery optimization, and functional assessment of gene editing outcomes. For sgRNA design, we utilized the CHOPCHOP algorithm to identify optimal targeting sequences within exons 5-8 of the TP53 gene, focusing on regions encoding the DNA-binding domain. The selected sgRNAs were cloned into pSpCas9(BB)-2A-GFP vectors and validated through in vitro cleavage assays. Cell culture experiments were conducted using HCT116 cells maintained in McCoy's 5A medium supplemented with 10% fetal bovine serum. Transfection was performed using Lipofectamine 3000 with 2 μg of Cas9-sgRNA plasmids per 10^5 cells. Post-transfection, cells were sorted for GFP expression and cultured for 72 hours before analysis. Gene editing efficiency was assessed using T7 endonuclease I assays and Sanger sequencing, while functional outcomes were evaluated through apoptosis assays (Annexin V/PI staining) and proliferation measurements (MTS assay). Statistical analysis was performed using GraphPad Prism with Student's t-test for pairwise comparisons and ANOVA for multiple group analyses.",
                "type": "methods",
                "position": 2
            },
            {
                "_id": "section_003",
                "title": "Results", 
                "text": "CRISPR-Cas9-mediated TP53 editing demonstrated remarkable efficacy in HCT116 colorectal cancer cells. Gene editing efficiency reached 85.3% ± 4.2% across three independent experiments, as confirmed by T7 endonuclease I assays and sequencing analysis. Functional characterization revealed significant biological effects: TP53 restoration resulted in 42.7% ± 6.1% reduction in cell proliferation compared to control groups (p < 0.001). Apoptosis induction was particularly pronounced, with 67.3% ± 8.4% of edited cells showing positive Annexin V staining after 48 hours. Western blot analysis confirmed increased expression of p21 and Bax proteins, downstream targets of functional TP53. Notably, edited cells exhibited enhanced sensitivity to 5-fluorouracil treatment, with IC50 values decreasing from 12.3 μM to 4.7 μM (p < 0.01). Flow cytometry analysis revealed cell cycle arrest at G1/S checkpoint in 78.2% of TP53-restored cells. These results demonstrate that CRISPR-Cas9 can effectively restore tumor suppressor function and sensitize cancer cells to conventional chemotherapy. The study also identified potential off-target effects in 3.2% of analyzed sites, primarily in genes with sequence homology to the target region. Long-term culture experiments showed stable TP53 expression for up to 12 passages, indicating durable editing outcomes.",
                "type": "results",
                "position": 3
            }
        ]
        
        logger.info(f"📄 Created test document with {len(sections)} sections")
        logger.info(f"  Document ID: {document_id}")
        for section in sections:
            logger.info(f"  - {section['title']}: {len(section['text'])} characters")
        
        # Initialize pipeline
        pipeline = GraphRAGPipeline()
        logger.info("✅ Pipeline initialized successfully")
        
        # Process document through pipeline
        logger.info("\n🚀 Starting document processing...")
        result = await pipeline.process_document(document_id, sections)
        
        # Log final results
        test_logger.log_final_summary(result)
        
        # Verify database storage
        await verify_database_storage(document_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}")
        raise

async def verify_database_storage(document_id: str):
    """Verify what was stored in the database"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 VERIFYING DATABASE STORAGE")
    logger.info(f"{'='*80}")
    
    try:
        # Get database connection
        db = get_database()
        
        # Check entities
        entities = list(db.entities.find({"paper_ids": document_id}))
        logger.info(f"📊 ENTITIES IN DATABASE: {len(entities)}")
        for entity in entities:
            logger.info(f"  - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
            logger.info(f"    Category: {entity.get('entity_category', 'N/A')}")
            logger.info(f"    Frequency: {entity.get('frequency', 1)}")
            logger.info(f"    Paper IDs: {entity.get('paper_ids', [])}")
            logger.info("")
        
        # Check relationships
        relationships = list(db.relationships.find({"paper_ids": document_id}))
        logger.info(f"📊 RELATIONSHIPS IN DATABASE: {len(relationships)}")
        for rel in relationships:
            logger.info(f"  - {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
            logger.info(f"    Type: {rel.get('relationship_type', 'N/A')}")
            logger.info(f"    Strength: {rel.get('relationship_strength', 'N/A')}")
            logger.info(f"    Paper IDs: {rel.get('paper_ids', [])}")
            logger.info("")
        
        # Check sections
        sections = list(db.sections.find({"document_id": document_id}))
        logger.info(f"📊 SECTIONS IN DATABASE: {len(sections)}")
        for section in sections:
            logger.info(f"  - {section.get('title', 'N/A')} ({section.get('type', 'N/A')})")
            logger.info(f"    Text length: {len(section.get('text', ''))}")
            logger.info(f"    Has embedding: {'embedding' in section}")
            logger.info("")
        
        logger.info(f"✅ Database verification complete!")
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")

if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(test_comprehensive_pipeline())

