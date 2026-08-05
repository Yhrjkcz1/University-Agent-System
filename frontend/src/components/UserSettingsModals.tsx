import { useState, useEffect } from 'react';
import { Modal, Form, Input, Button, List, Typography, message, Popconfirm } from 'antd';
import { DesktopOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { updateProfile, changePassword, deleteAccount, fetchSessions, revokeSession } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';
import type { SessionInfo } from '../services/authTypes';

// ==================== 编辑个人信息 ====================

export function EditProfileModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { user, setAuth, accessToken } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) form.resetFields();
  }, [open, form]);

  return (
    <Modal title="个人信息" open={open} onCancel={onClose} footer={null} destroyOnClose>
      <Form
        form={form}
        layout="vertical"
        initialValues={{ display_name: user?.display_name || '' }}
        onFinish={async (values) => {
          setLoading(true);
          try {
            const updated = await updateProfile({ display_name: values.display_name });
            if (updated && accessToken) {
              setAuth(accessToken, updated);
            }
            message.success('修改成功');
            onClose();
          } catch {
            message.error('修改失败');
          } finally {
            setLoading(false);
          }
        }}
      >
        <Form.Item label="用户名">
          <Input value={user?.username || ''} disabled />
        </Form.Item>
        <Form.Item label="角色">
          <Input value={user?.role === 'admin' ? '管理员' : '普通用户'} disabled />
        </Form.Item>
        <Form.Item label="注册时间">
          <Input value={user?.created_at || ''} disabled />
        </Form.Item>
        <Form.Item name="display_name" label="显示名称">
          <Input placeholder="输入显示名称" maxLength={32} />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Button onClick={onClose} style={{ marginRight: 8 }}>取消</Button>
          <Button type="primary" htmlType="submit" loading={loading}>保存</Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}

// ==================== 修改密码 ====================

export function ChangePasswordModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { clearAuth } = useAuth();

  useEffect(() => {
    if (open) form.resetFields();
  }, [open, form]);

  return (
    <Modal title="修改密码" open={open} onCancel={onClose} footer={null} destroyOnClose>
      <Form
        form={form}
        layout="vertical"
        onFinish={async (values) => {
          setLoading(true);
          try {
            await changePassword(values.old_password, values.new_password);
            message.success('密码修改成功，请重新登录');
            clearAuth();
            onClose();
          } catch (e: any) {
            message.error(e?.message || '修改失败');
          } finally {
            setLoading(false);
          }
        }}
      >
        <Form.Item
          name="old_password"
          label="原密码"
          rules={[{ required: true, message: '请输入原密码' }]}
        >
          <Input.Password placeholder="输入原密码" />
        </Form.Item>
        <Form.Item
          name="new_password"
          label="新密码"
          rules={[
            { required: true, message: '请输入新密码' },
            { min: 8, message: '密码至少 8 位' },
            {
              pattern: /^(?=.*[a-zA-Z])(?=.*\d)/,
              message: '密码需包含字母和数字',
            },
          ]}
        >
          <Input.Password placeholder="8位以上，含字母和数字" />
        </Form.Item>
        <Form.Item
          name="confirm_password"
          label="确认新密码"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请再次输入新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) return Promise.resolve();
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password placeholder="再次输入新密码" />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Button onClick={onClose} style={{ marginRight: 8 }}>取消</Button>
          <Button type="primary" htmlType="submit" loading={loading}>确认修改</Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}

// ==================== 会话管理 ====================

export function SessionManagerModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      fetchSessions()
        .then(setSessions)
        .finally(() => setLoading(false));
    }
  }, [open]);

  async function handleRevoke(id: string) {
    try {
      await revokeSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      message.success('已撤销');
    } catch {
      message.error('撤销失败');
    }
  }

  return (
    <Modal title="会话管理" open={open} onCancel={onClose} footer={null} width={560}>
      <Typography.Text type="secondary" style={{ fontSize: 13 }}>
        管理您所有设备的登录会话，最多保留 5 个活跃会话。
      </Typography.Text>
      <List
        loading={loading}
        style={{ marginTop: 16 }}
        dataSource={sessions}
        locale={{ emptyText: '暂无活跃会话' }}
        renderItem={(s) => (
          <List.Item
            actions={[
              s.is_current ? (
                <Typography.Text type="success" style={{ fontSize: 12 }}>
                  <CheckCircleOutlined /> 当前设备
                </Typography.Text>
              ) : (
                <Popconfirm title="确定撤销此会话？" onConfirm={() => handleRevoke(s.id)}>
                  <Button size="small" danger>撤销</Button>
                </Popconfirm>
              ),
            ]}
          >
            <List.Item.Meta
              avatar={<DesktopOutlined style={{ fontSize: 20, color: s.is_current ? '#52c41a' : '#999' }} />}
              title={
                <span>
                  {s.device_info || '未知设备'}
                  {s.is_current && (
                    <Typography.Text type="success" style={{ marginLeft: 8, fontSize: 12 }}>
                      当前
                    </Typography.Text>
                  )}
                </span>
              }
              description={
                <span style={{ fontSize: 12 }}>
                  <ClockCircleOutlined style={{ marginRight: 4 }} />
                  最近活跃：{s.last_used_at || s.created_at || '-'}
                </span>
              }
            />
          </List.Item>
        )}
      />
      <div style={{ textAlign: 'right', marginTop: 16 }}>
        <Button onClick={onClose}>关闭</Button>
      </div>
    </Modal>
  );
}

// ==================== 删除账号 ====================

export function DeleteAccountModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { clearAuth, user } = useAuth();

  useEffect(() => {
    if (open) form.resetFields();
  }, [open, form]);

  return (
    <Modal title="删除账号" open={open} onCancel={onClose} footer={null} destroyOnClose>
      <Typography.Paragraph type="danger" style={{ marginBottom: 16 }}>
        此操作不可撤销。删除后账号将被冻结，您将无法登录。
      </Typography.Paragraph>
      <Form
        form={form}
        layout="vertical"
        onFinish={async () => {
          setLoading(true);
          try {
            await deleteAccount();
            message.success('账号已注销');
            clearAuth();
            onClose();
          } catch (e: any) {
            message.error(e?.message || '操作失败');
          } finally {
            setLoading(false);
          }
        }}
      >
        <Form.Item
          name="confirm"
          label={`请输入用户名 "${user?.username || ''}" 确认删除`}
          rules={[
            { required: true, message: '请输入用户名确认' },
            {
              validator(_, value) {
                if (value === user?.username) return Promise.resolve();
                return Promise.reject(new Error('用户名不匹配'));
              },
            },
          ]}
        >
          <Input placeholder={`输入 ${user?.username || ''} 确认`} />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Button onClick={onClose} style={{ marginRight: 8 }}>取消</Button>
          <Button type="primary" danger htmlType="submit" loading={loading}>
            确认删除
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
