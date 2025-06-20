import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';
import AdvancedUpload from './AdvancedUpload';

const UploadPage = ({ onUpload, documents }) => {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (files) => {
    setIsUploading(true);
    setUploadStatus(null);

    try {
      for (const file of files) {
        await onUpload(file);
      }
      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded ${files.length} file(s)`
      });
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Upload failed'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const clearStatus = () => {
    setUploadStatus(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Documents</h1>
        <p className="text-gray-600">
          Upload PDF documents to analyze and chat with their content using AI.
        </p>
      </div>

      {/* Status Messages */}
      {uploadStatus && (
        <div className={`
          mb-6 p-4 rounded-lg border flex items-center justify-between
          ${uploadStatus.type === 'success' 
            ? 'bg-green-50 border-green-200 text-green-800' 
            : 'bg-red-50 border-red-200 text-red-800'
          }
        `}>
          <div className="flex items-center">
            {uploadStatus.type === 'success' ? (
              <CheckCircle className="w-5 h-5 mr-2" />
            ) : (
              <AlertCircle className="w-5 h-5 mr-2" />
            )}
            <span>{uploadStatus.message}</span>
          </div>
          <button
            onClick={clearStatus}
            className="p-1 hover:bg-white hover:bg-opacity-20 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Component */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <AdvancedUpload
          onUpload={handleUpload}
          isUploading={isUploading}
          accept=".pdf"
          maxSize={50 * 1024 * 1024} // 50MB
          multiple={true}
        />
      </div>

      {/* Uploaded Documents */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Uploaded Documents ({documents?.length || 0})
          </h2>
        </div>
        
        <div className="p-6">
          {documents && documents.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <FileText className="w-8 h-8 text-blue-600 flex-shrink-0" />
                    <span className="text-xs text-gray-500">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                  
                  <h3 className="font-medium text-gray-900 mb-1 truncate">
                    {doc.name}
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {doc.pages} pages • {Math.round(doc.size / 1024)} KB
                  </p>
                  
                  {doc.status && (
                    <div className={`
                      inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                      ${doc.status === 'processed' 
                        ? 'bg-green-100 text-green-800' 
                        : doc.status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                      }
                    `}>
                      {doc.status === 'processed' && <CheckCircle className="w-3 h-3 mr-1" />}
                      {doc.status === 'processing' && <Upload className="w-3 h-3 mr-1 animate-spin" />}
                      {doc.status === 'error' && <AlertCircle className="w-3 h-3 mr-1" />}
                      {doc.status}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded</h3>
              <p className="text-gray-600 mb-4">
                Upload your first PDF document to get started with AI-powered analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
