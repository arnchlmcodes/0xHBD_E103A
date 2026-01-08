
import { useState, useEffect } from 'react'
import axios from 'axios'
import { Upload, FileText, Check, Play, BookOpen, Brain, Clock, Activity, Download, ChevronRight, X, AlertCircle, Video, MessageSquare, Send } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = 'http://localhost:8000'

// --- SUB COMPONENTS ---

const Header = ({ systemOnline }) => (
  <div className="fixed top-0 w-full glass-panel z-50 px-6 py-4 flex justify-between items-center rounded-none border-t-0 border-x-0">
    <div>
      <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-600 to-blue-600" style={{ background: 'linear-gradient(to right, #14bf96, #3498db)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        Teaching Assistant
      </h1>
      <p className="text-xs text-slate-500">AI-Powered Curriculum Content Generator</p>
    </div>
    <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
      <div className={`status-dot-active ${!systemOnline && '!bg-red-500 !animate-none'}`}></div>
      <span className="text-xs font-semibold text-slate-600">{systemOnline ? 'System Online' : 'Backend Offline'}</span>
    </div>
  </div>
)

const LandingView = ({ isProcessing, handleUpload, files, setSelectedFile, setPhase }) => (
  <div className="pt-24 min-h-screen flex items-center justify-center p-6">
    <div className="app-grid w-full">
      {/* Upload Card */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-8 flex flex-col items-center justify-center text-center min-h-[400px]">
        <div className={`relative w-full h-full border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center p-6 transition-all ${isProcessing ? 'bg-slate-50' : 'hover:border-teal-400 hover:bg-slate-50'}`}>
          {isProcessing ? (
            <div className="flex flex-col items-center">
              <div className="loader-spinner mb-4"></div>
              <h3 className="text-lg font-semibold text-slate-700">Processing Document...</h3>
              <p className="text-sm text-slate-500">Extracting curriculum hierarchy</p>
            </div>
          ) : (
            <>
              <div className="w-16 h-16 bg-teal-50 text-teal-500 rounded-full flex items-center justify-center mb-4">
                <Upload size={32} />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-slate-700">Upload Curriculum PDF</h3>
              <p className="text-slate-500 mb-6 max-w-xs">Drag and drop your NCERT chapter or textbook directory here.</p>
              <input type="file" onChange={handleUpload} className="hidden" id="file-upload" />
              <label htmlFor="file-upload" className="btn-primary">
                Choose File
              </label>
            </>
          )}
        </div>
      </motion.div>

      {/* Recent Files */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-col gap-4">
        <h2 className="text-xl font-bold text-slate-700">Quick Access</h2>
        <div className="grid gap-3">
          {files.length === 0 ? (
            <div className="glass-panel p-6 text-center text-slate-400">No processed files yet.</div>
          ) : (
            files.map((f, i) => (
              <div key={i} onClick={() => { setSelectedFile(f); setPhase('dashboard'); }} className="glass-panel p-4 flex items-center gap-4 cursor-pointer hover:bg-white/50">
                <div className="w-10 h-10 bg-blue-50 text-blue-500 rounded-lg flex items-center justify-center">
                  <FileText size={20} />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-700">{f.topics && f.topics.length > 0 ? f.topics[0] : f.filename}</h4>
                  <span className="text-xs text-slate-500">{f.topics.length} topics extracted</span>
                </div>
                <ChevronRight size={16} className="text-slate-400" />
              </div>
            ))
          )}
        </div>
      </motion.div>
    </div>
  </div>
)

const TypeCard = ({ icon, title, desc, id, selected, onSelect }) => (
  <div
    onClick={() => onSelect(id)}
    className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${selected === id ? 'border-teal-400 bg-teal-50/50 shadow-md' : 'border-slate-100 hover:border-teal-200 bg-white'}`}
  >
    <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${selected === id ? 'bg-teal-100 text-teal-600' : 'bg-slate-100 text-slate-500'}`}>
      {icon}
    </div>
    <h3 className="font-bold text-slate-800 mb-1">{title}</h3>
    <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
  </div>
)

const DashboardView = ({ setPhase, selectedFile, selectedTopicIndex, setSelectedTopicIndex, selectedType, setSelectedType, handleGenerate }) => (
  <div className="pt-24 px-6 max-w-6xl mx-auto pb-20">
    <button onClick={() => setPhase('landing')} className="mb-6 text-slate-500 hover:text-teal-600 flex items-center gap-1 text-sm font-medium">← Back to Upload</button>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      {/* Configuration Sidebar */}
      <div className="md:col-span-1 space-y-6">
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="glass-panel p-6">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Active Document</h3>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-teal-100 text-teal-600 rounded-lg flex items-center justify-center">
              <FileText size={20} />
            </div>
            <div className="overflow-hidden">
              <div className="font-bold text-slate-700 truncate">{selectedFile?.topics && selectedFile.topics.length > 0 ? selectedFile.topics[0] : selectedFile?.filename}</div>
              <div className="text-xs text-slate-500">{selectedFile?.topic_count} topics available</div>
            </div>
          </div>

          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Select Topic</h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
            {selectedFile?.topics.map((topic, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedTopicIndex(idx)}
                className={`p-3 rounded-lg cursor-pointer transition-all border ${selectedTopicIndex === idx ? 'bg-teal-50 border-teal-200 text-teal-700 shadow-sm' : 'hover:bg-white border-transparent text-slate-600'}`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${selectedTopicIndex === idx ? 'bg-teal-500' : 'bg-slate-300'}`}></span>
                  <span className="text-sm font-medium">{topic}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Main Action Area */}
      <div className="md:col-span-2 space-y-6">
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel p-8">
          <h2 className="text-2xl font-bold text-slate-800 mb-2">What would you like to generate?</h2>
          <p className="text-slate-500 mb-8">Select a content type to generate AI-powered materials for the selected topic.</p>

          <div className="grid grid-cols-2 gap-4">
            <TypeCard
              icon={<BookOpen size={24} />}
              title="Teaching Plan"
              desc="Step-by-step lesson plan with objectives & timing."
              id="plan"
              selected={selectedType}
              onSelect={setSelectedType}
            />
            <TypeCard
              icon={<Activity size={24} />}
              title="Quiz"
              desc="Multiple choice & short answer questions."
              id="quiz"
              selected={selectedType}
              onSelect={setSelectedType}
            />
            <TypeCard
              icon={<Brain size={24} />}
              title="Practice Exercises"
              desc="Homework problems and application questions."
              id="practice"
              selected={selectedType}
              onSelect={setSelectedType}
            />
            <TypeCard
              icon={<Clock size={24} />}
              title="Flashcards"
              desc="Smart concept review cards."
              id="flashcards"
              selected={selectedType}
              onSelect={setSelectedType}
            />
            <TypeCard
              icon={<Video size={24} />}
              title="Video Lesson"
              desc="AI-generated animated video lesson (Landscape)"
              id="video"
              selected={selectedType}
              onSelect={setSelectedType}
            />
          </div>

          <div className="mt-8 flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={!selectedType}
              className={`btn-primary text-lg px-8 py-3 ${!selectedType && 'opacity-50 cursor-not-allowed'}`}
            >
              Generate Content &nbsp; ✨
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  </div>
)

const GeneratingView = ({ processingText }) => (
  <div className="fixed inset-0 bg-white/80 backdrop-blur-md z-50 flex flex-col items-center justify-center">
    <div className="loader-spinner mb-8"></div>
    <h2 className="text-2xl font-bold text-slate-800 mb-2">Generating Content...</h2>
    <p className="text-slate-500">{processingText || "Consulting AI models and formatting your document"}</p>

    <div className="mt-8 text-sm text-slate-400 flex flex-col gap-2 items-start">
      <div className="flex items-center gap-2 text-teal-600"><Check size={16} /> Extracted context</div>
      <div className="flex items-center gap-2 text-teal-600"><Check size={16} /> Verified facts</div>
      <div className="flex items-center gap-2 animate-pulse"><div className="w-4 h-4 rounded-full border-2 border-teal-500 border-t-transparent animate-spin"></div> Formatting output</div>
    </div>
  </div>
)

const ResultsView = ({ selectedType, selectedFile, selectedTopicIndex, generationResult, setPhase }) => (
  <div className="pt-24 px-6 max-w-4xl mx-auto pb-20 text-center">
    <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass-panel p-10">
      <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
        <Check size={40} />
      </div>
      <h2 className="text-3xl font-bold text-slate-800 mb-4">Content Ready!</h2>
      <p className="text-slate-500 mb-8 max-w-md mx-auto">
        Your <b>{selectedType}</b> for <i>{selectedFile?.topics[selectedTopicIndex]}</i> has been successfully generated.
      </p>

      {generationResult?.type === 'flashcards' ? (
        <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 mb-8 max-h-[400px] overflow-y-auto text-left">
          <h3 className="font-bold mb-4">Preview:</h3>
          <pre className="text-xs text-slate-600 whitespace-pre-wrap font-mono">
            {JSON.stringify(generationResult.data.data.cards, null, 2)}
          </pre>
          <button onClick={() => {
            const blob = new Blob([JSON.stringify(generationResult.data.data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `flashcards.json`;
            a.click();
          }} className="btn-primary mt-4">Download JSON</button>
        </div>
      ) : generationResult?.type === 'video' ? (
        <div className="flex flex-col items-center gap-6">
          <div className="relative rounded-xl overflow-hidden shadow-2xl border-4 border-white bg-black w-full max-w-3xl">
            <video
              controls
              autoPlay
              className="w-full h-auto block"
              src={`${API_BASE}${generationResult?.data?.file_url}`}
            >
              Your browser does not support the video tag.
            </video>
          </div>
          <a
            href={`${API_BASE}${generationResult?.data?.file_url}`}
            download
            className="flex items-center gap-2 text-slate-500 hover:text-teal-600 transition-colors"
          >
            <Download size={18} /> Download Video File
          </a>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-6">
          <div className="relative rounded-xl overflow-hidden shadow-2xl border border-slate-200 bg-slate-50 w-full max-w-4xl h-[600px]">
            <iframe
              src={`${API_BASE}${generationResult?.data?.file_url}#toolbar=0`}
              className="w-full h-full"
              title="PDF Preview"
            />
          </div>
          <a
            href={`${API_BASE}${generationResult?.data?.file_url}`}
            download
            target="_blank"
            className="flex items-center gap-2 text-slate-500 hover:text-teal-600 transition-colors"
          >
            <Download size={18} /> Download PDF File
          </a>
        </div>
      )}

      <div className="mt-12 border-t pt-6">
        <button onClick={() => setPhase('dashboard')} className="text-slate-500 hover:text-teal-600 text-sm font-medium">
          Generate Something Else
        </button>
      </div>
    </motion.div>
  </div>
)

// --- MAIN APP ---

function App() {
  const [phase, setPhase] = useState('landing')
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedTopicIndex, setSelectedTopicIndex] = useState(0)
  const [selectedType, setSelectedType] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [generationResult, setGenerationResult] = useState(null)
  const [processingText, setProcessingText] = useState(null)

  // Chat State
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your MathBuddy. Ask me anything about the uploaded curriculum!' }
  ])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)

  // Status check
  const [systemOnline, setSystemOnline] = useState(false)

  useEffect(() => {
    checkSystem()
    fetchFiles()
  }, [])

  const checkSystem = async () => {
    try {
      await axios.get(`${API_BASE}/`)
      setSystemOnline(true)
    } catch (e) {
      setSystemOnline(false)
    }
  }

  const fetchFiles = async () => {
    try {
      const res = await axios.get(`${API_BASE}/files`)
      setFiles(res.data)
    } catch (e) {
      console.error("Failed to fetch files")
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setIsProcessing(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      await axios.post(`${API_BASE}/upload`, formData)
      await fetchFiles()
      setPhase('dashboard')
    } catch (err) {
      alert("Upload failed: " + err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  // Poll for file existence
  const pollForFile = async (filename, type) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/download/${filename}`)
        if (res.status === 200) {
          clearInterval(interval)
          // Success!
          setGenerationResult({ type: type, data: { file_url: `/download/${filename}`, filename: filename } })
          setPhase('results')
          setProcessingText(null)
        }
      } catch (e) {
        // Continue polling if 404
        console.log("Polling...", filename)
      }
    }, 3000) // Check every 3 seconds
  }

  const handleGenerate = async () => {
    if (!selectedFile || !selectedType) return
    setPhase('generating')
    setProcessingText(null)

    try {
      let endpoint = ''
      switch (selectedType) {
        case 'plan': endpoint = '/generate/plan'; break;
        case 'quiz': endpoint = '/generate/quiz'; break;
        case 'practice': endpoint = '/generate/practice'; break;
        case 'flashcards': endpoint = '/generate/flashcards'; break;
        case 'video': endpoint = '/generate/video'; break;
        default: throw new Error("Unknown type");
      }
      const payload = {
        filename: selectedFile.filename,
        topic_index: selectedTopicIndex
      }

      if (selectedType === 'video') {
        setProcessingText("Generating your video... This may take up to 2-3 minutes. Please stay on this screen.")
      }

      console.log("Sending request to:", endpoint, payload)
      const res = await axios.post(`${API_BASE}${endpoint}`, payload)
      console.log("Response:", res.data)

      if (!res.data) {
        throw new Error("Empty response from server")
      }

      // Check for video type specifically OR generic processing status
      if (selectedType === 'video' || res.data.status === 'processing') {
        const fileToPoll = res.data.filename || res.data.json_file

        if (!fileToPoll) {
          console.error("No filename in response:", res.data)
          throw new Error("No filename returned for background task")
        }

        console.log("Starting polling for:", fileToPoll)
        pollForFile(fileToPoll, selectedType)
      } else {
        setGenerationResult({ type: selectedType, data: res.data })
        setPhase('results')
      }
    } catch (err) {
      console.error("Generation Error:", err)
      alert("Generation failed: " + (err.response?.data?.detail || err.message))
      setPhase('dashboard')
    }
  }

  const handleSendMessage = async () => {
    if (!currentMessage.trim()) return
    const userMsg = { role: 'user', content: currentMessage }
    setChatMessages(prev => [...prev, userMsg])
    setCurrentMessage('')
    setIsChatLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/chat`, { message: userMsg.content })
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources || []
      }])
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: "Error: Could not connect to Chatbot." }])
    } finally {
      setIsChatLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-soft">
      <Header systemOnline={systemOnline} />

      <AnimatePresence mode='wait'>
        {phase === 'landing' && (
          <LandingView
            key="landing"
            isProcessing={isProcessing}
            handleUpload={handleUpload}
            files={files}
            setSelectedFile={setSelectedFile}
            setPhase={setPhase}
          />
        )}
        {phase === 'dashboard' && (
          <DashboardView
            key="dashboard"
            setPhase={setPhase}
            selectedFile={selectedFile}
            selectedTopicIndex={selectedTopicIndex}
            setSelectedTopicIndex={setSelectedTopicIndex}
            selectedType={selectedType}
            setSelectedType={setSelectedType}
            handleGenerate={handleGenerate}
          />
        )}
        {phase === 'generating' && <GeneratingView key="loading" processingText={processingText} />}
        {phase === 'results' && (
          <ResultsView
            key="results"
            selectedType={selectedType}
            selectedFile={selectedFile}
            selectedTopicIndex={selectedTopicIndex}
            generationResult={generationResult}
            setPhase={setPhase}
          />
        )}
      </AnimatePresence>

      {/* Chat Widget */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-4">
        <AnimatePresence>
          {isChatOpen && (
            <motion.div initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 20 }} className="glass-panel w-80 h-[500px] flex flex-col shadow-2xl bg-white border border-slate-200">
              <div className="p-4 border-b flex justify-between items-center bg-teal-50 rounded-t-xl">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <h4 className="font-bold text-slate-700">MathBuddy AI</h4>
                </div>
                <button onClick={() => setIsChatOpen(false)} className="text-slate-400 hover:text-red-500"><X size={18} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-lg text-sm ${msg.role === 'user' ? 'bg-teal-500 text-white rounded-br-none' : 'bg-slate-100 text-slate-700 rounded-bl-none'}`}>
                      {msg.content}
                    </div>
                    {/* Display Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 text-[10px] text-slate-400 max-w-[85%] bg-slate-50 p-2 rounded border border-slate-100">
                        <div className="font-bold mb-1">📚 Sources:</div>
                        {msg.sources.map((s, i) => (
                          <div key={i} className="truncate">• {s.topic}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {isChatLoading && <div className="text-xs text-slate-400 pl-2">MathBuddy is thinking...</div>}
              </div>
              <div className="p-3 border-t flex gap-2">
                <input
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask a doubt..."
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-teal-400"
                />
                <button onClick={handleSendMessage} disabled={isChatLoading} className="bg-teal-500 text-white p-2 rounded-md hover:bg-teal-600 disabled:opacity-50">
                  <Send size={16} />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={() => setIsChatOpen(!isChatOpen)}
          className="w-14 h-14 bg-gradient-to-tr from-teal-500 to-blue-500 rounded-full shadow-lg flex items-center justify-center text-white hover:scale-110 transition-transform"
        >
          {isChatOpen ? <X size={24} /> : <MessageSquare size={24} />}
        </button>
      </div>
    </div>
  )
}

export default App
