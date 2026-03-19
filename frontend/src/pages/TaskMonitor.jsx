import { useState, useEffect, useRef } from 'react'
import {
  Card, Select, Row, Col, Statistic, Progress, Button,
  Table, Tag, Space, message, Badge, Empty,
} from 'antd'
import {
  PauseCircleOutlined, PlayCircleOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { taskApi } from '../api'

const STATUS_COLOR = {
  pending: 'default', calling: 'processing', accepted: 'success',
  rejected: 'error', no_answer: 'warning', to_schedule: 'cyan',
  transferred: 'purple', failed: 'red',
}
const STATUS_LABEL = {
  pending: '待拨打', calling: '拨打中', accepted: '同意体检', rejected: '拒绝体检',
  no_answer: '未接/无响应', to_schedule: '同意待约', transferred: '已转人工', failed: '拨打失败',
}

export default function TaskMonitor() {
  const [batches, setBatches] = useState([])
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [stats, setStats] = useState(null)
  const [detail, setDetail] = useState([])
  const [loadingStats, setLoadingStats] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const timerRef = useRef(null)

  const loadBatches = async () => {
    try {
      const res = await taskApi.listBatches()
      const list = res.data || []
      setBatches(list)
      if (!selectedBatch && list.length > 0) {
        setSelectedBatch(list[0].batch_id)
      }
    } catch {
      message.error('加载批次失败')
    }
  }

  const loadStats = async (batchId) => {
    if (!batchId) return
    setLoadingStats(true)
    try {
      const res = await taskApi.getBatchStats(batchId)
      setStats(res.data)
    } catch {
      message.error('加载统计失败')
    } finally {
      setLoadingStats(false)
    }
  }

  const loadDetail = async (batchId) => {
    if (!batchId) return
    setLoadingDetail(true)
    try {
      const res = await taskApi.getBatchDetail(batchId)
      setDetail(res.data || [])
    } catch {
      message.error('加载明细失败')
    } finally {
      setLoadingDetail(false)
    }
  }

  useEffect(() => {
    loadBatches()
  }, [])

  useEffect(() => {
    if (!selectedBatch) return
    loadStats(selectedBatch)
    loadDetail(selectedBatch)

    // 自动刷新：每 10 秒更新一次
    clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      loadStats(selectedBatch)
      loadDetail(selectedBatch)
    }, 10000)
    return () => clearInterval(timerRef.current)
  }, [selectedBatch])

  const handlePause = async () => {
    try {
      await taskApi.pause(selectedBatch)
      message.success('已暂停')
    } catch {
      message.error('暂停失败')
    }
  }

  const handleResume = async () => {
    try {
      await taskApi.resume(selectedBatch)
      message.success('已恢复')
    } catch {
      message.error('恢复失败')
    }
  }

  const finished = stats
    ? stats.accepted + stats.rejected + stats.no_answer +
      stats.to_schedule + stats.transferred + stats.failed
    : 0
  const percent = stats?.total ? Math.round((finished / stats.total) * 100) : 0
  const connected = stats
    ? stats.accepted + stats.rejected + stats.to_schedule + stats.transferred
    : 0
  const connectRate = finished ? Math.round((connected / finished) * 100) : 0

  const detailColumns = [
    { title: '姓名', dataIndex: 'patient_name', width: 90 },
    { title: '电话', dataIndex: 'patient_phone', width: 130 },
    {
      title: '状态', dataIndex: 'status', width: 110,
      render: (v) => (
        <Tag color={STATUS_COLOR[v] || 'default'}>{STATUS_LABEL[v] || v}</Tag>
      ),
    },
    { title: '拨打次数', dataIndex: 'call_count', width: 80 },
    { title: '按键', dataIndex: 'key_pressed', width: 70, render: v => v || '-' },
    { title: '是否转人工', dataIndex: 'transferred', width: 90, render: v => v ? <Tag color="purple">是</Tag> : '否' },
    {
      title: '最近拨打', dataIndex: 'called_at', width: 140,
      render: v => v?.slice(0, 16) || '-',
    },
    { title: '备注', dataIndex: 'notes', ellipsis: true, render: v => v || '-' },
  ]

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 批次选择 */}
      <Card size="small">
        <Space wrap>
          <span style={{ fontWeight: 500 }}>选择批次：</span>
          <Select
            style={{ width: 320 }}
            placeholder="请选择批次"
            value={selectedBatch}
            onChange={setSelectedBatch}
            options={batches.map(b => ({
              label: `${b.batch_id}（${b.total}人，${b.created_at?.slice(0, 16)}）`,
              value: b.batch_id,
            }))}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => { loadStats(selectedBatch); loadDetail(selectedBatch) }}
            loading={loadingStats}
          >刷新</Button>
          <Button icon={<PauseCircleOutlined />} onClick={handlePause} disabled={!selectedBatch}>
            暂停
          </Button>
          <Button icon={<PlayCircleOutlined />} type="primary" onClick={handleResume} disabled={!selectedBatch}>
            恢复
          </Button>
        </Space>
      </Card>

      {/* 进度统计 */}
      {stats ? (
        <>
          <Card title="拨打进度">
            <Progress
              percent={percent}
              status={percent === 100 ? 'success' : 'active'}
              format={p => `${p}% (${finished}/${stats.total})`}
              style={{ marginBottom: 24 }}
            />
            <Row gutter={16}>
              <Col span={4}>
                <Statistic title="总计" value={stats.total} />
              </Col>
              <Col span={4}>
                <Statistic title="待拨打" value={stats.pending} valueStyle={{ color: '#888' }} />
              </Col>
              <Col span={4}>
                <Statistic title="已接通" value={connected} valueStyle={{ color: '#1677ff' }} />
              </Col>
              <Col span={4}>
                <Statistic
                  title="接通率"
                  value={connectRate}
                  suffix="%"
                  valueStyle={{ color: connectRate >= 60 ? '#52c41a' : '#faad14' }}
                />
              </Col>
              <Col span={4}>
                <Statistic title="未接/无响应" value={stats.no_answer} valueStyle={{ color: '#faad14' }} />
              </Col>
              <Col span={4}>
                <Statistic title="拨打失败" value={stats.failed} valueStyle={{ color: '#ff4d4f' }} />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Statistic title="同意体检" value={stats.accepted + stats.to_schedule + stats.transferred} valueStyle={{ color: '#52c41a' }} />
              </Col>
              <Col span={6}>
                <Statistic title="已转人工预约" value={stats.transferred} valueStyle={{ color: '#722ed1' }} />
              </Col>
              <Col span={6}>
                <Statistic title="同意待约" value={stats.to_schedule} valueStyle={{ color: '#13c2c2' }} />
              </Col>
              <Col span={6}>
                <Statistic title="拒绝体检" value={stats.rejected} valueStyle={{ color: '#ff4d4f' }} />
              </Col>
            </Row>
          </Card>

          {/* 明细表格 */}
          <Card title="拨打明细" extra={<span style={{ color: '#888', fontSize: 12 }}>每10秒自动刷新</span>}>
            <Table
              dataSource={detail}
              columns={detailColumns}
              rowKey="id"
              loading={loadingDetail}
              pagination={{ pageSize: 20, showTotal: t => `共 ${t} 条` }}
              size="small"
            />
          </Card>
        </>
      ) : (
        <Card>
          <Empty description="请选择批次查看监控数据" />
        </Card>
      )}
    </Space>
  )
}
