#!/usr/bin/env python3
"""
Test the Enhanced GraphRAG Pipeline with detailed logging
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
from app.pipelines.graphrag_pipeline_enhanced import EnhancedGraphRAGPipeline

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_pipeline_test.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_enhanced_pipeline():
    """Test the enhanced GraphRAG pipeline with detailed logging"""
    logger.info("🚀 Starting Enhanced GraphRAG Pipeline Test")
    
    try:
        # Create test document sections
        document_id = "test_doc_comprehensive_001"
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
        
        # Initialize enhanced pipeline
        pipeline = EnhancedGraphRAGPipeline()
        logger.info("✅ Enhanced pipeline initialized successfully")
        
        # Process document through pipeline
        start_time = datetime.now()
        result = await pipeline.process_document(document_id, sections)
        end_time = datetime.now()
        
        # Log final results
        duration = (end_time - start_time).total_seconds()
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 ENHANCED PIPELINE TEST COMPLETED!")
        logger.info(f"{'='*80}")
        logger.info(f"📊 FINAL RESULTS:")
        logger.info(f"  Document ID: {result.get('document_id', 'N/A')}")
        logger.info(f"  Success: {result.get('success', False)}")
        logger.info(f"  Entities Extracted: {result.get('entities_extracted', 0)}")
        logger.info(f"  Relationships Extracted: {result.get('relationships_extracted', 0)}")
        logger.info(f"  Final Entities: {len(result.get('final_entities', []))}")
        logger.info(f"  Final Relationships: {len(result.get('final_relationships', []))}")
        logger.info(f"  Entity Merges: {result.get('entity_merges', 0)}")
        logger.info(f"  Contradictions: {result.get('contradictions', 0)}")
        logger.info(f"  Resolutions: {result.get('contradiction_resolutions', 0)}")
        logger.info(f"  Total Duration: {duration:.2f} seconds")
        
        # Save results to file
        results_data = {
            "test_timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "result": result
        }
        
        with open('enhanced_pipeline_results.json', 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"📁 Results saved to: enhanced_pipeline_results.json")
        
        # Verify database storage
        await verify_database_storage(document_id)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Enhanced pipeline test failed: {str(e)}")
        raise

async def verify_database_storage(document_id: str):
    """Verify what was stored in the database"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 VERIFYING DATABASE STORAGE")
    logger.info(f"{'='*80}")
    
    try:
        # Get database connection
        db = await get_database()
        
        # Check entities
        entities = list(db.entities.find({"paper_ids": document_id}))
        logger.info(f"📊 ENTITIES IN DATABASE: {len(entities)}")
        for entity in entities:
            logger.info(f"  - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
            logger.info(f"    Category: {entity.get('entity_category', 'N/A')}")
            logger.info(f"    Frequency: {entity.get('frequency', 1)}")
            logger.info(f"    Paper IDs: {entity.get('paper_ids', [])}")
            logger.info(f"    Section IDs: {entity.get('section_ids', [])}")
            logger.info("")
        
        # Check relationships
        relationships = list(db.relationships.find({"paper_ids": document_id}))
        logger.info(f"📊 RELATIONSHIPS IN DATABASE: {len(relationships)}")
        for rel in relationships:
            logger.info(f"  - {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
            logger.info(f"    Type: {rel.get('relationship_type', 'N/A')}")
            logger.info(f"    Strength: {rel.get('relationship_strength', 'N/A')}")
            logger.info(f"    Paper IDs: {rel.get('paper_ids', [])}")
            logger.info(f"    Section IDs: {rel.get('section_ids', [])}")
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
    # Run the enhanced pipeline test
    asyncio.run(test_enhanced_pipeline())
