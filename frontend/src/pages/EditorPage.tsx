import { useEffect, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, BrainCircuit, ShieldAlert, Cpu, Layers, Terminal } from 'lucide-react';
import axios from 'axios';
import { useStore } from '../store';

const DEFAULT_CODE: Record<string, string> = {
  python: 'def execute_distributed_task():\n    print("CodeForge Execution Node Initialized.")\n    print("Processing payload...")\n    return {"status": "success"}\n\nexecute_distributed_task()',
  cpp: '#include <iostream>\n\nint main() {\n    std::cout << "CodeForge Execution Node Initialized." << std::endl;\n    return 0;\n}',
  java: 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("CodeForge Execution Node Initialized.");\n    }\n}'
};

export default function EditorPage() {
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(DEFAULT_CODE['python']);
  const [output, setOutput] = useState<{ stdout?: string, stderr?: string, error?: string } | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [jobElapsedMs, setJobElapsedMs] = useState<number>(0);
  const [aiNotification, setAiNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const token = useStore(state => state.token);
  const pollTimeoutRef = useRef<number | null>(null);
  const elapsedIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current !== null) {
        window.clearTimeout(pollTimeoutRef.current);
        pollTimeoutRef.current = null;
      }
      if (elapsedIntervalRef.current !== null) {
        window.clearInterval(elapsedIntervalRef.current);
        elapsedIntervalRef.current = null;
      }
    };
  }, []);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value;
    setLanguage(lang);
    setCode(DEFAULT_CODE[lang] || '');
  };

  const handleExecute = async () => {
    if (pollTimeoutRef.current !== null) {
      window.clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
    if (elapsedIntervalRef.current !== null) {
      window.clearInterval(elapsedIntervalRef.current);
      elapsedIntervalRef.current = null;
    }
    setIsExecuting(true);
    setOutput(null);
    setJobStatus('SUBMITTED');
    setJobElapsedMs(0);
    try {
      const idempotency_key = crypto.randomUUID();
      
      const res = await axios.post('/api/jobs/', 
        { idempotency_key, language, code, priority: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const jobId = res.data.id;

      const startedAt = Date.now();
      elapsedIntervalRef.current = window.setInterval(() => {
        setJobElapsedMs(Date.now() - startedAt);
      }, 250);
      const pollOnce = async (attempt: number) => {
        try {
          const statusRes = await axios.get(`/api/jobs/${jobId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          setJobStatus(statusRes.data.status || 'UNKNOWN');

          if (statusRes.data.status === 'COMPLETED') {
            setIsExecuting(false);
            if (elapsedIntervalRef.current !== null) {
              window.clearInterval(elapsedIntervalRef.current);
              elapsedIntervalRef.current = null;
            }
            setOutput({
              stdout: statusRes.data.result?.stdout,
              stderr: statusRes.data.result?.stderr,
            });
            return;
          }

          if (statusRes.data.status === 'FAILED') {
            setIsExecuting(false);
            if (elapsedIntervalRef.current !== null) {
              window.clearInterval(elapsedIntervalRef.current);
              elapsedIntervalRef.current = null;
            }
            setOutput({
              stdout: statusRes.data.result?.stdout,
              stderr: statusRes.data.result?.stderr,
              error: statusRes.data.result?.error_message,
            });
            return;
          }

          const elapsedMs = Date.now() - startedAt;
          // First run may pull Docker images inside the worker host; allow more time.
          if (attempt >= 600 || elapsedMs > 10 * 60_000) {
            setIsExecuting(false);
            if (elapsedIntervalRef.current !== null) {
              window.clearInterval(elapsedIntervalRef.current);
              elapsedIntervalRef.current = null;
            }
            setOutput({ error: 'Execution timed out — the sandbox may still be running. Try again.' });
            return;
          }

          const nextDelayMs = Math.min(1500, 250 + attempt * 50);
          pollTimeoutRef.current = window.setTimeout(() => {
            pollOnce(attempt + 1);
          }, nextDelayMs);
        } catch (e: any) {
          setIsExecuting(false);
          if (elapsedIntervalRef.current !== null) {
            window.clearInterval(elapsedIntervalRef.current);
            elapsedIntervalRef.current = null;
          }
          setOutput({
            error:
              e?.response?.data?.detail ||
              e?.message ||
              'Failed to fetch job status from API.',
          });
        }
      };

      // Fetch immediately (don’t wait 1s) and avoid overlapping requests.
      void pollOnce(0);

    } catch (err: any) {
      setIsExecuting(false);
      if (elapsedIntervalRef.current !== null) {
        window.clearInterval(elapsedIntervalRef.current);
        elapsedIntervalRef.current = null;
      }
      setOutput({ error: err.response?.data?.detail || err.message });
    }
  };

  const handleAIAction = async (endpoint: string) => {
    setAiNotification(null);
    try {
        const res = await axios.post(`/api/ai/${endpoint}`, 
          { code },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setAiNotification({ message: `✓ ${res.data.message} — Job ID: ${res.data.job_id.substring(0,8)}...`, type: 'success' });
        setTimeout(() => setAiNotification(null), 6000);
    } catch (err: any) {
        setAiNotification({ message: 'Failed: ' + (err.response?.data?.detail || err.message), type: 'error' });
        setTimeout(() => setAiNotification(null), 6000);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', gap: '2rem', height: '100%' }}>
      
      {/* Editor Main Area */}
      <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
             <Layers size={20} color="var(--text-secondary)" />
             <select 
               value={language} 
               onChange={handleLanguageChange}
               className="glass-input"
               style={{ width: '220px', padding: '0.6rem 1rem' }}
             >
               <option value="python">Python 3.11 Environment</option>
               <option value="cpp">C++ (GCC 12) Environment</option>
               <option value="java">Java 17 Environment</option>
             </select>
          </div>

          <button onClick={handleExecute} disabled={isExecuting} className="primary-button" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Play size={18} fill="currentColor" />
            {isExecuting ? 'Allocating Node & Executing...' : 'Execute Payload'}
          </button>
        </div>

        <div className="glass-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', border: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ padding: '0.75rem 1.5rem', background: 'rgba(0,0,0,0.4)', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
             <Cpu size={14} /> main_worker_thread.{language === 'python' ? 'py' : language}
          </div>
          <div style={{ flex: 1, padding: '1rem 0' }}>
            <Editor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(val) => setCode(val || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 15,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                lineHeight: 1.6,
                padding: { top: 8 },
                scrollBeyondLastLine: false,
                smoothScrolling: true,
                cursorBlinking: "smooth",
                cursorSmoothCaretAnimation: "on"
              }}
            />
          </div>
        </div>
      </div>

      {/* Side Panel: Results & AI */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Output Panel */}
        <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(0,0,0,0.2)' }}>
             <Terminal size={18} color="var(--accent-color)" /> Stdout console
          </div>
          <div style={{ 
            padding: '1.5rem', flex: 1, overflowY: 'auto', 
            fontFamily: "'JetBrains Mono', monospace", fontSize: '0.9rem', 
            background: 'rgba(0,0,0,0.5)', lineHeight: 1.7
          }}>
            {output ? (
              <div className="animate-fade-in">
                {output.error && <div style={{ color: 'var(--error)', marginBottom: '0.5rem' }}>[SYSTEM ERROR] {output.error}</div>}
                {output.stderr && <div style={{ color: 'var(--error)', marginBottom: '0.5rem' }}>{output.stderr}</div>}
                {output.stdout && <div style={{ color: 'var(--success)' }}>{output.stdout}</div>}
                <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px dashed rgba(255,255,255,0.1)', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                   Process Exited.
                </div>
              </div>
            ) : (
               <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.7 }}>
                 <Terminal size={48} style={{ marginBottom: '1rem' }} />
                 {isExecuting ? (
                   <>
                     <span style={{ marginBottom: '0.35rem' }}>
                       Executing… {jobStatus ? `(${jobStatus})` : ''}
                     </span>
                     <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>
                       {Math.max(0, Math.round(jobElapsedMs / 1000))}s elapsed
                       {jobElapsedMs > 8000 ? ' — first run may be pulling sandbox images' : ''}
                     </span>
                   </>
                 ) : (
                   <span>Awaiting execution output...</span>
                 )}
               </div>
            )}
          </div>
        </div>

        {/* AI Features Panel */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.15rem' }}>
            <BrainCircuit size={20} color="#8b5cf6"/> 
            Distributed AI Analysis
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Offload complex heuristic checks to our asynchronous AI worker cluster.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
            <button onClick={() => handleAIAction('explain')} className="glass-button" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '0.85rem' }}>
              <BrainCircuit size={18} color="#8b5cf6" /> Generate Explanation
            </button>
            <button onClick={() => handleAIAction('plagiarism')} className="glass-button" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '0.85rem' }}>
              <ShieldAlert size={18} color="#f59e0b" /> Detect Plagiarism
            </button>
            {aiNotification && (
              <div className="animate-fade-in" style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.82rem',
                lineHeight: 1.5,
                background: aiNotification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                border: `1px solid ${aiNotification.type === 'success' ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
                color: aiNotification.type === 'success' ? 'var(--success)' : 'var(--error)',
                wordBreak: 'break-all',
              }}>
                {aiNotification.message}
              </div>
            )}
          </div>
        </div>
      </div>
    
    </div>
  );
}
