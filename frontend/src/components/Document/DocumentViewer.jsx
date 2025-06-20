import React, { useState } from 'react';
import { 
  FileText, 
  ZoomIn, 
  ZoomOut, 
  Download, 
  ChevronLeft, 
  ChevronRight,
  Eye,
  Info
} from 'lucide-react';

const DocumentViewer = ({ document }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(100);

  if (!document) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Document Selected</h3>
          <p className="text-gray-600">Select a document to view its content</p>
        </div>
      </div>
    );
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 50));
  };

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, document.pages || 1));
  };

  const handleDownload = () => {
    // In a real implementation, this would trigger a download
    console.log('Download document:', document.name);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="font-medium text-gray-900 truncate max-w-48">
              {document.name}
            </h3>
            <p className="text-xs text-gray-500">
              {document.pages} pages • {Math.round(document.size / 1024)} KB
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleDownload}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
        {/* Page Navigation */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          
          <span className="text-sm text-gray-600">
            Page {currentPage} of {document.pages || 1}
          </span>
          
          <button
            onClick={handleNextPage}
            disabled={currentPage >= (document.pages || 1)}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= 50}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <span className="text-sm text-gray-600 min-w-12 text-center">
            {zoom}%
          </span>
          
          <button
            onClick={handleZoomIn}
            disabled={zoom >= 200}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Document Content */}
      <div className="flex-1 overflow-auto p-4">
        {document.preview_url ? (
          <div className="flex justify-center">
            <div 
              className="border border-gray-300 shadow-lg bg-white"
              style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
            >
              <img
                src={`${document.preview_url}?page=${currentPage}`}
                alt={`Page ${currentPage} of ${document.name}`}
                className="max-w-full h-auto"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <div className="hidden p-8 text-center">
                <Eye className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">Preview not available</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Eye className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Preview Not Available</h3>
              <p className="text-gray-600 mb-4">
                Document preview is being generated or not supported.
              </p>
              {document.content && (
                <div className="max-w-2xl mx-auto text-left">
                  <div className="bg-gray-50 rounded-lg p-4 border">
                    <div className="flex items-center mb-2">
                      <Info className="w-4 h-4 text-blue-600 mr-2" />
                      <span className="text-sm font-medium text-gray-900">Document Content</span>
                    </div>
                    <div className="text-sm text-gray-700 max-h-64 overflow-y-auto">
                      {document.content.substring(0, 1000)}
                      {document.content.length > 1000 && '...'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Uploaded: {new Date(document.uploaded_at).toLocaleDateString()}</span>
          <span>Status: {document.status || 'Unknown'}</span>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
