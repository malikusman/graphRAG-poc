import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';

const ResultsDisplay = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Query Results
          </h2>
          <p className="text-gray-600">
            Results will be displayed here after processing your query
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;


