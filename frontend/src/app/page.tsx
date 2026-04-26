"use client";

import { useEffect, useRef, useState, type ChangeEvent } from "react";

/* ---------- types ---------- */
type Detection = {
  id?: number | string;
  reddit_url: string;
  reddit_post_title?: string;
  classification: "Piracy" | "Meme" | "Transformative" | string;
  risk_score: number;
  reasoning: string;
  distance?: number;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/* ---------- helpers ---------- */
function badgeClasses(classification: string) {
  if (classification === "Piracy") {
    return "bg-red-100 text-red-700 ring-red-200 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-500/20";
  }
  if (classification === "Meme") {
    return "bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-400/10 dark:text-amber-400 dark:ring-amber-500/20";
  }
  return "bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-400/10 dark:text-emerald-400 dark:ring-emerald-500/20";
}

function riskColor(score: number) {
  if (score >= 85) return "text-red-600 dark:text-red-400";
  if (score >= 35) return "text-amber-600 dark:text-amber-400";
  return "text-emerald-600 dark:text-emerald-400";
}

function getLegalEntity(redditUrl: string): string {
  try {
    const host = new URL(redditUrl).hostname;
    if (host.includes("redd.it") || host.includes("reddit.com"))
      return "Reddit, Inc. – Copyright Agent";
  } catch { }
  return "Platform Copyright Agent";
}

/** Full DMCA takedown notice */
function generateDMCANotice(detection: Detection): string {
  const now = new Date().toLocaleDateString();
  return `TO: ${getLegalEntity(detection.reddit_url)}
DATE: ${now}
REF NO: SG-DMCA-${Math.floor(Math.random() * 900000) + 100000}
DETECTION TIME: ${now}

SUBJECT: Urgent Notice of Copyright Infringement

This notice is sent pursuant to the Digital Millennium Copyright Act (17 U.S.C. § 512).
We represent the intellectual property owner of the broadcast content detailed below.

INFRACTION DETAILS:
--------------------------------------------------
URL: ${detection.reddit_url}
${detection.reddit_post_title ? `TITLE: ${detection.reddit_post_title}\n` : ""}
MATCH CONFIDENCE: ${detection.risk_score}% (visual fingerprint verified)
AI CONTEXT: ${detection.reasoning}

DECLARATION:
--------------------------------------------------
We have a good faith belief that the use of the copyrighted material described above is not
authorized by the copyright owner, its agent, or the law. The information in this notification
is accurate, and under penalty of perjury, we are authorized to act on behalf of the owner of
an exclusive right that is allegedly infringed.

Please remove or disable access to the infringing material immediately.

This notice is submitted electronically by:
SportsGuard AI Automated Enforcement System`;
}

/* ---------- icons ---------- */
const ShieldIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 2l7 4v5c0 5-3.5 9.1-7 10-3.5-.9-7-5-7-10V6l7-4z" />
  </svg>
);
const UploadIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12" />
  </svg>
);
const ScanIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
  </svg>
);
const SunIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="5" />
    <path strokeLinecap="round" d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);
const MoonIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
  </svg>
);

/* ---------- main component ---------- */
export default function HomePage() {
  // ---------- theme ----------
  const [isDark, setIsDark] = useState(true);

  // Apply dark class on initial render and when toggled
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  // ---------- data ----------
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [statusMessage, setStatusMessage] = useState("Waiting for the first official upload.");
  const pollerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [isHealthy, setIsHealthy] = useState(true);
  const [scanStatus, setScanStatus] = useState("");
  const scanPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [resetting, setResetting] = useState(false);
  const [selectedDMCA, setSelectedDMCA] = useState<Detection | null>(null);

  // health check
  useEffect(() => {
    const check = async () => {
      try { setIsHealthy((await fetch(`${API_BASE_URL}/api/health`)).ok); }
      catch { setIsHealthy(false); }
    };
    check();
    const id = setInterval(check, 10_000);
    return () => clearInterval(id);
  }, []);

  // detections polling
  useEffect(() => {
    const fetchD = async () => {
      try {
        const r = await fetch(`${API_BASE_URL}/api/detections`, { cache: "no-store" });
        if (r.ok) setDetections(await r.json());
        else throw new Error();
      } catch { setStatusMessage("Detection feed temporarily unavailable."); }
    };
    fetchD();
    pollerRef.current = setInterval(fetchD, 5000);
    return () => { if (pollerRef.current) clearInterval(pollerRef.current); };
  }, []);

  // upload
  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    setUploading(true);
    setStatusMessage(`Hashing ${file.name}...`);
    try {
      const res = await fetch(`${API_BASE_URL}/api/upload`, { method: "POST", body: fd });
      const p = await res.json();
      if (!res.ok) throw new Error(p.detail ?? "Upload failed.");
      setStatusMessage(`Stored ${p.filename} with 3 visual hashes.`);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Upload failed.");
    } finally { setUploading(false); e.target.value = ""; }
  };

  // scan trigger
  const triggerScan = async () => {
    setScanning(true);
    setScanStatus("");
    setStatusMessage("Starting scan...");
    try {
      const res = await fetch(`${API_BASE_URL}/api/start-scan`, { method: "POST" });
      const p = await res.json();
      if (!res.ok) throw new Error(p.detail ?? "Scan start failed.");
      setStatusMessage(p.message ?? "Scan started.");
      if (scanPollRef.current) clearInterval(scanPollRef.current);
      scanPollRef.current = setInterval(async () => {
        try {
          const sr = await fetch(`${API_BASE_URL}/api/scan-status`);
          if (sr.ok) {
            const d = await sr.json();
            if (d.status === "completed") {
              setScanStatus(d.message);
              setStatusMessage(d.message);
              setScanning(false);
              clearInterval(scanPollRef.current!);
            } else if (d.status === "running") setScanStatus("Scan in progress…");
          }
        } catch { }
      }, 2000);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Scan failed.");
      setScanning(false);
    }
  };

  useEffect(() => () => { if (scanPollRef.current) clearInterval(scanPollRef.current); }, []);

  // clear feed
  const handleReset = async () => {
    if (!confirm("Clear all detections?")) return;
    setResetting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/reset-detections`, { method: "POST" });
      if (!res.ok) throw new Error("Reset failed.");
      setDetections([]);
      setStatusMessage("Feed cleared.");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Reset failed.");
    } finally { setResetting(false); }
  };

  // DMCA copy
  const copyDMCA = () => {
    if (!selectedDMCA) return;
    navigator.clipboard.writeText(generateDMCANotice(selectedDMCA));
    setSelectedDMCA(null);
  };

  // stats
  const totalDetections = detections.length;
  const piracyCount = detections.filter(d => d.classification === "Piracy").length;

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-[#070708] text-gray-900 dark:text-gray-200 font-sans antialiased transition-colors duration-300">
      {/* ---- top bar ---- */}
      <header className="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 bg-white/90 dark:bg-[#0c0c0d]/90 backdrop-blur-sm z-20 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center shadow-sm">
            <ShieldIcon />
          </div>
          <span className="text-sm font-bold tracking-tight text-gray-900 dark:text-white">SportsGuard</span>
          <span className="hidden sm:inline text-[10px] text-gray-400 dark:text-gray-500 ml-2 font-medium uppercase tracking-widest">
            Enforcement Console
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className={`flex items-center gap-1.5 ${isHealthy ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
            <span className={`h-2 w-2 rounded-full ${isHealthy ? "bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.6)]" : "bg-red-500"}`} />
            {isHealthy ? "Live" : "Down"}
          </span>
          <button
            onClick={() => setIsDark(!isDark)}
            className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            title="Toggle theme"
          >
            {isDark ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </header>

      {/* ---- main content ---- */}
      <div className="flex-1 flex flex-col overflow-hidden p-6 gap-6">
        {/* stats */}
        <div className="grid grid-cols-3 gap-4 flex-shrink-0">
          <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#0f0f10] p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">Detections</p>
            <p className="text-2xl font-semibold mt-1 text-gray-900 dark:text-white">{totalDetections}</p>
          </div>
          <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#0f0f10] p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">Piracy Flags</p>
            <p className="text-2xl font-semibold mt-1 text-red-600 dark:text-red-400">{piracyCount}</p>
          </div>
          <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#0f0f10] p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">System</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`h-2.5 w-2.5 rounded-full ${isHealthy ? "bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.6)]" : "bg-red-500"}`} />
              <span className="text-2xl font-semibold text-gray-900 dark:text-white">{isHealthy ? "Online" : "Offline"}</span>
            </div>
          </div>
        </div>

        {/* toolbar */}
        <div className="flex flex-wrap items-end justify-between gap-4 flex-shrink-0">
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Threat Feed</h1>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
              Latest detections from Reddit scans.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800/50 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 transition">
              <UploadIcon />
              {uploading ? "Uploading…" : "Upload MP4"}
              <input type="file" accept=".mp4,video/mp4" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
            <button
              onClick={triggerScan}
              disabled={scanning}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <ScanIcon />
              {scanning ? "Scanning…" : "Start Scan"}
            </button>
            <button
              onClick={handleReset}
              disabled={resetting}
              className="rounded-lg border border-gray-300 dark:border-gray-700 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:border-red-300 dark:hover:border-red-700 transition"
            >
              Clear Feed
            </button>
          </div>
        </div>

        {/* status */}
        <div className="text-sm text-gray-500 dark:text-gray-400 flex-shrink-0">
          {statusMessage}
          {scanStatus && <span className="ml-3 text-gray-400 dark:text-gray-500 text-xs">{scanStatus}</span>}
        </div>

        {/* detection table */}
        <div className="flex-1 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-[#0c0c0d] shadow-sm">
          <div className="h-full overflow-y-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900/40 text-xs uppercase text-gray-500 sticky top-0 z-10">
                <tr>
                  <th className="px-5 py-3 text-left font-medium">Content</th>
                  <th className="px-5 py-3 text-left font-medium">Classification</th>
                  <th className="px-5 py-3 text-left font-medium">Risk</th>
                  <th className="px-5 py-3 text-left font-medium">Reasoning</th>
                  <th className="px-5 py-3 text-left font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800/50">
                {detections.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-16 text-center text-gray-400 dark:text-gray-600">
                      No detections yet. Upload an official asset and start a scan.
                    </td>
                  </tr>
                ) : (
                  detections.map((d) => (
                    <tr key={d.id ?? d.reddit_url} className="hover:bg-gray-50 dark:hover:bg-white/[0.02] transition">
                      <td className="px-5 py-3">
                        <a href={d.reddit_url} target="_blank" rel="noreferrer" className="text-gray-800 dark:text-gray-200 underline decoration-gray-300 dark:decoration-gray-700 underline-offset-4 hover:text-black dark:hover:text-white transition text-sm">
                          {d.reddit_url}
                        </a>
                        {d.reddit_post_title && (
                          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 line-clamp-2">{d.reddit_post_title}</p>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${badgeClasses(d.classification)}`}>
                          {d.classification}
                        </span>
                      </td>
                      <td className={`px-5 py-3 font-mono text-sm font-semibold ${riskColor(d.risk_score)}`}>
                        {d.risk_score}
                      </td>
                      <td className="px-5 py-3 text-gray-600 dark:text-gray-400 text-xs leading-relaxed max-w-xs">{d.reasoning}</td>
                      <td className="px-5 py-3">
                        {d.classification === "Piracy" && (
                          <button
                            onClick={() => setSelectedDMCA(d)}
                            className="text-xs font-semibold text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 underline underline-offset-2 transition"
                          >
                            Issue DMCA
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ---------- DMCA Modal ---------- */}
      {selectedDMCA && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 dark:bg-black/80 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#0c0c0d] border border-gray-200 dark:border-gray-800 rounded-2xl max-w-3xl w-full mx-4 shadow-2xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">DMCA Takedown Notice</h3>
              <button onClick={() => setSelectedDMCA(null)} className="text-gray-400 hover:text-gray-600 dark:hover:text-white text-xl leading-none">&times;</button>
            </div>
            <pre className="bg-gray-50 dark:bg-black border-b border-gray-200 dark:border-gray-800 p-6 text-xs font-mono text-gray-800 dark:text-gray-300 h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {generateDMCANotice(selectedDMCA)}
            </pre>
            <div className="flex justify-end gap-3 px-6 py-4">
              <button onClick={() => setSelectedDMCA(null)} className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white text-sm font-medium">Cancel</button>
              <button onClick={copyDMCA} className="bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white px-5 py-2 rounded-lg text-sm font-semibold shadow-sm transition">
                Copy &amp; Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}