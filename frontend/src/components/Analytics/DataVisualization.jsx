import React from 'react';
import Plot from 'react-plotly.js';
import { BarChart3, Download, Settings } from 'lucide-react';

const DataVisualization = ({ chartData }) => {
  if (!chartData || !chartData.plotly_json) {
    return (
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
          Data Visualization
        </h3>
        <div className="text-center py-12">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600">No visualization data available</p>
          <p className="text-sm text-gray-500 mt-1">
            Ask questions about trends or data to generate charts
          </p>
        </div>
      </div>
    );
  }

  try {
    const plotData = JSON.parse(chartData.plotly_json);
    
    return (
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
            Data Visualization
          </h3>
          <div className="flex space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <Settings className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="relative">
          <Plot
            data={plotData.data}
            layout={{
              ...plotData.layout,
              autosize: true,
              height: 400,
              margin: { l: 50, r: 50, t: 50, b: 50 },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { family: 'Inter, sans-serif', size: 12 }
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
            }}
            style={{ width: '100%' }}
          />
        </div>

        {chartData.config && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Chart Type:</strong> {chartData.config.chart_type || 'Auto-generated'}
            </p>
            {chartData.config.description && (
              <p className="text-sm text-gray-600 mt-1">
                <strong>Description:</strong> {chartData.config.description}
              </p>
            )}
          </div>
        )}
      </div>
    );
  } catch (error) {
    console.error('Error rendering chart:', error);
    return (
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Data Visualization</h3>
        <div className="text-center py-8">
          <p className="text-red-600">Error loading visualization</p>
        </div>
      </div>
    );
  }
};

export default DataVisualization;