import { useState, useEffect } from 'react';
import axios from 'axios';
import { useStore } from '../store';
import { Activity, XCircle, CheckCircle2, AlertCircle } from 'lucide-react';

export default function JobsList() {
  const [jobs, setJobs] = useState<any[]>([]);
  const token = useStore(state => state.token);

  useEffect(() => {
     // Mock fetch for now, realistically there would be a GET /jobs/user endpoint
     const fetchFailedJobs = async () => {
         try {
             // In a real app we'd fetch all jobs, but the endpoint we built is `/jobs/failed`
             // I will mock some jobs here, or we can just fetch failed
             const res = await axios.get('/api/jobs/failed', {
                 headers: { Authorization: `Bearer ${token}` }
             });
             setJobs(res.data);
         } catch(e) { }
     };
     fetchFailedJobs();
  }, [token]);

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <h3 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.25rem' }}>
        <Activity size={24} color="var(--accent-color)" />
        Distributed Job History (Failed)
      </h3>
      
      {jobs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
          <CheckCircle2 size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <p>No failed jobs found. Everything is running smoothly.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {jobs.map(job => (
            <div key={job.id} className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(239, 68, 68, 0.05)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600 }}>Job ID: <span style={{ fontFamily: 'monospace', opacity: 0.8 }}>{job.id}</span></div>
                <div className={`status-badge status-${job.status}`}>{job.status}</div>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', display: 'flex', gap: '2rem' }}>
                <span>Language: <strong style={{ color: 'var(--text-primary)' }}>{job.language}</strong></span>
                <span>Retries: <strong style={{ color: 'var(--text-primary)' }}>{job.retry_count} / 3</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
