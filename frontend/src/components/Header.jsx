import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Search, Database } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <Database className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">SageWrite GraphRAG</h1>
          </div>
          
          <nav className="flex items-center space-x-6">
            <Link 
              to="/" 
              className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <FileText className="h-5 w-5" />
              <span>Upload</span>
            </Link>
            <Link 
              to="/query" 
              className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <Search className="h-5 w-5" />
              <span>Query</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

