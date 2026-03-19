import { useState, useEffect } from 'react'
import {
  Card, Radio, Input, Button, Table, message, Space,
  Tag, Divider, Statistic, Row, Col, Popconfirm,
} from 'antd'
import {
  PlayCircleOutlined, PlusOutlined, TeamOutlined,
} from '@ant-design/icons'
import { taskApi, patientApi } from '../api'

const STATUS_COLOR = {
  pending: 'default', calling: 'processing', accepted: 'success',
  rejected: 'error', no_answer: 'warning', to_schedule: 'cyan',
  transferred: 'purple', failed: 'red',
}
const STATUS_LABEL = {
  pending: '待拨打', calling: '拨打中', accepted: '同意', rejected: '拒绝',
  no_answer: '未接通', to_schedule: '待约', transferred: '已转人工', failed: '失败',
}

export default function TaskCreate() {
  const [mode, setMode] = useState('all')       // all | community | select
  const [community, setCommunity] = useState('')
  const [selectedIds, setSelectedIds] = useState([])
  const [patients, setPatients] = useState([])
  const [patientLoading, setPatientLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [batches, setBatches] = useState([])
  const [batchesLoading, setBatchesLoading] = useState(false)

  const loadPatients = async (kw) => {
    setPatientLoading(true)
    try {
      const res = await patientApi.list({ keyword: kw || undefined, size: 200 })
      setPatients(Array.isArray(res.data) ? res.data : [])
    } catch {
      message.error('加载老人列表失败')
    } finally {
      setPatientLoading(false)
    }
  }

  const loadBatches = async () => {
    setBatchesLoading(true)
    try {
      const res = await taskApi.listBatches()
      setBatches(res.data || [])
    } catch {
      message.error('加载批次列表失败')
    } finally {
      setBatchesLoading(false)
    }
  }

  useEffect(() => {
    loadBatches()
  }, [])

  useEffect(() => {
    if (mode === 'select') loadPatients()
    if (mode === 'community' && community) loadPatients(community)
  }, [mode])

  const handleCreate = async () => {
    const payload = {}
    if (mode === 'community') {
      if (!community.trim()) { message.warning('请输入社区名称'); return }
      payload.community = community.trim()
    } else if (mode === 'select') {
      if (selectedIds.length === 0) { message.warning('请至少选择一位老人'); return }
      payload.patient_ids = selectedIds
    }

    setCreating(true)
    try {
      const res = await taskApi.create(payload)
      message.success(res.data.message)
      loadBatches()
      setSelectedIds([])
    } catch (e) {
      message.error(e.response?.data?.detail || '创建失败')
    } finally {
      setCreating(false)
    }
  }

  const handleStart = async (batchId) => {
    try {
      const res = await taskApi.start(batchId)
      message.success(res.data.message)
      loadBatches()
    } catch (e) {
      message.error(e.response?.data?.detail || '启动失败')
    }
  }

  const handlePause = async (batchId) => {
    try {
      await taskApi.pause(batchId)
      message.success('已暂停')
      loadBatches()
    } catch {
      message.error('暂停失败')
    }
  }

  const patientColumns = [
    { title: '姓名', dataIndex: 'name', width: 100 },
    { title: '电话', dataIndex: 'phone' },
    { title: '年龄', dataIndex: 'age', width: 70, render: v => v ? `${v}岁` : '-' },
    { title: '社区', dataIndex: 'community' },
  ]

  const batchColumns = [
    { title: '批次ID', dataIndex: 'batch_id', ellipsis: true },
    { title: '总计', dataIndex: 'total', width: 70 },
    {
      title: '进度', key: 'progress',
      render: (_, r) => {
        const done = r.accepted + r.rejected + r.no_answer + r.to_schedule + r.transferred + r.failed
        const pct = r.total ? Math.round(done / r.total * 100) : 0
        return <span>{done}/{r.total} ({pct}%)</span>
      }
    },
    { title: '接通', dataIndex: 'transferred', width: 60, render: (v, r) => r.accepted + r.rejected + r.to_schedule + r.transferred },
    { title: '同意', dataIndex: 'to_schedule', width: 60, render: (v, r) => r.accepted + r.to_schedule + r.transferred },
    { title: '拒绝', dataIndex: 'rejected', width: 60 },
    { title: '未接', dataIndex: 'no_answer', width: 60 },
    {
      title: '创建时间', dataIndex: 'created_at', width: 120,
      render: v => v?.slice(0, 16),
    },
    {
      title: '操作', key: 'action', width: 180,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleStart(record.batch_id)}
          >启动</Button>
          <Button size="small" onClick={() => handlePause(record.batch_id)}>暂停</Button>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 创建任务卡片 */}
      <Card title={<><PlusOutlined /> 创建拨打任务</>}>
        <div style={{ marginBottom: 16 }}>
          <span style={{ marginRight: 12, fontWeight: 500 }}>拨打范围：</span>
          <Radio.Group value={mode} onChange={e => { setMode(e.target.value); setSelectedIds([]) }}>
            <Radio.Button value="all">全部老人</Radio.Button>
            <Radio.Button value="community">按社区</Radio.Button>
            <Radio.Button value="select">手动勾选</Radio.Button>
          </Radio.Group>
        </div>

        {mode === 'community' && (
          <Space style={{ marginBottom: 16 }}>
            <Input
              placeholder="输入社区名称"
              style={{ width: 220 }}
              value={community}
              onChange={e => setCommunity(e.target.value)}
            />
            <Button onClick={() => loadPatients(community)}>预览名单</Button>
          </Space>
        )}

        {mode === 'select' && (
          <Table
            dataSource={patients}
            columns={patientColumns}
            rowKey="id"
            loading={patientLoading}
            rowSelection={{
              selectedRowKeys: selectedIds,
              onChange: setSelectedIds,
            }}
            pagination={{ pageSize: 10, showTotal: t => `共 ${t} 人` }}
            size="small"
            style={{ marginBottom: 16 }}
          />
        )}

        {mode === 'community' && patients.length > 0 && (
          <div style={{ color: '#888', marginBottom: 12 }}>
            预览：找到 <strong>{patients.length}</strong> 位老人
          </div>
        )}

        <Button
          type="primary"
          size="large"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          loading={creating}
        >
          创建批次任务
        </Button>
      </Card>

      {/* 历史批次 */}
      <Card title={<><TeamOutlined /> 历史批次</>} extra={<Button size="small" onClick={loadBatches}>刷新</Button>}>
        <Table
          dataSource={batches}
          columns={batchColumns}
          rowKey="batch_id"
          loading={batchesLoading}
          pagination={{ pageSize: 10, showTotal: t => `共 ${t} 个批次` }}
          size="middle"
        />
      </Card>
    </Space>
  )
}
