# Test Documents for Multi-Document GraphRAG System

This directory contains realistic research papers designed to test the multi-document GraphRAG system's ability to:

1. **Extract entities and relationships** from scientific text
2. **Canonicalize entities** across multiple documents
3. **Detect contradictions** in relationships
4. **Maintain global graph consistency**

## Test Document Overview

### CRISPR Research Papers (Entity Canonicalization Test)

#### 1. `crispr_genome_editing.txt`
- **Focus**: CRISPR-Cas9 genome editing in human cells
- **Key Entities**: CRISPR-Cas9, Cas9, TP53, p53, human cells, genome editing
- **Key Relationships**: CRISPR-Cas9 edits TP53, TP53 regulates cell cycle
- **Test Purpose**: Extract entities with canonical names

#### 2. `cas9_gene_therapy.txt`
- **Focus**: Cas9-mediated gene therapy applications
- **Key Entities**: Cas9, CRISPR, TP53, p53, gene therapy, off-target effects
- **Key Relationships**: Cas9 causes off-target effects, TP53 prevents cancer
- **Test Purpose**: Same entities with different names (Cas9 vs CRISPR-Cas9)

#### 3. `crispr_offtarget_analysis.txt`
- **Focus**: CRISPR system off-target analysis
- **Key Entities**: CRISPR-Cas9, off-target effects, specificity, efficiency
- **Key Relationships**: CRISPR-Cas9 has off-target effects, specificity improves efficiency
- **Test Purpose**: Additional relationships about the same entities

### Cancer Research Papers (Contradiction Detection Test)

#### 4. `tp53_tumor_suppressor.txt`
- **Focus**: TP53 tumor suppressor function
- **Key Entities**: TP53, p53, apoptosis, cell cycle, tumor suppression
- **Key Relationships**: TP53 increases apoptosis, TP53 decreases cell proliferation
- **Test Purpose**: Positive relationships about TP53 function

#### 5. `tp53_mutations_cancer.txt`
- **Focus**: TP53 mutations in cancer development
- **Key Entities**: TP53, p53, mutations, cancer, cell proliferation
- **Key Relationships**: TP53 mutations increase cell proliferation, TP53 mutations decrease apoptosis
- **Test Purpose**: Contradictory relationships about TP53 function

### Drug Development Paper (Complex Relationship Networks)

#### 6. `metformin_cancer_treatment.txt`
- **Focus**: Metformin in cancer treatment
- **Key Entities**: Metformin, cancer, AMPK, mTOR, cell growth
- **Key Relationships**: Metformin inhibits mTOR, Metformin activates AMPK, AMPK inhibits cell growth
- **Test Purpose**: Multi-step relationship chains and complex networks

## Expected Test Results

### Entity Canonicalization
- **CRISPR-Cas9** should be canonicalized from: "CRISPR-Cas9", "Cas9", "CRISPR"
- **TP53** should be canonicalized from: "TP53", "p53"
- **Metformin** should be canonicalized from: "Metformin", "1,1-dimethylbiguanide"

### Contradiction Detection
- **TP53 vs Apoptosis**: "TP53 increases apoptosis" vs "TP53 mutations decrease apoptosis"
- **CRISPR-Cas9 vs Off-target**: "CRISPR-Cas9 has off-target effects" vs "CRISPR-Cas9 prevents off-target effects"

### Global Graph Consistency
- No orphaned entities (entities with no relationships)
- Consistent relationship strengths for the same entity pairs
- Proper provenance tracking across documents

## Running the Tests

1. **Start the application**:
   ```bash
   cd /Users/usman/Documents/projects/sagewrite-app
   docker-compose up -d
   ```

2. **Run the test script**:
   ```bash
   python run_tests.py
   ```

3. **Check results**:
   - Test results will be saved to `test_results.json`
   - Console output will show real-time progress
   - Each test phase will report success/failure

## Test Validation Criteria

### ✅ Success Criteria
- **Entity Canonicalization**: Similar entities merged correctly
- **Contradiction Detection**: Conflicting relationships identified
- **Global Consistency**: No orphaned entities, consistent relationships
- **Performance**: All documents processed within 10 minutes

### ❌ Failure Indicators
- Entities not canonicalized (duplicates in global graph)
- Contradictions not detected
- Orphaned entities present
- Processing timeouts or errors

## Troubleshooting

### Common Issues
1. **API Connection Errors**: Ensure the application is running on localhost:8000
2. **Document Upload Failures**: Check file permissions and format
3. **Processing Timeouts**: Increase timeout values in test script
4. **Missing Entities**: Verify LLM prompts are working correctly

### Debug Information
- Check application logs for detailed error messages
- Review `test_results.json` for specific failure details
- Use the API endpoints directly to test individual components

## Expected Processing Flow

1. **Upload Phase**: All 6 documents uploaded via API
2. **Processing Phase**: Each document processed through Map-Combine-Reduce pipeline
3. **Global Update Phase**: Entities and relationships integrated into global graph
4. **Validation Phase**: Tests run to verify canonicalization, contradictions, and consistency
5. **Report Phase**: Results compiled and saved

This test suite provides comprehensive coverage of the multi-document GraphRAG system's core functionality.
