import React, { useState } from 'react';
import { Search, Send, Brain } from 'lucide-react';
import toast from 'react-hot-toast';

const QueryInterface = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch('/api/v1/queries/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          max_results: 10,
          include_graph: true,
          max_hops: 3
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        toast.success('Query processed successfully!');
      } else {
        throw new Error('Query failed');
      }
    } catch (error) {
      toast.error('Failed to process query');
      console.error('Query error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <Brain className="h-16 w-16 text-purple-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            GraphRAG Query Interface
          </h2>
          <p className="text-gray-600">
            Ask complex questions that require multi-hop reasoning across documents
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Which methods improved accuracy on ImageNet dataset for computer vision tasks since 2020?"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                <span>Search</span>
              </>
            )}
          </button>
        </form>

        {result && (
          <div className="mt-8 space-y-6">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Answer</h3>
              <p className="text-gray-700">{result.answer}</p>
              <p className="text-sm text-gray-500 mt-2">
                Processing time: {result.processing_time.toFixed(2)}s
              </p>
            </div>

            {result.sources && result.sources.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sources</h3>
                <div className="space-y-3">
                  {result.sources.map((source, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border">
                      <h4 className="font-medium text-gray-900">{source.document_title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{source.content}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        Relevance: {(source.relevance_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.graph_paths && result.graph_paths.length > 0 && (
              <div className="bg-green-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Graph Paths</h3>
                <div className="space-y-3">
                  {result.graph_paths.map((path, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border">
                      <div className="flex items-center space-x-2">
                        {path.path.map((node, nodeIndex) => (
                          <React.Fragment key={nodeIndex}>
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                              {node}
                            </span>
                            {nodeIndex < path.path.length - 1 && (
                              <span className="text-gray-400">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        Strength: {(path.total_strength * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryInterface;


