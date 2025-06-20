import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { Download, Maximize, Settings, RefreshCw } from 'lucide-react';

const PlotlyChart = ({ 
  data, 
  layout = {}, 
  config = {}, 
  title,
  onExport,
  onRefresh,
  className = ""
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const defaultLayout = {
    autosize: true,
    margin: { l: 50, r: 50, t: 50, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { 
      family: 'Inter, sans-serif', 
      size: 12 
    },
    showlegend: true,
    ...layout
  };

  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: title || 'chart',
      height: 500,
      width: 700,
      scale: 1
    },
    ...config
  };

  const handleExport = () => {
    if (onExport) {
      onExport();
    } else {
      // Default export functionality
      const plotElement = document.querySelector('.js-plotly-plot');
      if (plotElement) {
        // Trigger Plotly's built-in download
        const downloadButton = plotElement.querySelector('[data-title="Download plot as a png"]');
        if (downloadButton) {
          downloadButton.click();
        }
      }
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!data || data.length === 0) {
    return (
      <div className={`bg-white p-6 rounded-lg border ${className}`}>
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-lg flex items-center justify-center">
            📊
          </div>
          <p className="text-gray-600">No data to display</p>
        </div>
      </div>
    );
  }

  const chartHeight = isFullscreen ? window.innerHeight - 100 : 400;

  return (
    <>
      <div className={`bg-white rounded-lg border ${className} ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
        {/* Chart Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">
            {title || defaultLayout.title?.text || 'Chart'}
          </h3>
          <div className="flex space-x-2">
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Chart settings"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={handleExport}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Export chart"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={toggleFullscreen}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              <Maximize className="w-4 h-4" />
            </button>
            {isFullscreen && (
              <button
                onClick={() => setIsFullscreen(false)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Close"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="p-4 border-b bg-gray-50">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block text-gray-700 mb-1">Chart Type</label>
                <select className="w-full p-2 border rounded">
                  <option>Auto-detected</option>
                  <option>Line Chart</option>
                  <option>Bar Chart</option>
                  <option>Scatter Plot</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 mb-1">Theme</label>
                <select className="w-full p-2 border rounded">
                  <option>Default</option>
                  <option>Dark</option>
                  <option>Minimal</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Chart Content */}
        <div className="p-4">
          <Plot
            data={data}
            layout={{
              ...defaultLayout,
              height: chartHeight,
              title: isFullscreen ? { ...defaultLayout.title, text: title } : undefined
            }}
            config={defaultConfig}
            style={{ width: '100%' }}
            useResizeHandler={true}
          />
        </div>
      </div>

      {/* Fullscreen Overlay */}
      {isFullscreen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsFullscreen(false)}
        />
      )}
    </>
  );
};

export default PlotlyChart;