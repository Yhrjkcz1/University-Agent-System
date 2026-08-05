import { ConfigProvider, Tabs, Spin, Result, Button } from 'antd';
import { useState, useEffect, Component, type ReactNode } from 'react';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CompetitionsProvider } from './contexts/CompetitionsContext';
import { CompetitionsDataProvider } from './contexts/CompetitionsDataContext';
import { NavigationProvider } from './contexts/NavigationContext';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { AIRecommendation } from './pages/AIRecommendation';
import { CompetitionsLibrary } from './pages/CompetitionsLibrary';
import { Home } from './pages/Home';
import { MyCompetitions } from './pages/MyCompetitions';
import { AdminDashboard } from './pages/AdminDashboard';
import { designTokens } from './styles/tokens';

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  state = { hasError: false, error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="页面出现异常"
          subTitle={this.state.error?.message || '未知错误'}
          extra={<Button type="primary" onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}>刷新页面</Button>}
        />
      );
    }
    return this.props.children;
  }
}

const TAB_KEY = 'saizhitong_active_tab';

function getStoredTab(): string {
  try {
    return sessionStorage.getItem(TAB_KEY) || 'home';
  } catch {
    return 'home';
  }
}

function AppShell() {
  const { user, loading, isAdmin } = useAuth();
  const [activeKey, setActiveKey] = useState(getStoredTab);
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    if (!loading && isAdmin) {
      setActiveKey('admin');
    }
  }, [loading, isAdmin]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (showLogin) {
    return <LoginPage onSuccess={() => setShowLogin(false)} />;
  }

  const tabItems = isAdmin
    ? [
        { key: 'admin', label: '管理', children: <AdminDashboard /> },
        { key: 'library', label: '竞赛库', children: <CompetitionsLibrary /> },
      ]
    : [
        { key: 'home', label: '首页', children: <Home /> },
        { key: 'ai', label: 'AI推荐', children: <AIRecommendation /> },
        { key: 'library', label: '竞赛库', children: <CompetitionsLibrary /> },
        { key: 'mine', label: '我的竞赛', children: <MyCompetitions /> },
      ];

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: designTokens.colorPrimary,
          borderRadius: designTokens.borderRadiusSmall,
        },
      }}
    >
      <NavigationProvider navigateTo={(key: string) => {
        setActiveKey(key);
        try { sessionStorage.setItem(TAB_KEY, key); } catch {}
      }}>
        <AppLayout onLoginClick={() => setShowLogin(true)}>
          <Tabs
            activeKey={tabItems.some(t => t.key === activeKey) ? activeKey : tabItems[0].key}
            onChange={(key) => {
              setActiveKey(key);
              try { sessionStorage.setItem(TAB_KEY, key); } catch {}
            }}
            items={tabItems}
          />
        </AppLayout>
      </NavigationProvider>
    </ConfigProvider>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <CompetitionsDataProvider>
          <CompetitionsProvider>
            <AppShell />
          </CompetitionsProvider>
        </CompetitionsDataProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
