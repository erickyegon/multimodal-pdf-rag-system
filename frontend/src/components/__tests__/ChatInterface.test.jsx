import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInterface from '../Chat/ChatInterface';

// Mock react-plotly.js
jest.mock('react-plotly.js', () => {
  return function Plot() {
    return <div data-testid="plotly-chart">Chart</div>;
  };
});

describe('ChatInterface', () => {
  const mockProps = {
    messages: [],
    onSendMessage: jest.fn(),
    loading: false,
    currentDocument: { name: 'test.pdf', id: '1' }
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders chat interface correctly', () => {
    render(<ChatInterface {...mockProps} />);
    
    expect(screen.getByPlaceholderText(/ask a question about your document/i)).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('sends message when form is submitted', async () => {
    render(<ChatInterface {...mockProps} />);
    
    const input = screen.getByPlaceholderText(/ask a question about your document/i);
    const button = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockProps.onSendMessage).toHaveBeenCalledWith('Test message');
    });
  });

  test('displays messages correctly', () => {
    const messages = [
      {
        id: '1',
        type: 'user',
        content: 'Hello',
        timestamp: new Date()
      },
      {
        id: '2',
        type: 'assistant',
        content: 'Hi there!',
        timestamp: new Date()
      }
    ];

    render(<ChatInterface {...mockProps} messages={messages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  test('disables input when no document is selected', () => {
    render(<ChatInterface {...mockProps} currentDocument={null} />);
    
    const input = screen.getByPlaceholderText(/please upload a document first/i);
    expect(input).toBeDisabled();
  });

  test('shows loading state', () => {
    render(<ChatInterface {...mockProps} loading={true} />);
    
    expect(screen.getByText(/analyzing document/i)).toBeInTheDocument();
  });

  test('renders chart when chartData is present', () => {
    const messagesWithChart = [
      {
        id: '1',
        type: 'assistant',
        content: 'Here is your chart',
        chartData: {
          plotly_json: JSON.stringify({
            data: [{ y: [1, 2, 3], type: 'scatter' }],
            layout: { title: 'Test Chart' }
          })
        },
        timestamp: new Date()
      }
    ];

    render(<ChatInterface {...mockProps} messages={messagesWithChart} />);
    
    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument();
  });
});