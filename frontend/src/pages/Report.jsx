import { useState, useEffect } from 'react'
import {
  Card, Select, Row, Col, Statistic, Button, Table,
  Tag, Space, message, Empty,
} from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { taskApi, statsApi } from '../api'

const PIE_COLORS = {
  transferred: '#722ed1',
  accepted:    '#52c41a',
  to_schedule: '#13c2c2',
  rejected:    '#ff4d4f',
  no_answer:   '#faad14',
  pending:     '#d9d9d9',
  calling:     '#1677ff',
  failed:      '#ff7875',
}
const STATUS_LABEL = {
  accepted: '同意体检', rejected: '拒绝体检', no_answer: '未接/无响应',
  to_schedule: '同意待约', transferred: '已转人工', pending: '待拨打',
  calling: '拨打中', failed: '拨打失败',
}

export default function Report() {
  const [batches, setBatches] = useState([])
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [stats, setStats] = useState(null)
  const [detail, setDetail] = useState([])
  const [loadingStats, setLoadingStats] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const loadBatches = async () => {
    try {
      const res = await taskApi.listBatches()
      const list = res.data || []
      setBatches(list)
      if (list.length > 0 && !selectedBatch) setSelectedBatch(list[0].batch_id)
    } catch {
      message.error('加载批次失败')
    }
  }

  const loadReport = async (batchId) => {
    if (!batchId) return
    setLoadingStats(true)
    setLoadingDetail(true)
    try {
      const [statsRes, detailRes] = await Promise.all([
        statsApi.batch(batchId),
        taskApi.getBatchDetail(batchId),
      ])
      setStats(statsRes.data)
      setDetail(detailRes.data || [])
    } catch {
      message.error('加载报表失败')
    } finally {
      setLoadingStats(false)
      setLoadingDetail(false)
    }
  }

  useEffect(() => { loadBatches() }, [])
  useEffect(() => { if (selectedBatch) loadReport(selectedBatch) }, [selectedBatch])

  // 饼图数据
  const pieData = stats
    ? Object.entries({
        transferred: stats.transferred,
        to_schedule: stats.to_schedule,
        accepted:    stats.accepted,
        rejected:    stats.rejected,
        no_answer:   stats.no_answer,
        failed:      stats.failed,
        pending:     stats.pending,
      })
        .filter(([, v]) => v > 0)
        .map(([k, v]) => ({ name: STATUS_LABEL[k] || k, value: v, key: k }))
    : []

  const connected = stats
    ? stats.accepted + stats.rejected + stats.to_schedule + stats.transferred
    : 0
  const acceptedTotal = stats
    ? stats.accepted + stats.to_schedule + stats.transferred
    : 0

  const detailColumns = [
    { title: '姓名', dataIndex: 'patient_name', width: 90 },
    { title: '电话', dataIndex: 'patient_phone', width: 130 },
    {
      title: '状态', dataIndex: 'status', width: 120,
      render: v => (
        <Tag color={PIE_COLORS[v] || 'default'}>{STATUS_LABEL[v] || v}</Tag>
      ),
    },
    { title: '拨打次数', dataIndex: 'call_count', width: 80 },
    { title: '按键记录', dataIndex: 'key_pressed', width: 80, render: v => v || '-' },
    { title: '是否转人工', dataIndex: 'transferred', width: 90, render: v => v ? '是' : '否' },
    { title: '最近拨打时间', dataIndex: 'called_at', width: 150, render: v => v?.slice(0, 16) || '-' },
    { title: '备注', dataIndex: 'notes', ellipsis: true, render: v => v || '-' },
  ]

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 批次选择 */}
      <Card size="small">
        <Space wrap>
          <span style={{ fontWeight: 500 }}>选择批次：</span>
          <Select
            style={{ width: 340 }}
            placeholder="请选择批次"
            value={selectedBatch}
            onChange={setSelectedBatch}
            options={batches.map(b => ({
              label: `${b.batch_id}（${b.total}人，${b.created_at?.slice(0, 16)}）`,
              value: b.batch_id,
            }))}
          />
          <Button icon={<ReloadOutlined />} onClick={() => loadReport(selectedBatch)} loading={loadingStats}>
            刷新
          </Button>
          {selectedBatch && (
            <Button
              icon={<DownloadOutlined />}
              type="primary"
              onClick={() => window.location.href = statsApi.exportUrl(selectedBatch)}
            >
              导出 Excel
            </Button>
          )}
        </Space>
      </Card>

      {stats ? (
        <>
          {/* 核心指标 */}
          <Row gutter={16}>
            {[
              { title: '总人数', value: stats.total },
              { title: '已拨打', value: connected + stats.no_answer + stats.failed },
              { title: '接通数', value: connected, color: '#1677ff' },
              { title: '接通率', value: stats.total ? `${Math.round(connected / stats.total * 100)}%` : '0%', color: '#1677ff' },
              { title: '同意体检', value: acceptedTotal, color: '#52c41a' },
              { title: '同意率', value: connected ? `${Math.round(acceptedTotal / connected * 100)}%` : '0%', color: '#52c41a' },
              { title: '已转人工', value: stats.transferred, color: '#722ed1' },
              { title: '拒绝体检', value: stats.rejected, color: '#ff4d4f' },
            ].map((item, i) => (
              <Col span={3} key={i}>
                <Card size="small">
                  <Statistic
                    title={item.title}
                    value={item.value}
                    valueStyle={item.color ? { color: item.color, fontSize: 20 } : { fontSize: 20 }}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          {/* 饼图 */}
          <Card title="拨打结果分布">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  dataKey="value"
                  label={({ name, value, percent }) =>
                    `${name}: ${value}人 (${(percent * 100).toFixed(1)}%)`
                  }
                  labelLine={false}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.key} fill={PIE_COLORS[entry.key] || '#ccc'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v, n) => [`${v} 人`, n]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* 明细表格 */}
          <Card
            title="拨打明细"
            extra={
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => window.location.href = statsApi.exportUrl(selectedBatch)}
              >
                导出 Excel
              </Button>
            }
          >
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
        <Card><Empty description="请选择批次查看报表" /></Card>
      )}
    </Space>
  )
}
