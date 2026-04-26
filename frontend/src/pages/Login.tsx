import { useState } from 'react';
import { useStore } from '../store';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Code2, KeyRound, Mail, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('engineer@codeforge.ai');
  const [password, setPassword] = useState('password');
  const [isLoading, setIsLoading] = useState(false);
  const setAuth = useStore((state) => state.setAuth);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await axios.post('/api/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      // Mock User setting for now
      setAuth(res.data.access_token, { id: 'user_id', email, role: 'User', balance: 100 });
      navigate('/editor');
    } catch (err) {
      alert('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
      
      <div className="glass-panel animate-fade-in" style={{ 
        padding: '3.5rem', 
        width: '440px',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
           position: 'absolute', top: '-50px', left: '-50px',
           width: '150px', height: '150px',
           background: 'rgba(59, 130, 246, 0.4)',
           filter: 'blur(60px)', zIndex: 0
        }} />
        <div style={{
           position: 'absolute', bottom: '-50px', right: '-50px',
           width: '150px', height: '150px',
           background: 'rgba(139, 92, 246, 0.4)',
           filter: 'blur(60px)', zIndex: 0
        }} />

        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', 
          marginBottom: '2.5rem', zIndex: 1 
        }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', 
            padding: '12px', borderRadius: '14px',
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
          }}>
            <Code2 size={32} color="white" />
          </div>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
            CodeForge
          </h2>
        </div>
        
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', zIndex: 1 }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500 }}>
              <Mail size={16} /> Email Address
            </label>
            <input 
              type="email" 
              className="glass-input" 
              placeholder="engineer@codeforge.ai"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required 
            />
          </div>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500 }}>
              <KeyRound size={16} /> Password
            </label>
            <input 
              type="password" 
              className="glass-input" 
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required 
            />
          </div>
          <button type="submit" className="primary-button" disabled={isLoading} style={{ 
            marginTop: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', height: '50px' 
          }}>
            {isLoading ? 'Authenticating...' : 'Sign In To Sandbox'} {!isLoading && <ArrowRight size={20} />}
          </button>
        </form>
        
      </div>
      
    </div>
  );
}
