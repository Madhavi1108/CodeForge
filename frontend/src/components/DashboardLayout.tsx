import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';
import { Terminal, LayoutDashboard, LogOut, Code2, Banknote, Sparkles } from 'lucide-react';
import { useStore } from '../store';

export default function DashboardLayout() {
  const logout = useStore(state => state.logout);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NavItem = ({ to, icon, label }: { to: string, icon: React.ReactNode, label: string }) => {
    const isActive = location.pathname.includes(to);
    return (
      <Link 
        to={to} 
        style={{
          display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem 1.25rem', 
          borderRadius: '12px', color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
          background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
          textDecoration: 'none', transition: 'all 0.3s', fontWeight: isActive ? 600 : 500,
          boxShadow: isActive ? 'inset 0 0 0 1px rgba(59, 130, 246, 0.3), 0 4px 12px rgba(59, 130, 246, 0.1)' : 'none',
        }}
      >
        <div style={{ color: isActive ? 'var(--accent-color)' : 'inherit' }}>
          {icon}
        </div>
        {label}
      </Link>
    );
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '3.5rem' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', 
            padding: '8px', borderRadius: '10px',
            boxShadow: '0 0 15px rgba(59, 130, 246, 0.4)'
          }}>
            <Code2 size={24} color="white" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.5px' }}>CodeForge</h1>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          <NavItem to="/editor" icon={<Terminal size={20} />} label="Execution Sandbox" />
          <NavItem to="/jobs" icon={<LayoutDashboard size={20} />} label="Global Job Tracker" />
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <button 
            onClick={handleLogout}
            className="glass-button" 
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', color: 'rgba(255,255,255,0.6)' }}
          >
            <LogOut size={18} />
            Disconnect Session
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <h2 style={{ fontSize: '1.35rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {location.pathname.includes('editor') ? <><Sparkles size={22} color="var(--accent-color)"/> Distributed Sandbox</> : <><LayoutDashboard size={22} color="var(--accent-color)"/> Job Telemetry</>}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div className="glass-panel" style={{ 
              padding: '0.6rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', 
              fontSize: '0.9rem', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.2)' 
            }}>
              <Banknote size={18} color="var(--success)" />
              <span style={{ color: 'var(--text-secondary)'}}>Compute Credits: <strong style={{ color: 'var(--text-primary)', fontSize: '1rem'}}>100.00</strong></span>
            </div>
            
            <div style={{
               width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, #1e293b, #334155)',
               border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
               fontWeight: 600, boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
            }}>
               U
            </div>
          </div>
        </header>

        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
