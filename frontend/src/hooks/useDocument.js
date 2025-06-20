import { useState, useCallback } from 'react';
import { toast } from 'react-toastify';

export const useDocument = () => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadDocument = useCallback(async (file, onProgress) => {
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          setUploadProgress(progress);
          onProgress?.(progress);
        }
      });

      const uploadPromise = new Promise((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        };
        xhr.onerror = () => reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/upload/upload`);
      xhr.send(formData);

      const result = await uploadPromise;

      const newDocument = {
        id: Date.now().toString(),
        name: file.name,
        size: file.size,
        uploadDate: new Date(),
        pageCount: result.page_count,
        textChunks: result.text_chunks,
        tablesFound: result.tables_found,
        imagesFound: result.images_found,
        status: 'processed'
      };

      setDocuments(prev => [...prev, newDocument]);
      toast.success(`Document "${file.name}" uploaded successfully!`);

      return newDocument;

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(`Failed to upload "${file.name}": ${error.message}`);
      throw error;
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, []);

  const deleteDocument = useCallback(async (documentId) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/upload/documents/${documentId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        toast.success('Document deleted successfully');
      } else {
        throw new Error('Failed to delete document');
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to delete document');
    }
  }, []);

  const getDocuments = useCallback(async () => {
    try {
      console.log('useDocument: Fetching documents from API...');
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      console.log('useDocument: API URL:', apiUrl);

      // Immediate fallback - don't wait for API
      setDocuments([]);
      console.log('useDocument: Set empty documents array immediately');

      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.log('useDocument: Request timed out after 2 seconds');
      }, 2000); // Reduced to 2 seconds

      const response = await fetch(`${apiUrl}/api/v1/upload/documents`, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const docs = await response.json();
        console.log('useDocument: Documents fetched successfully:', docs);
        setDocuments(docs);
      } else {
        console.warn('useDocument: API returned error, keeping empty array');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.warn('useDocument: Request aborted, keeping empty array');
      } else {
        console.error('useDocument: Error fetching documents:', error);
      }
      // Documents already set to empty array above
    }
  }, []);

  const getDocumentStats = useCallback((documentId) => {
    const doc = documents.find(d => d.id === documentId);
    if (!doc) return null;

    return {
      pageCount: doc.pageCount,
      textChunks: doc.textChunks,
      tablesFound: doc.tablesFound,
      imagesFound: doc.imagesFound,
      size: doc.size,
      uploadDate: doc.uploadDate
    };
  }, [documents]);

  return {
    documents,
    uploading,
    uploadProgress,
    uploadDocument,
    deleteDocument,
    getDocuments,
    getDocumentStats
  };
};