import { useState, useEffect, useRef } from 'react'
import {
  Table, Button, Input, Space, Modal, Form,
  Upload, message, Popconfirm, Card, Tag,
} from 'antd'
import {
  UploadOutlined, EditOutlined, DeleteOutlined,
} from '@ant-design/icons'
import { patientApi } from '../api'

const PAGE_SIZE = 20

export default function PatientList() {
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [editModal, setEditModal] = useState({ open: false, record: null })
  const [importModal, setImportModal] = useState(false)
  const [importLoading, setImportLoading] = useState(false)
  const [form] = Form.useForm()
  const keywordRef = useRef(keyword)
  keywordRef.current = keyword

  const load = async (kw = keyword, pg = page) => {
    setLoading(true)
    try {
      const res = await patientApi.list({ keyword: kw || undefined, page: pg, size: PAGE_SIZE })
      setPatients(Array.isArray(res.data) ? res.data : [])
      setTotal(parseInt(res.headers['x-total-count'] || '0', 10))
    } catch {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(keyword, page) }, [keyword, page])

  const handleDelete = async (id) => {
    try {
      await patientApi.delete(id)
      message.success('已删除')
      load()
    } catch {
      message.error('删除失败')
    }
  }

  const handleEditSubmit = async (values) => {
    try {
      await patientApi.update(editModal.record.id, values)
      message.success('已保存')
      setEditModal({ open: false, record: null })
      load()
    } catch {
      message.error('保存失败')
    }
  }

  const handleImport = async (file) => {
    setImportLoading(true)
    try {
      const res = await patientApi.import(file)
      const { success, failed, errors } = res.data
      if (errors.length > 0) {
        Modal.info({
          title: `导入完成：成功 ${success} 条，失败 ${failed} 条`,
          content: (
            <div style={{ maxHeight: 240, overflow: 'auto', marginTop: 8 }}>
              {errors.map((e, i) => (
                <div key={i} style={{ color: '#ff4d4f', fontSize: 12 }}>{e}</div>
              ))}
            </div>
          ),
        })
      } else {
        message.success(`成功导入 ${success} 条`)
      }
      setImportModal(false)
      load()
    } catch {
      message.error('导入失败，请检查文件格式')
    } finally {
      setImportLoading(false)
    }
    return false // 阻止 antd Upload 自动上传
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 64 },
    { title: '姓名', dataIndex: 'name', width: 100 },
    { title: '电话', dataIndex: 'phone', width: 140 },
    {
      title: '年龄', dataIndex: 'age', width: 70,
      render: (v) => v ? <Tag color="blue">{v}岁</Tag> : '-',
    },
    { title: '社区', dataIndex: 'community', ellipsis: true },
    {
      title: '录入时间', dataIndex: 'created_at', width: 120,
      render: (v) => v?.slice(0, 10),
    },
    {
      title: '操作', key: 'action', width: 140,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setEditModal({ open: true, record })
              form.setFieldsValue(record)
            }}
          >编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="号码管理"
        extra={
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setImportModal(true)}>
            导入 Excel
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="搜索姓名或社区"
            allowClear
            style={{ width: 260 }}
            onSearch={(v) => { setPage(1); setKeyword(v) }}
          />
          <span style={{ color: '#888' }}>共 {total} 人</span>
        </Space>
        <Table
          dataSource={patients}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            onChange: setPage,
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
          }}
          size="middle"
        />
      </Card>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑老人信息"
        open={editModal.open}
        onOk={() => form.submit()}
        onCancel={() => setEditModal({ open: false, record: null })}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={handleEditSubmit} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="电话" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="age" label="年龄">
            <Input type="number" min={0} max={150} />
          </Form.Item>
          <Form.Item name="community" label="社区">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入弹窗 */}
      <Modal
        title="批量导入老人信息"
        open={importModal}
        footer={null}
        onCancel={() => setImportModal(false)}
      >
        <div style={{ color: '#888', fontSize: 13, marginBottom: 16 }}>
          Excel 格式要求：第1列姓名、第2列电话、第3列年龄（可选）、第4列社区（可选），第1行为表头
        </div>
        <Upload
          accept=".xlsx,.xls,.csv"
          beforeUpload={handleImport}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />} loading={importLoading} type="primary">
            选择文件并上传
          </Button>
        </Upload>
      </Modal>
    </>
  )
}
