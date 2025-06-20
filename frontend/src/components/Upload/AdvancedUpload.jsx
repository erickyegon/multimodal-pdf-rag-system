import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const AdvancedUpload = ({ onUpload, uploading, progress }) => {
  const [files, setFiles] = useState([]);
  const [uploadResults, setUploadResults] = useState({});

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    rejectedFiles.forEach(file => {
      console.error('Rejected file:', file.file.name, file.errors);
    });

    // Add accepted files to the list
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending'
    }));

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true
  });

  const uploadFile = async (fileItem) => {
    try {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { ...f, status: 'uploading' } : f
      ));

      const result = await onUpload(fileItem.file, (progress) => {
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id ? { ...f, progress } : f
        ));
      });

      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { ...f, status: 'completed', result } : f
      ));

      setUploadResults(prev => ({
        ...prev,
        [fileItem.id]: result
      }));

    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id ? { ...f, status: 'error', error: error.message } : f
      ));
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setUploadResults(prev => {
      const { [fileId]: removed, ...rest } = prev;
      return rest;
    });
  };

  const uploadAllFiles = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    for (const file of pendingFiles) {
      await uploadFile(file);
    }
  };

  return (
    <div className="space-y-6">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-blue-600">Drop the PDF files here...</p>
        ) : (
          <div>
            <p className="text-gray-600 mb-2">
              Drag & drop PDF files here, or click to select
            </p>
            <p className="text-sm text-gray-400">
              Maximum file size: 100MB per file
            </p>
          </div>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Files to Upload ({files.length})</h3>
            <button
              onClick={uploadAllFiles}
              disabled={uploading || files.every(f => f.status !== 'pending')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Upload All
            </button>
          </div>

          <div className="space-y-2">
            {files.map((fileItem) => (
              <FileUploadItem
                key={fileItem.id}
                fileItem={fileItem}
                onUpload={() => uploadFile(fileItem)}
                onRemove={() => removeFile(fileItem.id)}
                result={uploadResults[fileItem.id]}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const FileUploadItem = ({ fileItem, onUpload, onRemove, result }) => {
  const { file, status, progress = 0, error } = fileItem;

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'uploading':
        return (
          <div className="w-8 h-8">
            <CircularProgressbar
              value={progress}
              text={`${Math.round(progress)}%`}
              styles={buildStyles({
                textSize: '24px',
                pathColor: '#3B82F6',
                textColor: '#3B82F6',
              })}
            />
          </div>
        );
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
      <div className="flex items-center space-x-3">
        {getStatusIcon()}
        <div>
          <p className="font-medium text-gray-900">{file.name}</p>
          <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
          {error && <p className="text-sm text-red-500">{error}</p>}
          {result && (
            <div className="text-xs text-green-600 mt-1">
              {result.page_count} pages, {result.text_chunks} chunks, {result.tables_found} tables
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        {status === 'pending' && (
          <button
            onClick={onUpload}
            className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm hover:bg-blue-200"
          >
            Upload
          </button>
        )}
        <button
          onClick={onRemove}
          className="text-gray-400 hover:text-red-500"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default AdvancedUpload;