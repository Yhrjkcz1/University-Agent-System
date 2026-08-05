import { createContext, useContext, useEffect, useState, useCallback, useRef, type ReactNode } from 'react';
import { type Competition } from '../services/competitions';
import { useAuth } from './AuthContext';
import { message } from 'antd';
import { request } from '../services/apiClient';

interface CompetitionsContextType {
  myCompetitions: Competition[];
  addCompetition: (competition: Competition) => boolean;
  removeCompetition: (id: number) => void;
  isJoined: (id: number) => boolean;
  loading: boolean;
}

const CompetitionsContext = createContext<CompetitionsContextType | null>(null);

async function loadFromServer(): Promise<Competition[]> {
  const res = await request<{ items: Competition[] }>('/api/saved-competitions');
  return res.items || [];
}

export function CompetitionsProvider({ children }: { children: ReactNode }) {
  const { user, accessToken } = useAuth();
  const prevUserId = useRef<string | undefined>(undefined);
  const [myCompetitions, setMyCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(false);

  // 登录/退出 → 重新从服务端加载
  useEffect(() => {
    // 等待 accessToken 就绪后再请求，避免不带 token 的 401
    if (!user || !accessToken) {
      setMyCompetitions([]);
      prevUserId.current = undefined;
      return;
    }

    if (prevUserId.current === user.id) return;
    prevUserId.current = user.id;

    setLoading(true);
    loadFromServer()
      .then(setMyCompetitions)
      .catch((err) => {
        console.error('[Competitions] 加载我的竞赛失败:', err);
      })
      .finally(() => setLoading(false));
  }, [user, accessToken]);

  const addCompetition = useCallback((competition: Competition): boolean => {
    if (!user) {
      message.warning('请先登录后再添加竞赛');
      return false;
    }
    setMyCompetitions((prev) => {
      if (prev.some((item) => item.id === competition.id)) return prev;
      return [...prev, competition];
    });
    request(`/api/saved-competitions/${competition.id}`, { method: 'POST' }).catch((err) => {
      console.error('[Competitions] 添加收藏失败:', err);
      setMyCompetitions((prev) => prev.filter((item) => item.id !== competition.id));
    });
    return true;
  }, [user]);

  const removeCompetition = useCallback((id: number) => {
    if (!user) return;
    setMyCompetitions((prev) => prev.filter((item) => item.id !== id));
    request(`/api/saved-competitions/${id}`, { method: 'DELETE' }).catch((err) => {
      console.error('[Competitions] 移除收藏失败:', err);
      loadFromServer().then(setMyCompetitions).catch(() => {});
    });
  }, [user]);

  const isJoined = useCallback(
    (id: number) => myCompetitions.some((item) => item.id === id),
    [myCompetitions],
  );

  return (
    <CompetitionsContext.Provider value={{ myCompetitions, addCompetition, removeCompetition, isJoined, loading }}>
      {children}
    </CompetitionsContext.Provider>
  );
}

export function useCompetitions(): CompetitionsContextType {
  const ctx = useContext(CompetitionsContext);
  if (!ctx) throw new Error('useCompetitions must be used within CompetitionsProvider');
  return ctx;
}
