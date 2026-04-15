import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './App.css'

function MarkdownContent({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ children, className }) {
          const language = /language-(\w+)/.exec(className || '')?.[1]
          return language ? (
            <SyntaxHighlighter language={language} style={oneDark} PreTag="div">
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className="inline-code">{children}</code>
          )
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

const EXAMPLES = [
  'Explain how the attention mechanism in transformers works',
  'Write a Python function to detect palindromes',
  'What are some tips for learning a new language quickly?',
  'Summarise the plot of Dune in three sentences',
]

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [copiedIdx, setCopiedIdx] = useState(null)

  const copyMessage = useCallback((content, idx) => {
    navigator.clipboard.writeText(content)
    setCopiedIdx(idx)
    setTimeout(() => setCopiedIdx(null), 2000)
  }, [])
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async (overrideText) => {
    const text = (overrideText ?? input).trim()
    if (!text || isStreaming) return

    const userMsg = { role: 'user', content: text }
    const history = [...messages, userMsg]

    setMessages([...history, { role: 'assistant', content: '' }])
    setInput('')
    setIsStreaming(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
        signal: controller.signal,
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') break
          try {
            const { token, error } = JSON.parse(data)
            if (token !== undefined) {
              setMessages(prev => {
                const next = [...prev]
                const last = next[next.length - 1]
                next[next.length - 1] = { ...last, content: last.content + token }
                return next
              })
            }
            if (error) {
              setMessages(prev => {
                const next = [...prev]
                next[next.length - 1] = { ...next[next.length - 1], content: `Error: ${error}` }
                return next
              })
            }
          } catch { /* ignore malformed chunk */ }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages(prev => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant' && last.content === '') {
            next[next.length - 1] = { ...last, content: 'Could not reach the server.' }
          }
          return next
        })
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
      textareaRef.current?.focus()
    }
  }, [input, messages, isStreaming])

  const stopGeneration = () => abortRef.current?.abort()

  const clearChat = () => {
    abortRef.current?.abort()
    setMessages([])
    setInput('')
    setTimeout(() => textareaRef.current?.focus(), 0)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px'
  }

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <div className="header-logo">G</div>
          <div>
            <span className="header-title">Gemma 4 E2B-it</span>
            <span className="header-badge">4-bit · MLX · local</span>
          </div>
        </div>
        <button className="new-chat-btn" onClick={clearChat}>New chat</button>
      </header>

      {/* ── Messages ── */}
      <div className="messages-container">
        <div className="messages">

          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-logo">G</div>
              <h2 className="empty-heading">How can I help you?</h2>
              <p className="empty-sub">Running privately on your Mac — nothing leaves your device</p>
              <div className="examples">
                {EXAMPLES.map(ex => (
                  <button key={ex} className="example-card" onClick={() => sendMessage(ex)}>
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => {
            const isLast = i === messages.length - 1

            if (msg.role === 'user') {
              return (
                <div key={i} className="message user">
                  <div className="bubble user-bubble">{msg.content}</div>
                </div>
              )
            }

            return (
              <div key={i} className="message assistant">
                <div className="avatar assistant-avatar">G</div>
                <div className="assistant-body">
                  <div className={`bubble assistant-bubble${msg.content ? '' : ' compact'}`}>
                    {msg.content
                      ? <MarkdownContent content={msg.content} />
                      : <span className="placeholder-dots"><span/><span/><span/></span>}
                    {isStreaming && isLast && msg.content && <span className="cursor" />}
                  </div>
                  {!isStreaming && msg.content && (
                    <button
                      className={`copy-btn ${copiedIdx === i ? 'copied' : ''}`}
                      onClick={() => copyMessage(msg.content, i)}
                      title="Copy response"
                    >
                      {copiedIdx === i ? (
                        <>
                          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="2,8 6,12 14,4" />
                          </svg>
                          Copied
                        </>
                      ) : (
                        <>
                          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <rect x="5" y="5" width="9" height="9" rx="1.5" />
                            <path d="M11 5V3.5A1.5 1.5 0 0 0 9.5 2h-6A1.5 1.5 0 0 0 2 3.5v6A1.5 1.5 0 0 0 3.5 11H5" />
                          </svg>
                          Copy
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )
          })}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Input bar ── */}
      <div className="input-bar">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Message Gemma…"
            rows={1}
            disabled={isStreaming}
            autoFocus
          />
          {isStreaming ? (
            <button className="btn stop-btn" onClick={stopGeneration}>
              <span className="stop-icon" /> Stop
            </button>
          ) : (
            <button className="btn send-btn" onClick={() => sendMessage()} disabled={!input.trim()}>
              Send
            </button>
          )}
        </div>
        <p className="input-hint">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  )
}
