import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, DatePicker, Select, Input,
  Space, message, Popconfirm, Tag, Badge,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, PhoneOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { appointmentApi, taskApi } from '../api'

const TIME_SLOTS = [
  '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
  '14:00-15:00', '15:00-16:00', '16:00-17:00',
]
const TIME_OPTIONS = TIME_SLOTS.map(s => ({ label: s, value: s }))

export default function Appointment() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(false)
  const [filterDate, setFilterDate] = useState(null)
  const [pendingTransfers, setPendingTransfers] = useState([])
  const [pendingLoading, setPendingLoading] = useState(false)
  const [createModal, setCreateModal] = useState(false)
  const [editModal, setEditModal] = useState({ open: false, record: null })
  const [submitLoading, setSubmitLoading] = useState(false)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  const loadAppointments = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filterDate) {
        params.start_date = filterDate.format('YYYY-MM-DD')
        params.end_date = filterDate.format('YYYY-MM-DD')
      }
      const res = await appointmentApi.list({ ...params, size: 100 })
      setAppointments(Array.isArray(res.data) ? res.data : [])
    } catch {
      message.error('加载预约失败')
    } finally {
      setLoading(false)
    }
  }

  const loadPendingTransfers = async () => {
    setPendingLoading(true)
    try {
      const res = await taskApi.pendingTransfers()
      setPendingTransfers(Array.isArray(res.data) ? res.data : [])
    } catch {
      // 静默失败
    } finally {
      setPendingLoading(false)
    }
  }

  useEffect(() => {
    loadAppointments()
    loadPendingTransfers()
  }, [filterDate])

  const handleCreate = async (values) => {
    setSubmitLoading(true)
    try {
      await appointmentApi.create({
        patient_id: Number(values.patient_id),
        task_id: values.task_id ? Number(values.task_id) : null,
        appointment_date: values.appointment_date.format('YYYY-MM-DD'),
        appointment_time: values.appointment_time,
        operator: values.operator,
      })
      message.success('预约已创建')
      setCreateModal(false)
      createForm.resetFields()
      loadAppointments()
      loadPendingTransfers()
    } catch (e) {
      message.error(e.response?.data?.detail || '创建失败')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleEdit = async (values) => {
    setSubmitLoading(true)
    try {
      await appointmentApi.update(editModal.record.id, {
        appointment_date: values.appointment_date.format('YYYY-MM-DD'),
        appointment_time: values.appointment_time,
        operator: values.operator,
      })
      message.success('已更新')
      setEditModal({ open: false, record: null })
      loadAppointments()
    } catch {
      message.error('更新失败')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await appointmentApi.delete(id)
      message.success('已取消预约')
      loadAppointments()
    } catch {
      message.error('取消失败')
    }
  }

  const handleRegisterFromTransfer = (task) => {
    createForm.setFieldsValue({
      patient_id: task.patient_id,
      task_id: task.id,
      appointment_date: dayjs().add(1, 'day'),
    })
    setCreateModal(true)
  }

  const apptColumns = [
    { title: '姓名', dataIndex: 'patient_name', width: 90 },
    { title: '电话', dataIndex: 'patient_phone', width: 130 },
    {
      title: '预约日期', dataIndex: 'appointment_date', width: 120,
      render: v => v ? <Tag color="blue">{v}</Tag> : '-',
    },
    {
      title: '时间段', dataIndex: 'appointment_time', width: 130,
      render: v => v ? <Tag color="green">{v}</Tag> : '-',
    },
    { title: '操作人', dataIndex: 'operator', width: 90, render: v => v || '-' },
    {
      title: '创建时间', dataIndex: 'created_at', width: 140,
      render: v => v?.slice(0, 16) || '-',
    },
    {
      title: '操作', key: 'action', width: 130,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setEditModal({ open: true, record })
              editForm.setFieldsValue({
                ...record,
                appointment_date: record.appointment_date ? dayjs(record.appointment_date) : null,
              })
            }}
          >修改</Button>
          <Popconfirm title="确认取消此预约？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>取消</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const transferColumns = [
    { title: '姓名', dataIndex: 'patient_name', width: 90 },
    { title: '电话', dataIndex: 'patient_phone', width: 130 },
    {
      title: '转接时间', dataIndex: 'called_at', width: 150,
      render: v => v?.slice(0, 16) || '-',
    },
    {
      title: '操作', key: 'action', width: 120,
      render: (_, record) => (
        <Button
          size="small"
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => handleRegisterFromTransfer(record)}
        >登记预约</Button>
      ),
    },
  ]

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 待跟进转接 */}
      {pendingTransfers.length > 0 && (
        <Card
          title={
            <span>
              <PhoneOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
              待跟进预约
              <Badge count={pendingTransfers.length} style={{ marginLeft: 8 }} />
            </span>
          }
          style={{ border: '1px solid #ff4d4f' }}
          styles={{ header: { backgroundColor: '#fff2f0' } }}
          extra={<Button size="small" onClick={loadPendingTransfers}>刷新</Button>}
        >
          <Table
            dataSource={pendingTransfers}
            columns={transferColumns}
            rowKey="id"
            loading={pendingLoading}
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* 预约列表 */}
      <Card
        title="预约列表"
        extra={
          <Space>
            <DatePicker
              placeholder="按日期筛选"
              value={filterDate}
              onChange={setFilterDate}
              allowClear
            />
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => { createForm.resetFields(); setCreateModal(true) }}
            >
              新建预约
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={appointments}
          columns={apptColumns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: t => `共 ${t} 条预约` }}
          size="middle"
        />
      </Card>

      {/* 新建预约弹窗 */}
      <Modal
        title="新建预约"
        open={createModal}
        onCancel={() => setCreateModal(false)}
        footer={null}
        width={460}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="patient_id" label="老人 ID" rules={[{ required: true, message: '请填写老人ID' }]}>
            <Input type="number" placeholder="老人ID（可在号码管理中查看）" />
          </Form.Item>
          <Form.Item name="task_id" label="关联任务ID（可选）">
            <Input type="number" placeholder="拨打任务ID（可留空）" />
          </Form.Item>
          <Form.Item
            name="appointment_date"
            label="预约日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker
              style={{ width: '100%' }}
              disabledDate={d => d < dayjs().startOf('day')}
            />
          </Form.Item>
          <Form.Item
            name="appointment_time"
            label="预约时间段"
            rules={[{ required: true, message: '请选择时间段' }]}
          >
            <Select placeholder="选择时间段" options={TIME_OPTIONS} />
          </Form.Item>
          <Form.Item name="operator" label="操作人员">
            <Input placeholder="客服姓名（可选）" />
          </Form.Item>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button onClick={() => setCreateModal(false)}>取消</Button>
            <Button type="primary" htmlType="submit" loading={submitLoading}>确认登记</Button>
          </div>
        </Form>
      </Modal>

      {/* 修改预约弹窗 */}
      <Modal
        title="修改预约"
        open={editModal.open}
        onCancel={() => setEditModal({ open: false, record: null })}
        footer={null}
        width={460}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical" onFinish={handleEdit} style={{ marginTop: 16 }}>
          <Form.Item name="appointment_date" label="预约日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="appointment_time" label="预约时间段" rules={[{ required: true }]}>
            <Select options={TIME_OPTIONS} />
          </Form.Item>
          <Form.Item name="operator" label="操作人员">
            <Input />
          </Form.Item>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <Button onClick={() => setEditModal({ open: false, record: null })}>取消</Button>
            <Button type="primary" htmlType="submit" loading={submitLoading}>保存</Button>
          </div>
        </Form>
      </Modal>
    </Space>
  )
}
