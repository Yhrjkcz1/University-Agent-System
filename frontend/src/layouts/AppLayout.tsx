import { useState, type ReactNode } from 'react';
import { Layout, Typography, Dropdown, Button, Avatar, Space } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  LockOutlined,
  SafetyOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { logout } from '../services/authService';
import { designTokens } from '../styles/tokens';
import {
  EditProfileModal,
  ChangePasswordModal,
  SessionManagerModal,
  DeleteAccountModal,
} from '../components/UserSettingsModals';

type ModalType = 'profile' | 'password' | 'sessions' | 'delete' | null;

interface AppLayoutProps {
  children: ReactNode;
  onLoginClick?: () => void;
}

export function AppLayout({ children, onLoginClick }: AppLayoutProps) {
  const { user, clearAuth, isAdmin } = useAuth();
  const [modal, setModal] = useState<ModalType>(null);

  const handleLogout = async () => {
    await logout();
    clearAuth();
  };

  const userMenu = {
    items: [
      {
        key: 'username',
        icon: <UserOutlined />,
        label: user?.display_name || user?.username || '用户',
        disabled: true,
      },
      { type: 'divider' as const },
      ...(isAdmin
        ? [
            {
              key: 'admin',
              icon: <SettingOutlined />,
              label: '管理后台',
            },
            { type: 'divider' as const },
          ]
        : []),
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人信息',
      },
      {
        key: 'password',
        icon: <LockOutlined />,
        label: '修改密码',
      },
      {
        key: 'sessions',
        icon: <SafetyOutlined />,
        label: '会话管理',
      },
      { type: 'divider' as const },
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除账号',
        danger: true,
      },
      { type: 'divider' as const },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        danger: true,
      },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') handleLogout();
      else if (key === 'profile') setModal('profile');
      else if (key === 'password') setModal('password');
      else if (key === 'sessions') setModal('sessions');
      else if (key === 'delete') setModal('delete');
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header
        style={{
          background: designTokens.colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: designTokens.boxShadow,
          padding: '0 32px',
        }}
      >
        <Typography.Title level={4} style={{ margin: 0, color: designTokens.colorPrimary }}>
          赛智通
        </Typography.Title>
        <Space>
          {user ? (
            <Dropdown menu={userMenu} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  style={{ backgroundColor: designTokens.colorPrimary }}
                />
                <Typography.Text style={{ fontSize: 14 }}>
                  {user.display_name || user.username}
                </Typography.Text>
              </Space>
            </Dropdown>
          ) : (
            <Button
              type="primary"
              size="small"
              onClick={onLoginClick}
              style={{ borderRadius: 10, height: 36, padding: '0 20px' }}
            >
              登录 / 注册
            </Button>
          )}
        </Space>
      </Layout.Header>
      <Layout.Content style={{ padding: '12px 32px 32px' }}>{children}</Layout.Content>
      <Layout.Footer
        style={{
          textAlign: 'center',
          color: designTokens.colorTextSecondary,
        }}
      >
        用 AI 帮你找到更适合的竞赛
      </Layout.Footer>

      {/* 用户设置弹窗 */}
      <EditProfileModal open={modal === 'profile'} onClose={() => setModal(null)} />
      <ChangePasswordModal open={modal === 'password'} onClose={() => setModal(null)} />
      <SessionManagerModal open={modal === 'sessions'} onClose={() => setModal(null)} />
      <DeleteAccountModal open={modal === 'delete'} onClose={() => setModal(null)} />
    </Layout>
  );
}
