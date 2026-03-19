import { useEffect, useRef, useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Layout, Menu, Modal, Form, DatePicker, Select, Input,
  Button, Descriptions, message, Badge,
} from 'antd'
import {
  TeamOutlined, PhoneOutlined, MonitorOutlined,
  BarChartOutlined, CalendarOutlined, BellOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { taskApi, appointmentApi } from '../api'

const { Sider, Header, Content } = Layout

const menuItems = [
  { key: '/patients',      icon: <TeamOutlined />,      label: '号码管理' },
  { key: '/tasks/create',  icon: <PhoneOutlined />,     label: '发起任务' },
  { key: '/tasks/monitor', icon: <MonitorOutlined />,   label: '任务监控' },
  { key: '/report',        icon: <BarChartOutlined />,  label: '结果报表' },
  { key: '/appointments',  icon: <CalendarOutlined />,  label: '预约管理' },
]

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [form] = Form.useForm()

  // 弹屏：待处理的转接任务
  const [pendingTransfers, setPendingTransfers] = useState([])
  const [popupTask, setPopupTask] = useState(null)
  const [popupOpen, setPopupOpen] = useState(false)
  const [popupSubmitting, setPopupSubmitting] = useState(false)
  const seenIds = useRef(new Set())

  // 每 6 秒轮询一次待转接任务
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await taskApi.pendingTransfers()
        const tasks = res.data || []
        // 找出首个未弹过的任务
        const newTask = tasks.find((t) => !seenIds.current.has(t.id))
        if (newTask && !popupOpen) {
          seenIds.current.add(newTask.id)
          setPopupTask(newTask)
          setPopupOpen(true)
          form.resetFields()
        }
        setPendingTransfers(tasks)
      } catch (_) {
        // 静默失败，不影响正常使用
      }
    }
    poll()
    const timer = setInterval(poll, 6000)
    return () => clearInterval(timer)
  }, [popupOpen])

  const handlePopupSubmit = async (values) => {
    setPopupSubmitting(true)
    try {
      await appointmentApi.create({
        patient_id: popupTask.patient_id,
        task_id: popupTask.id,
        appointment_date: values.appointment_date.format('YYYY-MM-DD'),
        appointment_time: values.appointment_time,
        operator: values.operator,
      })
      message.success('预约已登记')
      setPopupOpen(false)
      setPopupTask(null)
    } catch (e) {
      message.error('登记失败，请重试')
    } finally {
      setPopupSubmitting(false)
    }
  }

  const handlePopupSkip = () => {
    setPopupOpen(false)
    setPopupTask(null)
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="dark" style={{ position: 'fixed', height: '100vh', left: 0 }}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 'bold', fontSize: 14, borderBottom: '1px solid #333',
          padding: '0 12px', textAlign: 'center', lineHeight: '1.4',
        }}>
          体检预约<br />IVR系统
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout style={{ marginLeft: 200 }}>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0', position: 'sticky', top: 0, zIndex: 100,
        }}>
          <span style={{ fontSize: 18, fontWeight: 600, color: '#1677ff' }}>
            老年人体检预约 IVR 自动外呼系统
          </span>
          <Badge count={pendingTransfers.length} offset={[-4, 4]}>
            <Button
              icon={<BellOutlined />}
              type={pendingTransfers.length > 0 ? 'primary' : 'default'}
              onClick={() => navigate('/appointments')}
            >
              待跟进预约 {pendingTransfers.length > 0 ? `(${pendingTransfers.length})` : ''}
            </Button>
          </Badge>
        </Header>

        <Content style={{ margin: 24, minHeight: 'calc(100vh - 112px)' }}>
          <Outlet />
        </Content>
      </Layout>

      {/* 弹屏：客服填写预约 */}
      <Modal
        title={
          <span style={{ color: '#ff4d4f', fontSize: 16 }}>
            <BellOutlined style={{ marginRight: 8 }} />
            来电转接 — 请登记预约
          </span>
        }
        open={popupOpen}
        onCancel={handlePopupSkip}
        footer={null}
        maskClosable={false}
        width={480}
        zIndex={9999}
      >
        {popupTask && (
          <>
            <Descriptions bordered size="small" column={2} style={{ marginBottom: 20 }}>
              <Descriptions.Item label="姓名">{popupTask.patient_name}</Descriptions.Item>
              <Descriptions.Item label="电话">{popupTask.patient_phone}</Descriptions.Item>
            </Descriptions>

            <Form form={form} layout="vertical" onFinish={handlePopupSubmit}>
              <Form.Item
                name="appointment_date"
                label="预约日期"
                rules={[{ required: true, message: '请选择日期' }]}
              >
                <DatePicker style={{ width: '100%' }} disabledDate={(d) => d < dayjs().startOf('day')} />
              </Form.Item>
              <Form.Item
                name="appointment_time"
                label="预约时间段"
                rules={[{ required: true, message: '请选择时间段' }]}
              >
                <Select
                  placeholder="选择时间段"
                  options={[
                    { label: '08:00 - 09:00', value: '08:00-09:00' },
                    { label: '09:00 - 10:00', value: '09:00-10:00' },
                    { label: '10:00 - 11:00', value: '10:00-11:00' },
                    { label: '11:00 - 12:00', value: '11:00-12:00' },
                    { label: '14:00 - 15:00', value: '14:00-15:00' },
                    { label: '15:00 - 16:00', value: '15:00-16:00' },
                    { label: '16:00 - 17:00', value: '16:00-17:00' },
                  ]}
                />
              </Form.Item>
              <Form.Item name="operator" label="操作人员">
                <Input placeholder="客服姓名（可选）" />
              </Form.Item>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <Button onClick={handlePopupSkip}>稍后处理</Button>
                <Button type="primary" htmlType="submit" loading={popupSubmitting}>
                  确认登记预约
                </Button>
              </div>
            </Form>
          </>
        )}
      </Modal>
    </Layout>
  )
}
