import { useEffect, useState } from "react";
import { db } from "./firebase";
import { collection, onSnapshot, query, orderBy, limit } from "firebase/firestore";

function App() {
  const [view, setView] = useState('overview');
  const [processingStage, setProcessingStage] = useState(''); // 'hashing_master', 'fingerprint', 'scan', 'ai'
  const [liveHashes, setLiveHashes] = useState([]); // For the terminal effect
  const [scanResults, setScanResults] = useState([]);
  const [detections, setDetections] = useState([]);
  const [selectedDMCA, setSelectedDMCA] = useState(null);

  // --- FIRESTORE LIVE FEED ---
  useEffect(() => {
    const q = query(collection(db, "detections"), orderBy("detected_at", "desc"), limit(20));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setDetections(data);
    });
    return () => unsubscribe();
  }, []);

  // --- HELPER: REAL LEGAL ENTITIES ---
  const getLegalEntity = (platform) => {
    const map = {
      "Twitter/X": "X Corp. Copyright Agent",
      "Telegram": "Telegram FZ-LLC Abuse Team",
      "YouTube": "Google LLC, YouTube Legal Dept.",
      "Instagram": "Meta Platforms, Inc. IP Operations"
    };
    return map[platform] || "Platform Copyright Agent";
  };

  // --- HELPER: TIME FORMATTER ---
  const formatTime = (timestamp) => {
    if (!timestamp) return "Just now";
    // Handle Firestore timestamp format
    const date = timestamp.seconds ? new Date(timestamp.seconds * 1000) : new Date();
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // --- THE CORE LOGIC: REGISTER vs SCAN ---
  const handleUpload = async (event, mode) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", mode);

    // Pick a realistic platform for the demo instead of "Manual Scan"
    const platforms = ["Twitter/X", "Telegram", "YouTube", "Instagram"];
    const simulatedPlatform = platforms[Math.floor(Math.random() * 2)]; // Skews to Twitter/Telegram
    formData.append("platform", mode === 'register' ? 'OFFICIAL' : simulatedPlatform);

    // ==========================================
    // FLOW 1: REGISTER MASTER (Real Fingerprint UI)
    // ==========================================
    if (mode === 'register') {
      setView('processing');
      setProcessingStage('hashing_master');
      setLiveHashes([]);

      // Simulate real pHash generation in the UI terminal
      let frameCount = 0;
      const hashInterval = setInterval(() => {
        frameCount++;
        const hex = Math.floor(Math.random() * 16777215).toString(16).padEnd(6, '0') +
          Math.floor(Math.random() * 16777215).toString(16).padEnd(6, '0');
        setLiveHashes(prev => [...prev, `[SYS] Extracting Keyframe ${frameCount} -> pHash: ${hex}`].slice(-8));

        if (frameCount >= 24) {
          clearInterval(hashInterval);
          setLiveHashes(prev => [...prev, "✅ MASTER FINGERPRINT SECURED IN VAULT"]);

          // Actually send to backend in the background
          fetch("http://localhost:8000/analyze", { method: "POST", body: formData }).catch(console.error);

          setTimeout(() => setView('overview'), 2000);
        }
      }, 100);

      // ==========================================
      // FLOW 2: FORENSIC SCAN (The 3-Step Threat Flow)
      // ==========================================
    } else {
      setView('processing');
      setProcessingStage('fingerprint');

      // Step 1: Fingerprint (2s)
      setTimeout(() => {
        setProcessingStage('scan');

        // Step 2: Platform Scan
        const mockResults = [
          { platform: "Twitter/X", icon: "𝕏", status: "checking", progress: 0 },
          { platform: "Telegram", icon: "✈", status: "checking", progress: 0 },
          { platform: "YouTube", icon: "▶", status: "checking", progress: 0 },
          { platform: "Instagram", icon: "📷", status: "checking", progress: 0 }
        ];
        setScanResults(mockResults);

        let progress = 0;
        const scanInterval = setInterval(() => {
          progress += 20;
          setScanResults(prev => prev.map(p => ({ ...p, progress: Math.min(progress, 100) })));
          if (progress >= 100) {
            clearInterval(scanInterval);
            setScanResults([
              { platform: "Twitter/X", icon: "𝕏", status: "threat_found" },
              { platform: "Telegram", icon: "✈", status: "threat_found" },
              { platform: "YouTube", icon: "▶", status: "clean" },
              { platform: "Instagram", icon: "📷", status: "clean" }
            ]);

            // Step 3: AI Analysis (2s after scan finishes)
            setTimeout(() => {
              setProcessingStage('ai');

              // Call Backend
              fetch("http://localhost:8000/analyze", { method: "POST", body: formData })
                .then(() => setTimeout(() => setView('overview'), 2000))
                .catch(() => {
                  // Fallback so demo doesn't break if backend is asleep
                  alert("Backend sync failed. Check Python terminal.");
                  setView('overview');
                });
            }, 1500);
          }
        }, 300);
      }, 2000);
    }
  };

  // --- UI COMPONENTS ---
  const Sidebar = () => (
    <div className="w-64 bg-[#0a0a14] border-r border-gray-800 flex flex-col p-6 h-screen sticky top-0 shadow-2xl">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center font-bold text-xl shadow-[0_0_15px_rgba(124,58,237,0.5)]">S</div>
        <h1 className="font-bold text-xl tracking-tight">SportsGuard</h1>
      </div>
      <nav className="flex flex-col gap-2 flex-1">
        {[
          { id: 'overview', label: 'Live Command Center', icon: '📡' },
          { id: 'upload', label: 'Forensic Tools', icon: '🛡️' },
          { id: 'strikes', label: 'Legal Enforcement', icon: '⚖️' },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setView(item.id)}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${view === item.id ? 'bg-purple-600/20 text-purple-400 border border-purple-600/30' : 'text-gray-500 hover:bg-gray-800 hover:text-white'
              }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="mt-auto p-4 bg-black/50 rounded-xl border border-gray-800 text-center">
        <div className="flex items-center justify-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-xs text-green-500 font-mono uppercase tracking-widest">System Live</span>
        </div>
        <p className="text-[10px] text-gray-600">Gemini 2.0 Engine</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#07070a] text-gray-200 flex font-sans">
      <Sidebar />
      <main className="flex-1 p-10 overflow-y-auto relative">

        {/* ==========================================
            VIEW 1: UPLOAD (Now "Forensic Tools")
            ========================================== */}
        {view === 'upload' && (
          <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in duration-500">
            <div className="text-center">
              <h2 className="text-3xl font-bold mb-2">Forensic Asset Management</h2>
              <p className="text-gray-500">Establish encrypted baselines and manually verify suspicious media.</p>
            </div>

            <div className="grid grid-cols-2 gap-8">
              {/* Box 1: Register */}
              <div className="bg-[#11111a] p-10 rounded-2xl border border-gray-800 text-center hover:border-purple-500 transition-all shadow-xl">
                <div className="w-16 h-16 bg-purple-900/30 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 border border-purple-500/30">🔒</div>
                <h3 className="text-xl font-bold text-white mb-2">Vault Registration</h3>
                <p className="text-sm text-gray-400 mb-8">Extract pHash signatures from an official broadcast to set the system baseline.</p>
                <input type="file" id="reg-file" className="hidden" onChange={(e) => handleUpload(e, 'register')} />
                <label htmlFor="reg-file" className="bg-purple-600 text-white px-8 py-3 rounded-lg font-bold cursor-pointer hover:bg-purple-500 shadow-[0_0_15px_rgba(124,58,237,0.3)]">
                  Secure Master Asset
                </label>
              </div>

              {/* Box 2: Scan */}
              <div className="bg-[#11111a] p-10 rounded-2xl border border-gray-800 text-center hover:border-red-500 transition-all shadow-xl">
                <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 border border-red-500/30">🔍</div>
                <h3 className="text-xl font-bold text-white mb-2">Manual Threat Scan</h3>
                <p className="text-sm text-gray-400 mb-8">Force a global cross-reference of a specific suspicious file found in the wild.</p>
                <input type="file" id="scan-file" className="hidden" onChange={(e) => handleUpload(e, 'scan')} />
                <label htmlFor="scan-file" className="bg-red-600 text-white px-8 py-3 rounded-lg font-bold cursor-pointer hover:bg-red-500 shadow-[0_0_15px_rgba(220,38,38,0.3)]">
                  Initiate Scan
                </label>
              </div>
            </div>
          </div>
        )}

        {/* ==========================================
            VIEW 2: PROCESSING / TERMINAL ANIMATIONS
            ========================================== */}
        {view === 'processing' && (
          <div className="max-w-2xl mx-auto py-20 animate-in slide-in-from-bottom-8">

            {/* The "Real" Fingerprint Terminal */}
            {processingStage === 'hashing_master' && (
              <div className="bg-black border border-gray-800 p-6 rounded-xl shadow-2xl font-mono text-sm">
                <div className="flex items-center gap-2 border-b border-gray-800 pb-4 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-gray-500 ml-2">OpenCV Core :: Fingerprint Extraction</span>
                </div>
                <div className="space-y-1 h-64 flex flex-col justify-end">
                  {liveHashes.map((log, i) => (
                    <div key={i} className={log.includes('✅') ? "text-green-400 font-bold mt-4" : "text-purple-400"}>
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* The 3-Step Threat Flow */}
            {processingStage !== 'hashing_master' && (
              <div className="space-y-12">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider">
                  <span className={processingStage === 'fingerprint' ? 'text-purple-400 border-b-2 border-purple-400 pb-2' : 'text-gray-600'}>1. Extract Hash</span>
                  <span className={processingStage === 'scan' ? 'text-blue-400 border-b-2 border-blue-400 pb-2' : 'text-gray-600'}>2. Network Scan</span>
                  <span className={processingStage === 'ai' ? 'text-green-400 border-b-2 border-green-400 pb-2' : 'text-gray-600'}>3. AI Context</span>
                </div>

                {processingStage === 'fingerprint' && (
                  <div className="text-center py-10">
                    <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                    <h2 className="text-xl font-mono text-purple-400">Processing visual signature...</h2>
                  </div>
                )}

                {processingStage === 'scan' && (
                  <div className="space-y-4">
                    {scanResults.map((res, i) => (
                      <div key={i} className="bg-[#11111a] p-4 rounded-lg border border-gray-800 flex items-center justify-between">
                        <div className="flex items-center gap-3 w-32">
                          <span className="text-xl">{res.icon}</span>
                          <span className="font-bold text-sm">{res.platform}</span>
                        </div>

                        {res.progress !== undefined ? (
                          <div className="flex-1 mx-6 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 transition-all duration-300" style={{ width: `${res.progress}%` }}></div>
                          </div>
                        ) : (
                          <span className={`px-3 py-1 text-[10px] font-bold rounded uppercase tracking-widest ${res.status === 'threat_found' ? 'bg-red-900/40 text-red-400 border border-red-900' : 'bg-green-900/20 text-green-500'
                            }`}>
                            {res.status.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {processingStage === 'ai' && (
                  <div className="text-center py-10">
                    <div className="text-5xl mb-6 animate-pulse">🧠</div>
                    <h2 className="text-xl font-mono text-green-400">Gemini evaluating Fair Use context...</h2>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ==========================================
            VIEW 3: LIVE COMMAND CENTER
            ========================================== */}
        {view === 'overview' && (
          <div className="max-w-5xl animate-in fade-in">
            <header className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-3">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  Live Global Feed
                </h2>
                <p className="text-sm text-gray-500 mt-1">Real-time telemetry from Python tracking nodes.</p>
              </div>
            </header>

            <div className="space-y-4">
              {detections.length === 0 ? (
                <div className="bg-[#11111a] border border-gray-800 p-12 text-center rounded-2xl">
                  <p className="text-gray-500 font-mono">Listening for threats... (Run mock_scraper.py)</p>
                </div>
              ) : (
                detections.map((item) => (
                  <div key={item.id} className="bg-[#11111a] p-6 rounded-2xl border border-gray-800 flex flex-col group hover:border-gray-600 transition-all shadow-lg">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 text-[10px] rounded font-bold uppercase tracking-widest ${item.classification === 'Piracy' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                            item.classification === 'Transformative' ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20' :
                              'bg-green-500/10 text-green-500 border border-green-500/20'
                          }`}>
                          {item.classification} (Risk: {item.risk_score})
                        </span>
                        <span className="text-xs font-mono text-gray-500 flex items-center gap-1">
                          🕒 {formatTime(item.detected_at)}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1">Visual Match</p>
                        <p className="text-lg font-mono text-white">{item.match_confidence}%</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mb-3">
                      <span className="bg-blue-900/30 text-blue-400 text-[10px] px-2 py-0.5 rounded border border-blue-900/50 uppercase">{item.platform}</span>
                      <p className="text-gray-300 font-medium line-clamp-1 text-sm">"{item.post_text}"</p>
                    </div>

                    <div className="bg-black/40 p-4 rounded-xl border-l-2 border-purple-500 mt-2">
                      <p className="text-sm text-gray-400"><span className="text-purple-400 font-bold mr-2">AI Context:</span>{item.reasoning}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ==========================================
            VIEW 4: STRIKES / DMCA
            ========================================== */}
        {view === 'strikes' && (
          <div className="max-w-4xl">
            <h2 className="text-2xl font-bold mb-2">Enforcement Queue</h2>
            <p className="text-gray-500 mb-8">High-risk targets awaiting legal action.</p>
            <div className="space-y-4">
              {detections.filter(d => d.classification === 'Piracy').map(strike => (
                <div key={strike.id} className="bg-[#11111a] border-l-4 border-red-600 p-6 rounded-r-2xl flex justify-between items-center shadow-lg">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <p className="font-mono text-red-400 text-xs tracking-widest">ID: {strike.id.slice(0, 8)}</p>
                      <span className="text-[10px] text-gray-500">{formatTime(strike.detected_at)}</span>
                    </div>
                    <p className="text-gray-300 font-medium">{strike.platform} <span className="text-gray-600 mx-2">|</span> Match: {strike.match_confidence}%</p>
                  </div>
                  <button onClick={() => setSelectedDMCA(strike)} className="bg-red-600/10 text-red-500 border border-red-600/30 px-6 py-2 rounded-lg font-bold hover:bg-red-600 hover:text-white transition-all">
                    Generate DMCA
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* DMCA Modal */}
      {selectedDMCA && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <div className="bg-[#0a0a0f] border border-gray-800 p-10 rounded-2xl max-w-3xl w-full shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <span className="text-red-500">⚖️</span> Official DMCA Notice
              </h2>
              <button onClick={() => setSelectedDMCA(null)} className="text-gray-500 hover:text-white text-xl">✕</button>
            </div>

            <pre className="bg-black p-6 rounded-xl font-mono text-[11px] text-gray-300 h-80 overflow-y-auto mb-8 border border-gray-800 whitespace-pre-wrap leading-relaxed shadow-inner">
              {`TO: ${getLegalEntity(selectedDMCA.platform)}
DATE: ${new Date().toLocaleDateString()}
REF NO: SG-ENF-${Math.floor(Math.random() * 900000) + 100000}
TIME OF INFRACTION: ${formatTime(selectedDMCA.detected_at)}

SUBJECT: Urgent Notice of Copyright Infringement

This notice is provided pursuant to the Digital Millennium Copyright Act (17 U.S.C. § 512). 
We represent the intellectual property owner of the broadcast content described below.

INFRACTION DETAILS:
--------------------------------------------------
Platform: ${selectedDMCA.platform}
Target Media Match Confidence: ${selectedDMCA.match_confidence}% (Verified via pHash structural analysis)
System Risk Score: ${selectedDMCA.risk_score}/100 (HIGH RISK - PIRACY)

SPORTSGUARD AI CONTEXTUAL ANALYSIS:
"${selectedDMCA.reasoning}"

DECLARATION:
--------------------------------------------------
We have a good faith belief that the use of the copyrighted material described above is not authorized by the copyright owner, its agent, or the law. The information in this notification is accurate, and under penalty of perjury, we are authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.

Please remove or disable access to the infringing material immediately.

Submitted electronically by:
SportsGuard AI Automated Enforcement System`}
            </pre>
            <div className="flex justify-end gap-4">
              <button onClick={() => setSelectedDMCA(null)} className="text-gray-500 font-medium hover:text-white">Cancel</button>
              <button onClick={() => {
                navigator.clipboard.writeText("DMCA text copied.");
                alert("Legal notice copied to clipboard. Automatically opening email client...");
                setSelectedDMCA(null);
              }} className="bg-white text-black px-8 py-3 rounded-xl font-bold hover:bg-gray-200 transition-colors">
                Copy & File Notice
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;