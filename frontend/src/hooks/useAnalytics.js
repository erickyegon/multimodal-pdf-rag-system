import { useState, useCallback } from 'react';
import ApiClient from '../utils/api';

export const useAnalytics = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const runAnalysis = useCallback(async (query, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await ApiClient.runAnalytics(query, options.generateChart);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    runAnalysis,
    clearData
  };
};