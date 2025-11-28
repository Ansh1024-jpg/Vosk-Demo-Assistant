import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [status, setStatus] = useState('idle'); // idle, listening
  const [messages, setMessages] = useState([]);
  const [transcript, setTranscript] = useState('');
  const [inputValue, setInputValue] = useState('');
  const chatEndRef = useRef(null);
  const ws = useRef(null);

  const addMessage = (sender, text) => {
    setMessages(prev => [...prev, { sender, text }]);
  };

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:5000/ws');

    ws.current.onopen = () => {
      console.log('Connected to backend');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);

      switch (data.type) {
        case 'state_change':
          setStatus(data.state);
          if (data.state === 'idle') {
            setTranscript('');
          }
          break;
        case 'transcript':
          setTranscript(data.text);
          break;
        case 'assistant_question':
          addMessage('assistant', data.text);
          break;
        case 'user_answer':
          addMessage('user', data.text);
          break;
        default:
          break;
      }
    };

    ws.current.onclose = () => {
      console.log('Disconnected');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const handleSend = () => {
    if (inputValue.trim() && ws.current) {
      ws.current.send(JSON.stringify({ type: 'text_input', text: inputValue }));
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Vosk Assistant</h1>
      </header>

      <div className="main-content">
        <div className={`visualizer ${status === 'listening' ? 'active' : ''}`}>
          <div className="orb"></div>
          <div className="status-text">
            {status === 'idle' ? 'Say "Hey Assistant"' : 'Listening...'}
          </div>
          <div className="live-transcript">{transcript}</div>
        </div>

        <div className="chat-area">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="message-bubble">{msg.text}</div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Type your answer..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={status === 'idle'}
        />
        <button onClick={handleSend} disabled={status === 'idle' || !inputValue.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
