import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, FileText, Eye, Download } from 'lucide-react';
import TrendAnalysis from './TrendAnalysis';
import DataVisualization from './DataVisualization';
import InsightsSummary from './InsightsSummary';

const AnalyticsPage = ({ currentDocument }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState('trends');

  const runAnalysis = async (query, analysisType = 'general') => {
    if (!currentDocument) return;

    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/analytics/analytics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          generate_chart: true,
          chart_type: analysisType === 'trends' ? 'line' : 'bar'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnalyticsData(result);
      }
    } catch (error) {
      console.error('Analytics error:', error);
    } finally {
      setLoading(false);
    }
  };

  const predefinedQueries = [
    {
      id: 'revenue-trends',
      title: 'Revenue Trends',
      query: 'Show me revenue trends over time',
      type: 'trends',
      icon: TrendingUp
    },
    {
      id: 'performance-metrics',
      title: 'Performance Metrics',
      query: 'Analyze key performance indicators and metrics',
      type: 'metrics',
      icon: BarChart3
    },
    {
      id: 'data-summary',
      title: 'Data Summary',
      query: 'Provide a comprehensive summary of all data',
      type: 'summary',
      icon: FileText
    }
  ];

  if (!currentDocument) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">No Document Selected</h3>
          <p className="text-gray-500">Please select a document to run analytics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Document: {currentDocument.name}</p>
        </div>
        <div className="flex space-x-2">
          {analyticsData && (
            <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          )}
        </div>
      </div>

      {/* Quick Analysis Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {predefinedQueries.map((item) => (
          <button
            key={item.id}
            onClick={() => runAnalysis(item.query, item.type)}
            disabled={loading}
            className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50"
          >
            <item.icon className="w-8 h-8 text-blue-600 mb-2" />
            <h3 className="font-semibold text-gray-900">{item.title}</h3>
            <p className="text-sm text-gray-600 mt-1">{item.query}</p>
          </button>
        ))}
      </div>

      {/* Custom Query */}
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="font-semibold mb-3">Custom Analysis</h3>
        <div className="flex space-x-3">
          <input
            type="text"
            placeholder="Enter your analysis query..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                runAnalysis(e.target.value.trim());
                e.target.value = '';
              }
            }}
          />
          <button
            onClick={() => {
              const input = document.querySelector('input[placeholder="Enter your analysis query..."]');
              if (input.value.trim()) {
                runAnalysis(input.value.trim());
                input.value = '';
              }
            }}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Results */}
      {analyticsData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <TrendAnalysis data={analyticsData} />
            <InsightsSummary insights={analyticsData.insights} />
          </div>
          <div>
            <DataVisualization chartData={analyticsData.chart_data} />
          </div>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Analyzing document...</span>
        </div>
      )}
    </div>
  );
};

export default AnalyticsPage;