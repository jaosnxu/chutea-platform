import React, { useState, useRef, useEffect } from 'react'
import { USERS } from './data'

const API = 'https://chutea-platform.onrender.com'

export default function App() {
  const [contracts, setContracts] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [view, setView] = useState('empty')
  const [results, setResults] = useState([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selections, setSelections] = useState({})
  const [notes, setNotes] = useState({})
  const [contractText, setContractText] = useState('')
  const [file, setFile] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [approvalNodes, setApprovalNodes] = useState([
    { order: 1, node_type: 'approver', approver_id: 'awan', approver_name: '阿万' },
    { order: 2, node_type: 'approver', approver_id: 'jason', approver_name: 'Jason' },
    { order: 3, node_type: 'cc', approver_id: 'ceo', approver_name: 'CEO' },
  ])
  const [approvalInst, setApprovalInst] = useState(null)
  const [currentUserId] = useState('awan')
  const [rejectReason, setRejectReason] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const leftRef = useRef(null)
  const contractTextRef = useRef('')

  useEffect(() => {
    fetch(API + '/api/contracts/list').then(r => r.json()).then(data => {
      if (Array.isArray(data) && data.length > 0) setContracts(data)
    }).catch(() => { })
  }, [])

  const saveContract = () => {
    if (!activeId) return
    const c = contracts.find(c => c.id === activeId)
    if (!c) return
    fetch(API + '/api/contracts/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: String(activeId), name: c.name, content: contractTextRef.current, status: view, selections, notes, approval_status: c.approval_status || '', approval_id: c.approval_id || '' }) }).catch(() => { })
  }

  const handleNewContract = () => {
    const id = Date.now()
    setContracts([...contracts, { id, name: 'Новый договор', approval_status: null }])
    setActiveId(id); setView('upload'); setContractText(''); setFile(null); setError('')
  }

  const handleSubmit = async () => {
    const text = contractTextRef.current
    if (!text && !file) return
    setLoading(true); setError(''); setView('analyzing')
    try {
      const res = await fetch(API + '/api/contracts/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, filename: file?.name || '' })
      })
      const data = await res.json()
      if (data.error) { setError(data.error); setView('upload'); setLoading(false); return }
      setResults(data.clauses || [])
      setCurrentIdx(0)
      setSelections({})
      setNotes({})
      setView('clauses')
    } catch (e) {
      setError('Ошибка соединения с сервером'); setView('upload')
    }
    setLoading(false)
  }

  const handleConfirm = () => {
    const clause = results[currentIdx]
    if (!clause || !selections[clause.id]) return
    if (currentIdx < results.length - 1) { setCurrentIdx(currentIdx + 1); saveContract() }
    else handleSendApproval()
  }

  const handleSendApproval = () => {
    fetch(API + '/api/approvals/templates', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: 'default', name: '默认审批流', nodes: approvalNodes, method: 'sequential', timeout_hours: 48 }) })
      .then(() => fetch(API + '/api/approvals/instances', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ template_id: 'default', business_type: 'contract_review', business_id: String(activeId || Date.now()), created_by: 'awan' }) }))
      .then(r => r.json()).then(d => { setApprovalInst(d); setView('approval'); saveContract(); setContracts(prev => prev.map(c => c.id === activeId ? { ...c, approval_status: d.status, approval_id: d.id } : c)) })
  }

  const handleApprove = () => {
    if (!approvalInst) return
    fetch(API + '/api/approvals/instances/' + approvalInst.id + '/action', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ instance_id: approvalInst.id, action: 'approve', user_id: currentUserId }) })
      .then(r => r.json()).then(d => { setApprovalInst(d); setContracts(prev => prev.map(c => c.approval_id === d.id ? { ...c, approval_status: d.status } : c)) })
  }

  const handleReject = () => {
    if (!approvalInst || !rejectReason) return
    fetch(API + '/api/approvals/instances/' + approvalInst.id + '/action', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ instance_id: approvalInst.id, action: 'reject', user_id: currentUserId, comment: rejectReason }) })
      .then(r => r.json()).then(d => { setApprovalInst(d); setRejectReason(''); setContracts(prev => prev.map(c => c.approval_id === d.id ? { ...c, approval_status: d.status } : c)) })
  }

  function makeHighlightedText(fullText, clauseId) {
    if (!clauseId || !fullText) return fullText
    const escaped = clauseId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp('(' + escaped + '\\.[^\\n]*(?:\\n(?!\\d+\\.)[^\\n]*)*)', 'i')
    const m = fullText.match(regex)
    if (!m) return fullText
    return [fullText.substring(0, m.index), <span key="hl" className="highlight-yellow">{m[0]}</span>, fullText.substring(m.index + m[0].length)]
  }

  const active = contracts.find(c => c.id === activeId)
  const clause = results[currentIdx]
  const sel = clause ? selections[clause.id] : null
  const isLast = results.length > 0 && currentIdx === results.length - 1
  const highCount = results.filter(r => r.risk === 'high').length
  const medCount = results.filter(r => r.risk === 'med').length

  return (
    <div className="app">
      <div className="sidebar">
        <div className="logo">CHUTEA</div>
        <button className="add-btn" onClick={handleNewContract}>+ Добавить договор</button>
        <div className="contract-list">
          {contracts.map(c => {
            const badged = c.approval_status === 'approved' ? 'approved' : (c.approval_status === 'in_progress' || c.approval_status === 'pending') ? 'reviewing' : ''
            return (
              <div key={c.id} className={'contract-item' + (c.id === activeId ? ' active' : '')} onClick={() => { setActiveId(c.id); setView('upload'); setContractText(''); setFile(null); setError('') }}>
                <div>{c.name}</div>
                {c.approval_status && <div className="meta"><span className={'badge ' + badged}>{c.approval_status === 'approved' ? 'Утверждён' : c.approval_status === 'in_progress' ? 'На проверке' : c.approval_status}</span></div>}
              </div>
            )
          })}
        </div>
        <div className="settings" onClick={() => setShowSettings(true)}>⚙️ Настройки</div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="main-header">
          <span>{active ? active.name : 'CHUTEA'}</span>
          {view === 'clauses' && <span className="stage-badge">1 проверка</span>}
          {view === 'approval' && <span className="stage-badge">Согласование</span>}
        </div>
        <div className="main">
          {(view === 'clauses' || view === 'approval') && (
            <div className="panel-left" ref={leftRef}>
              {view === 'clauses' && clause ? makeHighlightedText(contractText, clause.id) : contractText}
            </div>
          )}
          <div style={{ flex: 1, overflowY: 'auto', padding: (view === 'clauses' || view === 'approval') ? 24 : 0 }}>
            {!activeId && <div className="empty-state">Выберите или добавьте договор</div>}
            {activeId && view === 'upload' && (
              <div className="upload-area">
                <h3>Добавить договор</h3>
                <input type="file" accept=".pdf,.docx,.doc,.txt" onChange={e => setFile(e.target.files[0])} style={{ marginBottom: 4, fontSize: 14 }} />
                <div className="upload-or">— или —</div>
                <textarea className="textarea" placeholder="Вставьте полный текст договора..." value={contractText} onChange={e => { setContractText(e.target.value); contractTextRef.current = e.target.value }} />
                {error && <div style={{ color: '#dc2626', fontSize: 13, marginTop: 8 }}>{error}</div>}
                <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn btn-primary" onClick={handleSubmit} disabled={(!contractText && !file) || loading}>Отправить на AI анализ</button>
                </div>
              </div>
            )}
            {view === 'analyzing' && (
              <div className="progress-spinner"><div className="spinner" /><span>AI анализ...</span></div>
            )}
            {view === 'clauses' && clause && (
              <div>
                <div className="ai-card">
                  <h4>🤖 AI Анализ на основе ГК РФ 2026</h4>
                  <div style={{ fontSize: 13, lineHeight: 1.8 }}>
                    <span style={{ color: '#fecaca', fontWeight: 700 }}>🔴 {highCount} высокий</span> · {' '}
                    <span style={{ color: '#fde68a', fontWeight: 700 }}>🟡 {medCount} средний</span>
                  </div>
                </div>
                <div className="nav-row"><span className="counter">{currentIdx + 1} / {results.length}</span></div>
                <div className="clause-card">
                  <div className="clause-title">{clause.title}</div>
                  <div className="original-ru">{clause.original}</div>
                  <div className="ai-ru"><strong>Анализ (ГК РФ 2026): </strong>{clause.ai_analysis}</div>
                  <div className="option-row">
                    {['A', 'B', 'C'].map(opt => (
                      <div key={opt} className={'option-card' + (sel === opt ? ' selected' : '')} onClick={() => setSelections({ ...selections, [clause.id]: opt })}>
                        <div className={'opt-label ' + opt.toLowerCase()}>{opt === 'A' ? 'Вариант А — Максимальная защита' : opt === 'B' ? 'Вариант Б — Сбалансированный' : 'Вариант В — Позиция контрагента'}</div>
                        <div className="opt-text">{opt === 'A' ? clause.optionA : opt === 'B' ? clause.optionB : clause.optionC}</div>
                      </div>
                    ))}
                  </div>
                  <div className="user-note-box">
                    <label>📝 Ваше мнение (необязательно)</label>
                    <textarea placeholder="Ваши замечания..." value={notes[clause.id] || ''} onChange={e => setNotes({ ...notes, [clause.id]: e.target.value })} />
                  </div>
                  <div className="confirm-row">
                    <button className="btn btn-success" onClick={handleConfirm} disabled={!sel}>{isLast ? 'Завершить и отправить на согласование' : 'Подтвердить → Следующий пункт'}</button>
                  </div>
                </div>
              </div>
            )}
            {view === 'approval' && approvalInst && (
              <div className="approval-section">
                <div className="approval-header">
                  <h3>Цепочка согласования</h3>
                  <span className={'approval-status ' + approvalInst.status}>{approvalInst.status === 'approved' ? '✅ Утверждено' : approvalInst.status === 'rejected' ? '❌ Отклонено' : '⏳ На согласовании'}</span>
                </div>
                <div className="approval-steps">
                  {approvalNodes.map((n, i) => [i > 0 ? <span key={'a' + i} className="arrow">→</span> : null, <div key={n.order} className={'approval-step' + (approvalInst.status === 'approved' && i < approvalInst.current_step ? ' done' : approvalInst.status === 'rejected' && i === 0 ? ' rejected' : i === approvalInst.current_step ? ' current' : '')}><div style={{ fontWeight: 600 }}>{n.approver_name}</div><div style={{ fontSize: 10, color: '#999' }}>{n.node_type === 'cc' ? 'Копия' : 'Соглас.'}</div></div>]).flat()}
                </div>
                {approvalInst.status === 'in_progress' && (<div className="approval-actions"><button className="btn btn-success" onClick={handleApprove}>✅ Утвердить</button><button className="btn btn-danger" onClick={() => setRejectReason('')}>❌ Отклонить</button></div>)}
                {rejectReason === '' && approvalInst.status === 'in_progress' && (<div className="reject-box" style={{ marginTop: 12 }}><textarea placeholder="Причина отклонения" value={rejectReason} onChange={e => setRejectReason(e.target.value)} /><button className="btn btn-danger" style={{ marginTop: 8 }} onClick={handleReject} disabled={!rejectReason}>Отклонить</button></div>)}
                {approvalInst.status === 'rejected' && (<div style={{ marginTop: 16, background: '#fef2f2', padding: 12, borderRadius: 6, fontSize: 13 }}><strong>Причина: </strong>{approvalInst.reject_reason || ''}<div style={{ marginTop: 12 }}><button className="btn btn-primary" onClick={() => { fetch(API + '/api/approvals/instances/' + approvalInst.id + '/resubmit', { method: 'POST' }).then(r => r.json()).then(d => { setApprovalInst(d); setView('clauses') }) }}>Повторно отправить</button></div></div>)}
                {approvalInst.status === 'approved' && <div style={{ marginTop: 16, textAlign: 'center', color: '#1a7a1a', fontWeight: 600, fontSize: 15 }}>✅ Утверждено всеми</div>}
              </div>
            )}
          </div>
        </div>
      </div>

      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Настройки</h3>
            <label>Цепочка согласования</label>
            {approvalNodes.map((n, i) => (<div key={i} className="step-editor"><span style={{ fontSize: 13, color: '#999', minWidth: 40 }}>{i + 1}</span><select value={n.node_type} onChange={ev => { const ns = [...approvalNodes]; ns[i].node_type = ev.target.value; setApprovalNodes(ns) }}><option value="approver">Согласующий</option><option value="cc">Копия</option></select><select value={n.approver_id} onChange={ev => { const ns = [...approvalNodes]; ns[i].approver_id = ev.target.value; ns[i].approver_name = USERS.find(u => u.id === ev.target.value)?.name || ''; setApprovalNodes(ns) }}>{USERS.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}</select><button onClick={() => setApprovalNodes(approvalNodes.filter((_, j) => j !== i))}>×</button></div>))}
            <button className="btn btn-outline" style={{ marginTop: 8, fontSize: 12 }} onClick={() => setApprovalNodes([...approvalNodes, { order: approvalNodes.length + 1, node_type: 'approver', approver_id: '', approver_name: '' }])}>+ Добавить</button>
            <div className="modal-actions"><button className="btn btn-outline" onClick={() => setShowSettings(false)}>Отмена</button><button className="btn btn-primary" onClick={() => setShowSettings(false)}>Сохранить</button></div>
          </div>
        </div>
      )}
    </div>
  )
}
