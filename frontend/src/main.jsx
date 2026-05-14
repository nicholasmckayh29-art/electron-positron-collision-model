import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { err: null }
  }

  static getDerivedStateFromError(error) {
    return { err: String(error) }
  }

  componentDidCatch(error, info) {
    console.error('React render error', error, info)
  }

  render() {
    if (this.state.err) {
      return (
        <div className="min-h-screen bg-red-950 p-6 text-white">
          <p className="font-semibold">Something went wrong</p>
          <pre className="mt-2 whitespace-pre-wrap text-sm opacity-90">{this.state.err}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </React.StrictMode>,
)
