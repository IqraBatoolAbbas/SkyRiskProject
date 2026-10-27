import { useEffect, useMemo, useState } from 'react'
import { Alert, Badge, Button, Card, DataTable, LoadingState } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getPersonnel, getRoles } from '../../services/api.js'
import { useAuth } from '../../context/AuthContext.jsx'

export default function UserManagement() {
  const { currentUser, switchUser } = useAuth()
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([getPersonnel(), getRoles()])
      .then(([userData, roleData]) => {
        setLoading(false)
        if (userData?.users) {
          setUsers(userData.users)
          setSelectedUser(userData.users.find((u) => u.username === currentUser.username) || userData.users[0])
        }
        if (roleData?.roles) {
          setRoles(roleData.roles)
        }
      })
      .catch(() => {
        setLoading(false)
      })
  }, [currentUser])

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>Role-Based Access Control (RBAC) & Personnel Directory</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Aviation personnel authorization matrix aligned with Proposal Section 1.4 target end-user roles.
          </p>
        </div>

        <Badge tone="low">PostgreSQL Auth Active</Badge>
      </div>

      <div className="split">
        {/* Left Column: Personnel Table */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Authorized Aviation Personnel (PostgreSQL Database)</h3>
              <p className="muted">Operational credentials, dispatcher identifiers, and active system roles.</p>
            </div>
            <Badge tone="info">{users.length} Personnel</Badge>
          </div>

          {loading ? (
            <LoadingState label="Loading personnel directory from database…" />
          ) : (
            <DataTable
              rows={users}
              selectedId={selectedUser?.id}
              onSelect={setSelectedUser}
              columns={[
                {
                  key: 'full_name',
                  label: 'Name & Callsign',
                  render: (u) => (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div
                        style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          background: currentUser.username === u.username ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.08)',
                          border: `1px solid ${currentUser.username === u.username ? '#38BDF8' : 'rgba(255, 255, 255, 0.15)'}`,
                          display: 'grid',
                          placeItems: 'center',
                          fontWeight: 700,
                          fontSize: 12,
                          color: currentUser.username === u.username ? '#38BDF8' : 'var(--text)',
                        }}
                      >
                        {u.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                      </div>
                      <div>
                        <strong style={{ fontSize: 13 }}>{u.full_name}</strong>
                        {currentUser.username === u.username && (
                          <Badge tone="info" style={{ marginLeft: 6, fontSize: 10 }}>Active Session</Badge>
                        )}
                        <div style={{ fontSize: 11, color: 'var(--muted)' }}>{u.email}</div>
                      </div>
                    </div>
                  ),
                },
                {
                  key: 'role_title',
                  label: 'Role Designation',
                  render: (u) => (
                    <div>
                      <strong style={{ fontSize: 12.5, color: 'var(--cyan)' }}>{u.role_title}</strong>
                      <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>{u.dispatcher_id}</div>
                    </div>
                  ),
                },
                {
                  key: 'actions',
                  label: 'Action',
                  render: (u) => (
                    <Button
                      size="sm"
                      variant={currentUser.username === u.username ? 'secondary' : 'primary'}
                      onClick={(e) => {
                        e.stopPropagation()
                        switchUser(u.role)
                      }}
                    >
                      {currentUser.username === u.username ? 'Active' : 'Switch Role'}
                    </Button>
                  ),
                },
              ]}
            />
          )}
        </Card>

        {/* Right Column: Selected Role Capabilities & RBAC Matrix */}
        <div className="stack" style={{ gap: 14 }}>
          {selectedUser && (
            <Card>
              <div className="section-heading">
                <div>
                  <h3>Role Permissions: {selectedUser.role_title}</h3>
                  <p className="muted">{selectedUser.full_name} · {selectedUser.dispatcher_id}</p>
                </div>
                {currentUser.username === selectedUser.username ? (
                  <Badge tone="low">Current Active Role</Badge>
                ) : (
                  <Button size="sm" icon="check" onClick={() => switchUser(selectedUser.role)}>
                    Activate Role
                  </Button>
                )}
              </div>

              <div className="stack" style={{ gap: 12 }}>
                <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 4 }}>ROLE OPERATIONAL MANDATE</div>
                  <p style={{ fontSize: 13, lineHeight: 1.5, margin: 0, color: 'var(--text)' }}>
                    {roles[selectedUser.role]?.description || 'Responsible for flight risk decision support.'}
                  </p>
                </div>

                {/* Capabilities Badges */}
                <div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8, fontWeight: 700 }}>
                    AUTHORIZED SYSTEM ACTIONS:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(roles[selectedUser.role]?.permissions || []).map((perm, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: 11.5,
                          padding: '4px 10px',
                          borderRadius: 6,
                          background: 'rgba(56, 189, 248, 0.1)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          color: '#38BDF8',
                          fontFamily: 'monospace',
                        }}
                      >
                        ✓ {perm}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 6 }}>
                  <div style={{ padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>CAN APPROVE RECOVERY</div>
                    <strong style={{ fontSize: 13, color: roles[selectedUser.role]?.can_approve_recovery ? '#10B981' : '#EF4444' }}>
                      {roles[selectedUser.role]?.can_approve_recovery ? 'YES (Authorized)' : 'NO (Restricted)'}
                    </strong>
                  </div>

                  <div style={{ padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>CAN SIGN OFP RELEASE</div>
                    <strong style={{ fontSize: 13, color: roles[selectedUser.role]?.can_sign_ofp ? '#10B981' : '#EF4444' }}>
                      {roles[selectedUser.role]?.can_sign_ofp ? 'YES (Authorized)' : 'NO (Restricted)'}
                    </strong>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Complete 4-Role Aviation Matrix */}
          <Card>
            <div className="section-heading">
              <div>
                <h3>Target User RBAC Specification</h3>
                <p className="muted">Proposal Section 1.4 role separation matrix.</p>
              </div>
            </div>

            <div className="stack" style={{ gap: 8, fontSize: 12 }}>
              <div style={{ padding: 8, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                <strong style={{ color: '#38BDF8' }}>1. Flight Dispatcher:</strong>
                <span style={{ color: 'var(--muted)', marginLeft: 6 }}>Flight plans, 4D trajectory, recovery execution, OFP release.</span>
              </div>
              <div style={{ padding: 8, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                <strong style={{ color: '#F59E0B' }}>2. Aviation Safety Analyst:</strong>
                <span style={{ color: 'var(--muted)', marginLeft: 6 }}>4D hazard cascading models, risk thresholds, safety audit.</span>
              </div>
              <div style={{ padding: 8, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                <strong style={{ color: '#10B981' }}>3. Aviation Security Auditor:</strong>
                <span style={{ color: 'var(--muted)', marginLeft: 6 }}>SHA-256 tamper-evident logs, compliance verification, forensic audits.</span>
              </div>
              <div style={{ padding: 8, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                <strong style={{ color: '#C084FC' }}>4. Meteorological Analyst:</strong>
                <span style={{ color: 'var(--muted)', marginLeft: 6 }}>Doppler weather radar feeds, SWPC Kp space-weather, DistilBERT NOTAMs.</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
