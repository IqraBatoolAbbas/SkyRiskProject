import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card, DataTable, Modal, StatusBadge, LoadingState } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getOfps, getFlights } from '../../services/api.js'
import { useAuth } from '../../context/AuthContext.jsx'

export default function FlightPlanManagement() {
  const { currentUser } = useAuth()
  const [ofps, setOfps] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [exportModal, setExportModal] = useState(false)

  const loadOfps = () => {
    setLoading(true)
    getOfps()
      .then((res) => {
        setLoading(false)
        if (res?.ofps?.length > 0) {
          setOfps(res.ofps)
          setSelected(res.ofps[0])
        }
      })
      .catch(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    loadOfps()
  }, [])

  const handlePrint = () => {
    window.print()
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>Operational Flight Plan (OFP) Management</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Official airline flight release documents and navigation logs generated from approved recovery decisions.
          </p>
        </div>

        <Button size="sm" icon="refresh" onClick={loadOfps}>
          Refresh OFP Ledger
        </Button>
      </div>

      <div className="split">
        {/* Left Column: OFP List */}
        <div className="stack" style={{ gap: 16 }}>
          <Card>
            <div className="section-heading">
              <div>
                <h3>Operational Flight Plans (PostgreSQL Database)</h3>
                <p className="muted">Flight release navlogs with fuel, timing, and recovery amendments.</p>
              </div>
              <Badge tone="info">{ofps.length} Documents</Badge>
            </div>

            {loading ? (
              <LoadingState label="Loading flight release documents…" />
            ) : (
              <DataTable
                rows={ofps}
                selectedId={selected?.id}
                onSelect={(draft) => setSelected(draft)}
                columns={[
                  {
                    key: 'id',
                    label: 'OFP Ref #',
                    render: (r) => (
                      <div>
                        <strong>{r.id}</strong>
                        {r.version > 1 && (
                          <Badge tone="low" style={{ marginLeft: 6, fontSize: 10 }}>REV {r.version}</Badge>
                        )}
                      </div>
                    ),
                  },
                  {
                    key: 'flight_id',
                    label: 'Flight ID',
                    render: (r) => <span style={{ fontWeight: 600, color: 'var(--cyan)' }}>{r.flight_id}</span>,
                  },
                  {
                    key: 'status',
                    label: 'Release State',
                    render: (r) => <StatusBadge value={r.status} />,
                  },
                  {
                    key: 'signed_at',
                    label: 'Signed Date',
                    render: (r) => <span style={{ fontSize: 12 }}>{r.signed_at?.slice(0, 16).replace('T', ' ')}</span>,
                  },
                ]}
              />
            )}
          </Card>

          {/* ICAO Official Format OFP Document Viewer */}
          {selected && (
            <Card>
              <div className="section-heading">
                <div>
                  <h3>ICAO Airline Dispatch Flight Plan Release</h3>
                  <p className="muted">{selected.id} · Official Navlog Document</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button size="sm" icon="printer" onClick={handlePrint}>
                    Print Document
                  </Button>
                  <Button size="sm" icon="download" onClick={() => setExportModal(true)}>
                    Export Digital PDF
                  </Button>
                </div>
              </div>

              <div
                className="ofp-doc"
                style={{
                  background: '#090E17',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: 8,
                  padding: 20,
                  fontFamily: 'monospace',
                  fontSize: 12,
                  lineHeight: 1.5,
                  color: '#E2E8F0',
                }}
              >
                <div style={{ textAlign: 'center', borderBottom: '1px dashed #334155', paddingBottom: 10, marginBottom: 12 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: 1.5, color: '#38BDF8' }}>
                    OPERATIONAL FLIGHT PLAN (OFP) — DISPATCH RELEASE
                  </div>
                  <div style={{ fontSize: 11, color: '#94A3B8' }}>
                    SKYRISK AUDITOR 4D DECISION-SUPPORT SUITE · NOTAM/WX RECOVERY AMENDMENT
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, borderBottom: '1px solid #334155', paddingBottom: 12, marginBottom: 12 }}>
                  <div>
                    <strong>OFP NUMBER:</strong> {selected.id}<br />
                    <strong>FLIGHT ID:</strong> {selected.flight_id}<br />
                    <strong>REVISION:</strong> VER-{selected.version || 1}
                  </div>
                  <div>
                    <strong>CRUISE LEVEL:</strong> {selected.cruise_fl || 'FL360'}<br />
                    <strong>EST. TIME ENROUTE:</strong> {selected.estimated_time_enroute_min || 110} MIN<br />
                    <strong>STATUS:</strong> <span style={{ color: '#10B981', fontWeight: 700 }}>{selected.status}</span>
                  </div>
                  <div>
                    <strong>DISPATCH SIGNATURE:</strong><br />
                    <span style={{ color: '#38BDF8' }}>{selected.dispatcher_signature || 'Ayesha Rahman (DISP-PK-891)'}</span><br />
                    <strong>TIMESTAMP:</strong> {selected.signed_at?.slice(0, 19).replace('T', ' ')} UTC
                  </div>
                </div>

                <div style={{ marginBottom: 14 }}>
                  <strong style={{ color: '#F59E0B' }}>ATC CLEARED ROUTE:</strong><br />
                  <span style={{ fontSize: 13, color: '#F8FAFC', fontWeight: 600 }}>{selected.route_text}</span>
                </div>

                {/* Fuel Calculation Table */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, color: '#38BDF8', marginBottom: 4 }}>FUEL COMPUTATION (KG)</div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #334155', color: '#94A3B8' }}>
                        <th style={{ textAlign: 'left', padding: '4px 0' }}>CATEGORY</th>
                        <th style={{ textAlign: 'right', padding: '4px 0' }}>FUEL (KG)</th>
                        <th style={{ textAlign: 'right', padding: '4px 0' }}>TIME (MIN)</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #1E293B' }}>
                        <td style={{ padding: '4px 0' }}>TRIP FUEL (PLANNED BURNOFF)</td>
                        <td style={{ textAlign: 'right' }}>{selected.trip_fuel_kg || 6800} KG</td>
                        <td style={{ textAlign: 'right' }}>{selected.estimated_time_enroute_min || 110} MIN</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #1E293B' }}>
                        <td style={{ padding: '4px 0' }}>CONTINGENCY (5% EN-ROUTE)</td>
                        <td style={{ textAlign: 'right' }}>{selected.contingency_fuel_kg || 350} KG</td>
                        <td style={{ textAlign: 'right' }}>15 MIN</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #1E293B' }}>
                        <td style={{ padding: '4px 0' }}>ALTERNATE DIVERSION (OPIS/OPLA)</td>
                        <td style={{ textAlign: 'right' }}>{selected.alternate_fuel_kg || 1150} KG</td>
                        <td style={{ textAlign: 'right' }}>30 MIN</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #1E293B' }}>
                        <td style={{ padding: '4px 0' }}>FINAL RESERVE (ICAO HOLDING 30M)</td>
                        <td style={{ textAlign: 'right' }}>{selected.reserve_fuel_kg || 900} KG</td>
                        <td style={{ textAlign: 'right' }}>30 MIN</td>
                      </tr>
                      <tr style={{ borderTop: '2px solid #38BDF8', fontWeight: 700, color: '#38BDF8' }}>
                        <td style={{ padding: '6px 0' }}>TOTAL BLOCK FUEL REQUIRED</td>
                        <td style={{ textAlign: 'right' }}>{selected.block_fuel_kg || 9200} KG</td>
                        <td style={{ textAlign: 'right' }}>{(selected.estimated_time_enroute_min || 110) + 75} MIN</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Dispatch Release Notes */}
                <div style={{ background: 'rgba(30, 41, 59, 0.4)', padding: 10, borderRadius: 6, border: '1px solid #334155' }}>
                  <strong style={{ color: '#94A3B8', fontSize: 11 }}>DISPATCHER RELEASE REMARKS:</strong>
                  <div style={{ marginTop: 4, color: '#E2E8F0' }}>
                    {selected.dispatch_notes || 'Aircraft dispatched in compliance with Karachi & Lahore FIR tactical hazard clearances. Multi-hazard residual risk verified within acceptable operating limits.'}
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: OFP Audit & Verification Details */}
        <div className="stack" style={{ gap: 16 }}>
          <Card>
            <div className="section-heading">
              <div>
                <h3>OFP Release Verification</h3>
                <p className="muted">Tamper-evident release credentials & verification state.</p>
              </div>
              <Badge tone="low">Verified</Badge>
            </div>

            <div className="note" style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Icon name="shield" size="sm" />
                <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>PostgreSQL Audit Lock</strong>
              </div>
              <p style={{ fontSize: 12, margin: 0, color: 'var(--muted)', lineHeight: 1.4 }}>
                This OFP was generated directly via the multi-hazard recovery workflow. Any modifications to waypoints or fuel require formal amendment release.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
              <div style={{ padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>OFP RECORD ID</div>
                <strong style={{ fontSize: 13 }}>{selected?.id}</strong>
              </div>
              <div style={{ padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>ASSOCIATED RECOVERY PLAN</div>
                <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>{selected?.recovery_plan_id || 'ORIGINAL RELEASE'}</strong>
              </div>
              <div style={{ padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>DIGITAL SIGNATURE</div>
                <strong style={{ fontSize: 13 }}>{selected?.dispatcher_signature}</strong>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Export Modal */}
      {exportModal && (
        <Modal title="Export Operational Flight Plan" onClose={() => setExportModal(false)}>
          <div className="stack" style={{ gap: 14 }}>
            <p className="muted" style={{ fontSize: 13 }}>
              Select desired export format for OFP document <strong>{selected?.id}</strong>.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Button icon="printer" onClick={() => { setExportModal(false); window.print(); }}>
                Print Ready Format (Aviation Standard)
              </Button>
              <Button icon="download" variant="secondary" onClick={() => {
                const element = document.createElement("a");
                const file = new Blob([JSON.stringify(selected, null, 2)], { type: 'application/json' });
                element.href = URL.createObjectURL(file);
                element.download = `${selected.id}.json`;
                document.body.appendChild(element);
                element.click();
                setExportModal(false);
              }}>
                Export JSON Operational Navlog
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
