import { useState } from 'react'
import axios from 'axios'
import { ReactFlow, Controls, Background } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import ReactDiffViewer from 'react-diff-viewer-continued'
import './App.css'

function App() {
  const [code, setCode] = useState('def hello():\n    return "world"')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('reasoning')
  const [showPRModal, setShowPRModal] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleAnalyze = async (codeOverride = null) => {
    const codeToAnalyze = typeof codeOverride === 'string' ? codeOverride : code;
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await axios.post(`${API_BASE_URL}/api/analyze`, { code: codeToAnalyze })
      setResult(res.data)
      setActiveTab('reasoning')
    } catch (err) {
      setError(err.message || 'Failed to analyze')
    }
    setLoading(false)
  }

  const loadDemo = (type) => {
    if (type === 'sql') setCode("query = 'SELECT * FROM users WHERE username = ' + user_input")
    if (type === 'eval') setCode("def run(cmd):\n    return eval(cmd)")
    if (type === 'auth') setCode("def login(username, password):\n    if password == 'admin' or True:\n        return True")
  }

  const applyPatch = () => {
    if (result?.patch_report?.patched_code) {
        const newCode = result.patch_report.patched_code;
        setCode(newCode)
        handleAnalyze(newCode) // Automatically re-analyze the patched code!
    }
  }

  // Generate ReactFlow Nodes
  const getFlowData = () => {
    if (!result || !result.attack_report || !result.attack_report.attack_paths) return { nodes: [], edges: [] }
    const paths = result.attack_report.attack_paths
    
    if (paths.length === 0) {
        return {
            nodes: [{ id: 'safe', data: { label: 'System Safe' }, position: { x: 250, y: 150 }, style: { background: 'rgba(16, 185, 129, 0.1)', color: '#065f46', border: '1px solid rgba(16,185,129,0.5)', borderRadius: '8px', padding: '10px', boxShadow: '0 4px 15px rgba(16, 185, 129, 0.15)' } }],
            edges: []
        }
    }

    const nodes = [{ id: 'src', data: { label: 'Untrusted Input' }, position: { x: 250, y: 50 }, style: { background: 'rgba(55, 65, 81, 0.1)', color: '#1f2937', border: '1px solid rgba(55,65,81,0.5)', borderRadius: '8px', padding: '10px' } }]
    const edges = []
    
    paths.forEach((p, i) => {
        const id = `node-${i}`
        const isCritical = p.severity === 'CRITICAL'
        nodes.push({ 
            id, 
            data: { label: p.attack_type }, 
            position: { x: (i * 200) + 150, y: 200 }, 
            style: { 
                background: isCritical ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)', 
                color: isCritical ? '#991b1b' : '#92400e',
                border: isCritical ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(245,158,11,0.5)',
                borderRadius: '8px',
                padding: '10px',
                boxShadow: isCritical ? '0 4px 15px rgba(239, 68, 68, 0.15)' : '0 4px 15px rgba(245, 158, 11, 0.15)'
            } 
        })
        edges.push({ id: `e-src-${id}`, source: 'src', target: id, animated: true, style: { stroke: isCritical ? '#ef4444' : '#f59e0b', strokeWidth: 2 } })
    })

    return { nodes, edges }
  }

  const { nodes, edges } = getFlowData()

  return (
    <div className="min-h-screen text-gray-900 font-sans p-4 md:p-8 relative selection:bg-indigo-500/20">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header */}
        <header className="text-center space-y-4 pt-4 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-fuchsia-600 drop-shadow-sm pb-2">
            CyberShield AI
          </h1>
          <p className="text-xl text-gray-600 font-light max-w-2xl mx-auto">
            Autonomous Security Reasoning Engine & Auto-Remediation System
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column: Input */}
          <div className="space-y-6 animate-fade-in" style={{animationDelay: '0.1s'}}>
            <div className="glass-panel p-6 flex flex-col h-full space-y-4">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center border-b border-gray-200 pb-4 gap-4">
                    <h2 className="text-2xl font-bold flex items-center text-gray-800">
                        <span className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center mr-3 border border-indigo-500/20 text-indigo-600">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                        </span>
                        Target Code
                    </h2>
                </div>
                
                <textarea
                  className="glass-input w-full flex-1 min-h-[350px] p-5 font-mono text-sm text-gray-800 resize-none leading-relaxed"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  spellCheck="false"
                  placeholder="Paste your vulnerable Python code here..."
                />
                
                <button
                  onClick={() => handleAnalyze()}
                  disabled={loading}
                  className={`btn-primary w-full py-4 text-lg tracking-wide ${loading ? 'animate-pulse-glow' : ''}`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Running Reasoning Agents...
                    </span>
                  ) : 'Analyze Risk Severity'}
                </button>
                
                {error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-start">
                    <svg className="w-5 h-5 mr-3 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span>{error}</span>
                  </div>
                )}
            </div>
          </div>

          {/* Right Column: Output */}
          <div className="space-y-6">
            {loading ? (
                <div className="glass-panel h-full min-h-[500px] flex flex-col items-center justify-center p-8 text-center bg-indigo-50/50">
                    <div className="relative w-24 h-24 mb-8">
                        <div className="absolute inset-0 border-4 border-indigo-200 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
                        <div className="absolute inset-0 flex items-center justify-center text-indigo-600 font-bold">AI</div>
                    </div>
                    <h3 className="text-2xl font-bold text-indigo-900 mb-3 animate-pulse">Analyzing Code Posture...</h3>
                    <p className="text-indigo-700 max-w-sm leading-relaxed text-sm">
                        CyberShield AI is currently parsing the syntax tree, engaging the Multi-Agent framework, and verifying deterministic fallbacks...
                    </p>
                </div>
            ) : !result ? (
                <div className="glass-panel h-full min-h-[500px] flex flex-col items-center justify-center text-gray-400 p-8 text-center animate-fade-in" style={{animationDelay: '0.2s'}}>
                    <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mb-6 border border-gray-200 shadow-inner">
                        <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                    </div>
                    <h3 className="text-xl font-bold text-gray-500 mb-2">Awaiting Code Submission</h3>
                    <p className="max-w-xs leading-relaxed text-sm text-gray-400">Submit code to engage the Critic and Patch Agents for automated analysis and remediation.</p>
                </div>
            ) : (
              <div className="space-y-6 animate-fade-in">
                
                {/* Header with Results and Action Buttons */}
                <div className="flex flex-col sm:flex-row justify-between items-center bg-white/80 backdrop-blur-md border border-gray-200 rounded-2xl p-4 shadow-sm">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4 sm:mb-0">Analysis Results</h2>
                    <div className="flex space-x-3">
                        <button 
                            onClick={() => setShowPRModal(true)} 
                            className="px-4 py-2 bg-gray-800 hover:bg-gray-900 rounded-lg text-white text-sm font-bold shadow-md transition-all duration-300 flex items-center group">
                            <span className="mr-2 group-hover:scale-110 transition-transform">📦</span> 
                            GitHub PR
                        </button>
                        <a 
                            href={`${API_BASE_URL}/api/download/pdf`}
                            download 
                            target="_blank" 
                            rel="noreferrer" 
                            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 rounded-lg text-white text-sm font-bold shadow-md transition-all duration-300 flex items-center group">
                            <span className="mr-2 group-hover:scale-110 transition-transform">📄</span> 
                            PDF Report
                        </a>
                    </div>
                </div>

                {/* Score Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="glass-panel p-6 flex flex-col items-center justify-center relative overflow-hidden">
                    <div className={`absolute inset-0 opacity-[0.03] ${result.risk_score > 70 ? 'bg-red-500' : result.risk_score > 30 ? 'bg-yellow-500' : 'bg-emerald-500'}`}></div>
                    <div className="text-sm text-gray-500 font-bold uppercase tracking-widest mb-2 z-10">Risk Score</div>
                    <div className={`text-5xl font-black z-10 ${result.risk_score > 70 ? 'text-red-600' : result.risk_score > 30 ? 'text-yellow-600' : 'text-emerald-600'}`}>
                      {result.risk_score}
                    </div>
                  </div>
                  
                  <div className="glass-panel p-6 flex flex-col items-center justify-center relative overflow-hidden">
                    <div className={`absolute inset-0 opacity-[0.03] ${result.verdict === 'BLOCK' ? 'bg-red-500' : result.verdict === 'WARN' ? 'bg-yellow-500' : 'bg-emerald-500'}`}></div>
                    <div className="text-sm text-gray-500 font-bold uppercase tracking-widest mb-2 z-10">AI Verdict</div>
                    <div className={`text-3xl font-black mt-2 z-10 ${result.verdict === 'BLOCK' ? 'text-red-600' : result.verdict === 'WARN' ? 'text-yellow-600' : 'text-emerald-600'}`}>
                      {result.verdict}
                    </div>
                  </div>

                  <div className="glass-panel p-6 flex flex-col items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 opacity-[0.03] bg-blue-500"></div>
                    <div className="text-xs md:text-sm text-gray-500 font-bold uppercase tracking-widest mb-2 z-10 text-center">Detect Conf.</div>
                    <div className="text-3xl font-black mt-2 z-10 text-blue-600">
                      {result.detection_confidence || 95}%
                    </div>
                  </div>

                  <div className="glass-panel p-6 flex flex-col items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 opacity-[0.03] bg-indigo-500"></div>
                    <div className="text-xs md:text-sm text-gray-500 font-bold uppercase tracking-widest mb-2 z-10 text-center">Patch Conf.</div>
                    <div className="text-3xl font-black mt-2 z-10 text-indigo-600">
                      {result.patch_confidence || 85}%
                    </div>
                  </div>
                </div>

                {/* Tabs & Main Display */}
                <div className="glass-panel overflow-hidden flex flex-col h-[500px]">
                  <div className="flex border-b border-gray-200 bg-gray-50/50">
                    <button 
                        onClick={() => setActiveTab('reasoning')} 
                        className={`flex-1 py-4 text-sm font-bold tracking-wide transition-all ${activeTab === 'reasoning' ? 'text-indigo-600 bg-white border-b-2 border-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'}`}>
                        Reasoning
                    </button>
                    <button 
                        onClick={() => setActiveTab('graph')} 
                        className={`flex-1 py-4 text-sm font-bold tracking-wide transition-all ${activeTab === 'graph' ? 'text-fuchsia-600 bg-white border-b-2 border-fuchsia-600 shadow-sm' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'}`}>
                        Attack Graph
                    </button>
                    <button 
                        onClick={() => setActiveTab('diff')} 
                        className={`flex-1 py-4 text-sm font-bold tracking-wide transition-all ${activeTab === 'diff' ? 'text-emerald-600 bg-white border-b-2 border-emerald-600 shadow-sm' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'}`}>
                        Auto-Heal Diff
                    </button>
                  </div>

                  <div className="p-0 flex-1 overflow-auto bg-white/50 relative">
                    {activeTab === 'reasoning' && (
                        <div className="p-6 h-full overflow-y-auto space-y-6">
                            
                            {/* RAG Context Widget */}
                            {result.rag_report?.rag_context?.length > 0 && (
                                <div className="bg-blue-50/50 border border-blue-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                                    <h4 className="text-blue-800 font-bold mb-3 flex items-center">
                                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                                        Enterprise Knowledge Base (RAG)
                                    </h4>
                                    <div className="space-y-3">
                                        {result.rag_report.rag_context.map((ctx, idx) => (
                                            <div key={idx} className="bg-white p-3 rounded-lg border border-blue-100 text-sm text-gray-700 shadow-sm leading-relaxed">
                                                {ctx}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Memory Widget */}
                            {result.memory_report?.matched_patterns?.length > 0 && (
                                <div className="bg-purple-50/50 border border-purple-200 rounded-xl p-5 shadow-sm relative overflow-hidden">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-purple-500"></div>
                                    <h4 className="text-purple-800 font-bold mb-3 flex items-center">
                                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg>
                                        Historical Scans (Cosmos DB)
                                    </h4>
                                    <div className="space-y-3">
                                        {result.memory_report.matched_patterns.map((hit, idx) => (
                                            <div key={idx} className="bg-white p-3 rounded-lg border border-purple-100 text-sm shadow-sm flex flex-col sm:flex-row justify-between sm:items-center">
                                                <span className="font-semibold text-gray-800">{hit.pattern || hit}</span>
                                                {hit.historical_occurrences && (
                                                    <span className="mt-2 sm:mt-0 px-3 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full">
                                                        Detected {hit.historical_occurrences} times previously
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Raw Reasoning Log */}
                            <div className="mt-4 pt-4 border-t border-gray-100">
                                <h4 className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-3">Raw Engine Reasoning</h4>
                                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    {result.reasoning}
                                </pre>
                            </div>
                        </div>
                    )}
                    {activeTab === 'graph' && (
                        <div className="w-full h-full bg-white">
                            <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.5} maxZoom={1.5}>
                                <Background color="#e5e7eb" gap={20} size={1} />
                                <Controls className="bg-white border-gray-200 fill-gray-700" />
                            </ReactFlow>
                        </div>
                    )}
                    {activeTab === 'diff' && (
                        <div className="flex flex-col h-full">
                            <div className="flex-1 overflow-auto bg-white">
                                <ReactDiffViewer 
                                    oldValue={code} 
                                    newValue={result.patch_report?.patched_code || code} 
                                    splitView={true} 
                                    useDarkTheme={false} 
                                    leftTitle="Original (Vulnerable)"
                                    rightTitle="Patched (Secure)"
                                />
                            </div>
                            <div className="p-4 bg-gray-50 border-t border-gray-200">
                                <button 
                                    onClick={applyPatch}
                                    className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-xl shadow-md transition-all duration-300 hover:shadow-emerald-500/40 hover:-translate-y-0.5 flex items-center justify-center">
                                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                    Apply Auto-Heal Patch to Editor
                                </button>
                            </div>
                        </div>
                    )}
                  </div>
                </div>

              </div>
            )}
          </div>
        </main>
      </div>

      {/* GitHub PR Modal (Light Mode) */}
      {showPRModal && result && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-sm p-4 animate-fade-in">
            <div className="glass-panel w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh] border border-gray-300 shadow-[0_20px_50px_rgba(0,0,0,0.15)] bg-white">
                <div className="bg-gray-50 border-b border-gray-200 p-5 flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <div className="bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold px-3 py-1.5 rounded-full flex items-center shadow-sm">
                            <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 16 16"><path fillRule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.25 2.25 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.25 2.25 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"></path></svg>
                            Open
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 tracking-wide">🛡️ Auto-Heal: Mitigate Critical Vulnerabilities</h3>
                    </div>
                    <button onClick={() => setShowPRModal(false)} className="text-gray-500 hover:text-gray-800 transition-colors bg-gray-100 hover:bg-gray-200 p-2 rounded-full">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                
                <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-white">
                    <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-600 flex items-center justify-center font-bold text-white shadow-md shrink-0">
                            AI
                        </div>
                        <div className="flex-1 bg-gray-50 border border-gray-200 rounded-xl p-5 relative before:absolute before:right-full before:top-5 before:border-y-8 before:border-r-8 before:border-y-transparent before:border-r-gray-200 shadow-sm">
                            <div className="text-sm text-gray-500 mb-4 border-b border-gray-200 pb-3 flex items-center">
                                <strong className="text-gray-900 text-base mr-2">CyberShield AI</strong> <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded text-xs mr-2 border border-indigo-200">bot</span> commented just now
                            </div>
                            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 leading-relaxed">
                                {result.security_pr?.summary || "No PR summary available."}
                            </pre>
                        </div>
                    </div>
                </div>
                
                <div className="bg-gray-50 border-t border-gray-200 p-5 flex justify-end space-x-4">
                    <button onClick={() => setShowPRModal(false)} className="px-5 py-2.5 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg text-sm font-bold text-gray-700 transition-colors shadow-sm">Cancel</button>
                    <button onClick={() => { applyPatch(); setShowPRModal(false); }} className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-bold shadow-md transition-all">Merge Pull Request</button>
                </div>
            </div>
        </div>
      )}

    </div>
  )
}

export default App
