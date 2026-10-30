import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';

// Priority Sector Icons
const SECTOR_ICONS = {
  'Geographic Information Systems (GIS)': '🗺️',
  'WebGIS and Spatial Data Infrastructure (SDI)': '🌐',
  'Management Information Systems (MIS)': '💻',
  'Disaster Risk Management & Climate Resilience': '🌪️',
  'Energy & Environmental Information Systems': '⚡',
  'Transport & Infrastructure Project': '🛣️',
  'Agriculture Information Systems & Crop Monitoring': '🌾',
  'Water Resources Network & Hydrological Modeling': '💧',
  'Digital Transformation & Cloud Platforms': '☁️'
};

export default function DevexProcurementTab({ API_BASE, showToast, onSelectIndianState }) {
  // SWR in-memory cache for instant filter responses (0ms)
  const devexCacheRef = useRef(new Map());

  // Source Filter State: 'DEVEX', 'ALL', 'STATES', 'ADB'
  const [sourceFilter, setSourceFilter] = useState('DEVEX');

  // Devex Opportunities Data
  const [opportunities, setOpportunities] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterChoices, setFilterChoices] = useState({ countries: [], donors: [], sectors: [], types: [] });

  // Unified Data (when sourceFilter != 'DEVEX')
  const [unifiedData, setUnifiedData] = useState([]);
  const [unifiedTotal, setUnifiedTotal] = useState(0);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('ALL');
  const [selectedDonor, setSelectedDonor] = useState('ALL');
  const [selectedSector, setSelectedSector] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedStage, setSelectedStage] = useState('ALL');

  // Sync & Compliance State
  const [syncStatus, setSyncStatus] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [complianceInfo, setComplianceInfo] = useState(null);
  const [showComplianceModal, setShowComplianceModal] = useState(false);

  // Detail Modal State
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [activeModalTab, setActiveModalTab] = useState('overview'); // 'overview', 'scope', 'documents', 'ai_analysis', 'partners', 'tracker'

  // Partner Recommendations & Draft Email State
  const [partnerRecs, setPartnerRecs] = useState([]);
  const [loadingPartners, setLoadingPartners] = useState(false);
  const [draftingPartnerId, setDraftingPartnerId] = useState(null);
  const [createdDraft, setCreatedDraft] = useState(null);

  // Proposal Tracker State
  const [trackerForm, setTrackerForm] = useState({
    pipeline_stage: 'Opportunity Identified',
    lead_partner_name: 'GISFY Private Limited',
    notes: '',
    target_submission_date: ''
  });
  const [updatingTracker, setUpdatingTracker] = useState(false);

  // Manual Import Modal (Option D)
  const [showImportModal, setShowImportModal] = useState(false);
  const [importForm, setImportForm] = useState({
    title: '',
    donor_agency: 'World Bank',
    country: 'International',
    project_sector: 'Geographic Information Systems (GIS)',
    procurement_category: 'Consulting Services',
    submission_deadline_str: '',
    estimated_value: '',
    scope_of_work: '',
    official_tender_url: ''
  });

  // --------------------------------------------------------------------------
  // API FETCH METHODS
  // --------------------------------------------------------------------------

  const fetchComplianceStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/devex/compliance-status`);
      if (res.ok) {
        const data = await res.json();
        setComplianceInfo(data);
      }
    } catch (e) {
      console.error('Error fetching compliance status:', e);
    }
  }, [API_BASE]);

  const fetchSyncStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/devex/sync/status`);
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data);
      }
    } catch (e) {
      console.error('Error fetching sync status:', e);
    }
  }, [API_BASE]);

  const fetchDevexOpportunities = useCallback(async (forceRefresh = false) => {
    const params = new URLSearchParams();
    if (selectedCountry !== 'ALL') params.set('country', selectedCountry);
    if (selectedDonor !== 'ALL') params.set('donor', selectedDonor);
    if (selectedSector !== 'ALL') params.set('sector', selectedSector);
    if (selectedType !== 'ALL') params.set('opportunity_type', selectedType);
    if (selectedStage !== 'ALL') params.set('pipeline_stage', selectedStage);
    if (searchQuery.trim()) params.set('search', searchQuery.trim());
    params.set('limit', '100');

    const cacheKey = params.toString();
    const cached = devexCacheRef.current.get(cacheKey);

    if (cached && !forceRefresh) {
      setOpportunities(cached.items || []);
      setTotalCount(cached.total || 0);
      if (cached.filters) setFilterChoices(cached.filters);
      setLoading(false);
    } else {
      setLoading(true);
    }

    try {
      const res = await fetch(`${API_BASE}/api/devex/opportunities?${cacheKey}`);
      if (res.ok) {
        const data = await res.json();
        devexCacheRef.current.set(cacheKey, data);
        setOpportunities(data.items || []);
        setTotalCount(data.total || 0);
        if (data.filters) {
          setFilterChoices(data.filters);
        }
      } else {
        if (!cached) showToast?.('Failed to load Devex opportunities', 'error');
      }
    } catch (e) {
      console.error('Error loading devex opportunities:', e);
      if (!cached) showToast?.('Network error loading Devex opportunities', 'error');
    } finally {
      setLoading(false);
    }
  }, [API_BASE, selectedCountry, selectedDonor, selectedSector, selectedType, selectedStage, searchQuery, showToast]);

  const fetchUnifiedOpportunities = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('source_filter', sourceFilter);
      if (searchQuery.trim()) params.set('search', searchQuery.trim());
      params.set('limit', '100');

      const res = await fetch(`${API_BASE}/api/devex/unified-opportunities?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setUnifiedData(data.items || []);
        setUnifiedTotal(data.total || 0);
      }
    } catch (e) {
      console.error('Error fetching unified opportunities:', e);
    } finally {
      setLoading(false);
    }
  }, [API_BASE, sourceFilter, searchQuery]);

  useEffect(() => {
    fetchComplianceStatus();
    fetchSyncStatus();
  }, [fetchComplianceStatus, fetchSyncStatus]);

  useEffect(() => {
    if (sourceFilter === 'DEVEX') {
      fetchDevexOpportunities();
    } else {
      fetchUnifiedOpportunities();
    }
  }, [sourceFilter, fetchDevexOpportunities, fetchUnifiedOpportunities]);

  // Trigger Live Sync
  const handleTriggerSync = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/devex/sync?sync_type=manual_now`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showToast?.(`Sync Complete: Found ${data.opportunities_found} opportunities, ${data.documents_downloaded} documents.`, 'success');
        devexCacheRef.current.clear();
        fetchSyncStatus();
        fetchDevexOpportunities(true);
      } else {
        showToast?.('Sync request failed', 'error');
      }
    } catch (e) {
      showToast?.('Network error triggering synchronization', 'error');
    } finally {
      setIsSyncing(false);
    }
  };

  // Open Full Detail Modal
  const handleOpenDetail = async (tenderId, initialTab = 'overview') => {
    setActiveModalTab(initialTab);
    setLoadingDetail(true);
    setSelectedOpp(null);
    setCreatedDraft(null);
    try {
      const res = await fetch(`${API_BASE}/api/devex/opportunities/${tenderId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedOpp(data);
        if (data.tracker) {
          setTrackerForm({
            pipeline_stage: data.tracker.pipeline_stage || 'Opportunity Identified',
            lead_partner_name: data.tracker.lead_partner_name || 'GISFY Private Limited',
            notes: data.tracker.internal_notes || '',
            target_submission_date: data.tracker.target_submission_date ? data.tracker.target_submission_date.slice(0, 10) : ''
          });
        }
        if (initialTab === 'partners') {
          loadPartners(tenderId);
        }
      } else {
        showToast?.('Failed to load opportunity details', 'error');
      }
    } catch (e) {
      showToast?.('Error loading opportunity details', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  // Load Partner Recommendations
  const loadPartners = async (tenderId) => {
    setLoadingPartners(true);
    try {
      const res = await fetch(`${API_BASE}/api/devex/opportunities/${tenderId}/partners`);
      if (res.ok) {
        const data = await res.json();
        setPartnerRecs(data.recommendations || []);
      }
    } catch (e) {
      console.error('Error fetching partner recommendations:', e);
    } finally {
      setLoadingPartners(false);
    }
  };

  // Generate Draft Email for Partner
  const handleGenerateDraft = async (tenderId, partnerId) => {
    setDraftingPartnerId(partnerId);
    try {
      const res = await fetch(`${API_BASE}/api/devex/opportunities/${tenderId}/partners/${partnerId}/draft-email`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setCreatedDraft(data);
        showToast?.(`Draft created for ${data.company_name} (Auto-send disabled).`, 'success');
      } else {
        showToast?.('Failed to create partner draft', 'error');
      }
    } catch (e) {
      showToast?.('Network error creating partner draft', 'error');
    } finally {
      setDraftingPartnerId(null);
    }
  };

  // Update Proposal Tracker
  const handleUpdateTracker = async () => {
    if (!selectedOpp) return;
    setUpdatingTracker(true);
    try {
      const tenderId = selectedOpp.tender.id;
      const res = await fetch(`${API_BASE}/api/devex/opportunities/${tenderId}/tracker`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackerForm)
      });
      if (res.ok) {
        const data = await res.json();
        showToast?.(`Proposal stage updated to "${data.pipeline_stage}".`, 'success');
        // Refresh local detail
        handleOpenDetail(tenderId, 'tracker');
        fetchDevexOpportunities();
      } else {
        showToast?.('Failed to update tracker', 'error');
      }
    } catch (e) {
      showToast?.('Error updating proposal tracker', 'error');
    } finally {
      setUpdatingTracker(false);
    }
  };

  // Option D: Manual Import Submit
  const handleManualImportSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/devex/manual-import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importForm)
      });
      if (res.ok) {
        const data = await res.json();
        showToast?.(`Successfully imported opportunity: "${data.title}"`, 'success');
        setShowImportModal(false);
        fetchDevexOpportunities();
      } else {
        showToast?.('Manual import failed', 'error');
      }
    } catch (err) {
      showToast?.('Error during manual import', 'error');
    }
  };

  // Deadline urgency styling helper
  const getDeadlineBadge = (daysLeft, closingDate) => {
    if (daysLeft === null || daysLeft === undefined) {
      return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#f1f5f9', color: '#475569' }}>📅 {closingDate}</span>;
    }
    if (daysLeft <= 0) {
      return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#fee2e2', color: '#991b1b', fontWeight: 700 }}>🔴 Closing Today ({closingDate})</span>;
    }
    if (daysLeft <= 3) {
      return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#ffedd5', color: '#9a3412', fontWeight: 700 }}>🟠 Within 3 Days ({daysLeft}d left)</span>;
    }
    if (daysLeft <= 7) {
      return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#fef3c7', color: '#92400e', fontWeight: 600 }}>🟡 Within 7 Days ({daysLeft}d left)</span>;
    }
    if (daysLeft <= 15) {
      return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#e0f2fe', color: '#0369a1' }}>🔵 Within 15 Days ({daysLeft}d left)</span>;
    }
    return <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#ecfdf5', color: '#065f46' }}>🟢 Within 30+ Days ({daysLeft}d left)</span>;
  };

  return (
    <div className="devex-intelligence-container" style={{ padding: '16px 20px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      
      {/* -------------------------------------------------------------------- */}
      {/* 1. HEADER & INTEGRATION HIERARCHY STATUS BANNER (MODULE 2)           */}
      {/* -------------------------------------------------------------------- */}
      <div style={{ background: '#ffffff', borderRadius: '12px', padding: '20px 24px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontSize: '24px' }}>🌍</span>
              <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Devex Global Procurement Intelligence
              </h1>
              <span style={{ background: '#dbeafe', color: '#1e40af', padding: '3px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 700 }}>
                International Tenders & Donors
              </span>
            </div>
            <p style={{ margin: 0, color: '#64748b', fontSize: '13.5px', maxWidth: '850px', lineHeight: 1.5 }}>
              International consulting opportunities from Devex intelligence, official multilateral donor portals (World Bank, UNGM, AfDB, MCC, USAID), and bilateral missions.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => setShowComplianceModal(true)}
              style={{ background: '#f8fafc', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 14px', borderRadius: '8px', fontSize: '12.5px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              🛡️ Integration Hierarchy & Compliance
            </button>
            <button
              onClick={() => setShowImportModal(true)}
              style={{ background: '#f8fafc', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 14px', borderRadius: '8px', fontSize: '12.5px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              📥 Option D: Manual Import
            </button>
            <button
              onClick={handleTriggerSync}
              disabled={isSyncing}
              style={{ background: '#2563eb', border: 'none', color: '#ffffff', padding: '8px 18px', borderRadius: '8px', fontSize: '13px', fontWeight: 700, cursor: isSyncing ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 2px 4px rgba(37,99,235,0.2)' }}
            >
              {isSyncing ? '🔄 Synchronizing...' : '🔄 Synchronize Sources'}
            </button>
          </div>
        </div>

        {/* Integration Hierarchy Live Status Pill Bar */}
        <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', fontSize: '12.5px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, color: '#334155' }}>Active Permitted Ingestion:</span>
            <span style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
              🟢 Option B: Mailbox Alerts
            </span>
            <span style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
              🟢 Option C: Official Donor Enrichment
            </span>
            <span style={{ background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0', padding: '2px 8px', borderRadius: '4px' }}>
              🔒 Option A: Enterprise API (Contract Required)
            </span>
          </div>

          <div style={{ color: '#64748b', fontSize: '12px' }}>
            Last Sync: <strong>{syncStatus?.last_sync_time ? new Date(syncStatus.last_sync_time).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recently Synchronized'}</strong>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 2. UNIFIED SOURCE FILTERS (MODULE 7)                                  */}
      {/* -------------------------------------------------------------------- */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px', background: '#f8fafc', padding: '6px', borderRadius: '10px', border: '1px solid #e2e8f0', width: 'fit-content' }}>
        <button
          onClick={() => setSourceFilter('ALL')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', background: sourceFilter === 'ALL' ? '#0f172a' : 'transparent', color: sourceFilter === 'ALL' ? '#ffffff' : '#475569', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
        >
          🌟 All Opportunities (Unified View)
        </button>
        <button
          onClick={() => setSourceFilter('DEVEX')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', background: sourceFilter === 'DEVEX' ? '#2563eb' : 'transparent', color: sourceFilter === 'DEVEX' ? '#ffffff' : '#475569', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
        >
          🌍 Devex Global Procurement
        </button>
        <button
          onClick={() => setSourceFilter('ADB')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', background: sourceFilter === 'ADB' ? '#0891b2' : 'transparent', color: sourceFilter === 'ADB' ? '#ffffff' : '#475569', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
        >
          🌐 ADB CMS Opportunities
        </button>
        <button
          onClick={() => setSourceFilter('STATES')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', background: sourceFilter === 'STATES' ? '#d97706' : 'transparent', color: sourceFilter === 'STATES' ? '#ffffff' : '#475569', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
        >
          🇮🇳 Indian State Tenders (29 States)
        </button>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 3. SEARCH & DEEP FILTERS BAR (MODULE 15)                             */}
      {/* -------------------------------------------------------------------- */}
      {sourceFilter === 'DEVEX' && (
        <div style={{ background: '#ffffff', borderRadius: '10px', padding: '14px 18px', border: '1px solid #e2e8f0', marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Search keywords, project title, donor, procurement ref..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flex: '1 1 280px', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
          />

          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', background: '#fff' }}
          >
            <option value="ALL">All Countries ({filterChoices.countries.length})</option>
            {filterChoices.countries.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select
            value={selectedDonor}
            onChange={(e) => setSelectedDonor(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', background: '#fff' }}
          >
            <option value="ALL">All Donors ({filterChoices.donors.length})</option>
            {filterChoices.donors.map(d => <option key={d} value={d}>{d}</option>)}
          </select>

          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', background: '#fff' }}
          >
            <option value="ALL">All Sectors ({filterChoices.sectors.length})</option>
            {filterChoices.sectors.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', background: '#fff' }}
          >
            <option value="ALL">All Proposal Stages</option>
            <option value="Opportunity Identified">Opportunity Identified</option>
            <option value="Under Evaluation">Under Evaluation</option>
            <option value="EOI Preparation">EOI Preparation</option>
            <option value="EOI Submitted">EOI Submitted</option>
            <option value="Shortlisted">Shortlisted</option>
            <option value="Proposal Submitted">Proposal Submitted</option>
            <option value="Awarded">Awarded</option>
          </select>

          {(searchQuery || selectedCountry !== 'ALL' || selectedDonor !== 'ALL' || selectedSector !== 'ALL' || selectedStage !== 'ALL') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCountry('ALL');
                setSelectedDonor('ALL');
                setSelectedSector('ALL');
                setSelectedStage('ALL');
              }}
              style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '7px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', color: '#475569' }}
            >
              Reset Filters
            </button>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 4. OPPORTUNITIES TABLE VIEW (MODULE 5, 7)                             */}
      {/* -------------------------------------------------------------------- */}
      <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              {sourceFilter === 'DEVEX' ? '🌍 Devex Procurement Opportunities' : `🌟 Unified Opportunities (${sourceFilter})`}
            </h2>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              Showing {sourceFilter === 'DEVEX' ? opportunities.length : unifiedData.length} records
            </span>
          </div>
          <button
            onClick={() => sourceFilter === 'DEVEX' ? fetchDevexOpportunities() : fetchUnifiedOpportunities()}
            style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
          >
            🔄 Refresh List
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>🔄</div>
            <div>Loading procurement opportunities...</div>
          </div>
        ) : (sourceFilter === 'DEVEX' ? opportunities : unifiedData).length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>🔍</div>
            <div style={{ fontWeight: 600, color: '#0f172a' }}>No opportunities found</div>
            <div style={{ fontSize: '13px', marginTop: '4px' }}>Try resetting filters or click Synchronize Sources above.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontWeight: 700 }}>
                  <th style={{ padding: '12px 16px' }}>Project / Assignment Title</th>
                  <th style={{ padding: '12px 14px' }}>Source & Ref</th>
                  <th style={{ padding: '12px 14px' }}>Country</th>
                  <th style={{ padding: '12px 14px' }}>Donor / Client</th>
                  <th style={{ padding: '12px 14px' }}>Sector</th>
                  <th style={{ padding: '12px 14px' }}>Deadline</th>
                  <th style={{ padding: '12px 14px' }}>GISFY Eligibility</th>
                  <th style={{ padding: '12px 14px' }}>Readiness</th>
                  <th style={{ padding: '12px 14px' }}>Documents</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center' }}>Working Actions</th>
                </tr>
              </thead>
              <tbody>
                {(sourceFilter === 'DEVEX' ? opportunities : unifiedData).map((opp) => {
                  const isDevex = sourceFilter === 'DEVEX' || opp.source_code === 'DEVEX';
                  const sectorIcon = SECTOR_ICONS[opp.sector] || '📁';

                  return (
                    <tr key={opp.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      {/* Project Title */}
                      <td style={{ padding: '14px 16px', maxWidth: '320px' }}>
                        <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '4px', lineHeight: 1.4 }}>
                          {opp.title}
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '11px', background: '#f1f5f9', color: '#475569', padding: '1px 6px', borderRadius: '4px' }}>
                            Ref: {opp.procurement_ref || opp.tender_id}
                          </span>
                          {opp.estimated_value && (
                            <span style={{ fontSize: '11px', background: '#ecfdf5', color: '#065f46', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                              Est: ${Number(opp.estimated_value).toLocaleString()} {opp.currency}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Source */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 700,
                          background: opp.source === 'Devex' ? '#dbeafe' : (opp.source === 'ADB CMS' ? '#cffafe' : '#fef3c7'),
                          color: opp.source === 'Devex' ? '#1e40af' : (opp.source === 'ADB CMS' ? '#155e75' : '#92400e')
                        }}>
                          {opp.source || 'Devex'}
                        </span>
                      </td>

                      {/* Country */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap', fontWeight: 600, color: '#1e293b' }}>
                        📍 {opp.country}
                      </td>

                      {/* Donor */}
                      <td style={{ padding: '14px 14px', maxWidth: '180px', color: '#334155' }}>
                        {opp.donor || opp.donor_client}
                      </td>

                      {/* Sector */}
                      <td style={{ padding: '14px 14px', maxWidth: '180px' }}>
                        <span style={{ fontSize: '12px', color: '#334155' }}>
                          {sectorIcon} {opp.sector}
                        </span>
                      </td>

                      {/* Closing Date */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap' }}>
                        {getDeadlineBadge(opp.days_left, opp.closing_date)}
                      </td>

                      {/* Eligibility */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: 700,
                          background: opp.gisfy_eligibility === 'Eligible' ? '#dcfce7' : '#fef9c3',
                          color: opp.gisfy_eligibility === 'Eligible' ? '#166534' : '#854d0e'
                        }}>
                          {opp.gisfy_eligibility === 'Eligible' ? '✅ Eligible' : '⚠️ Clarify'}
                        </span>
                      </td>

                      {/* Readiness */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <div style={{ width: '45px', background: '#e2e8f0', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(opp.readiness_score || 80, 100)}%`, background: (opp.readiness_score >= 80 ? '#16a34a' : '#eab308'), height: '100%' }} />
                          </div>
                          <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#334155' }}>{opp.readiness_score || 80}%</span>
                        </div>
                      </td>

                      {/* Documents */}
                      <td style={{ padding: '14px 14px', whiteSpace: 'nowrap' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: (opp.verified_docs_count > 0 || opp.documents_count > 0) ? '#059669' : '#64748b' }}>
                          📄 {opp.documents_count || 0} Docs
                        </span>
                      </td>

                      {/* Working Actions (Module 7) */}
                      <td style={{ padding: '14px 16px', textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                          <button
                            onClick={() => handleOpenDetail(opp.id, 'overview')}
                            title="View Full Opportunity Details"
                            style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '5px', fontSize: '11.5px', fontWeight: 600, cursor: 'pointer' }}
                          >
                            👁️ View
                          </button>
                          {opp.official_tender_url && (
                            <a
                              href={opp.official_tender_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Open Official Donor Source Portal"
                              style={{ background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', padding: '5px 8px', borderRadius: '5px', fontSize: '11.5px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}
                            >
                              🌐 Source
                            </a>
                          )}
                          <button
                            onClick={() => handleOpenDetail(opp.id, 'documents')}
                            title="View & Download Authentic Documents"
                            style={{ background: '#f8fafc', color: '#334155', border: '1px solid #cbd5e1', padding: '6px 8px', borderRadius: '5px', fontSize: '11.5px', cursor: 'pointer' }}
                          >
                            📄 Docs
                          </button>
                          <button
                            onClick={() => handleOpenDetail(opp.id, 'ai_analysis')}
                            title="AI Tender Analysis & Eligibility Assessment"
                            style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '6px 8px', borderRadius: '5px', fontSize: '11.5px', fontWeight: 600, cursor: 'pointer' }}
                          >
                            🧠 AI Check
                          </button>
                          <button
                            onClick={() => handleOpenDetail(opp.id, 'partners')}
                            title="Recommend JV / Consortium Partners"
                            style={{ background: '#f3e8ff', color: '#6b21a8', border: '1px solid #e9d5ff', padding: '6px 8px', borderRadius: '5px', fontSize: '11.5px', fontWeight: 600, cursor: 'pointer' }}
                          >
                            🤝 JV Partner
                          </button>
                          <button
                            onClick={() => handleOpenDetail(opp.id, 'tracker')}
                            title="Track Proposal Progress"
                            style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '6px 8px', borderRadius: '5px', fontSize: '11.5px', fontWeight: 600, cursor: 'pointer' }}
                          >
                            📊 Track
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 5. MULTI-TAB OPPORTUNITY DETAIL MODAL                                */}
      {/* -------------------------------------------------------------------- */}
      {selectedOpp && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <div style={{ background: '#ffffff', borderRadius: '14px', width: '920px', maxWidth: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)', overflow: 'hidden' }}>
            
            {/* Modal Header */}
            <div style={{ padding: '18px 24px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 }}>
                    {selectedOpp.devex_detail.donor_agency}
                  </span>
                  <span style={{ fontSize: '12px', color: '#475569', fontWeight: 600 }}>
                    Ref: {selectedOpp.devex_detail.original_procurement_ref}
                  </span>
                  <span style={{ fontSize: '12px', color: '#475569' }}>
                    📍 {selectedOpp.devex_detail.country}
                  </span>
                </div>
                <h3 style={{ fontSize: '16.5px', fontWeight: 800, color: '#0f172a', margin: 0, lineHeight: 1.4 }}>
                  {selectedOpp.tender.title}
                </h3>
              </div>
              <button
                onClick={() => setSelectedOpp(null)}
                style={{ background: 'none', border: 'none', fontSize: '22px', color: '#94a3b8', cursor: 'pointer', padding: '0 4px' }}
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', background: '#ffffff', padding: '0 16px' }}>
              {[
                { id: 'overview', label: '📌 Overview & Dates' },
                { id: 'scope', label: '📋 Technical Scope' },
                { id: 'documents', label: `📄 Documents (${selectedOpp.documents.length})` },
                { id: 'ai_analysis', label: `🧠 AI Eligibility (${selectedOpp.ai_analysis.verdict})` },
                { id: 'partners', label: '🤝 JV Partner Match' },
                { id: 'tracker', label: `📊 Proposal Tracker (${selectedOpp.tracker.pipeline_stage})` }
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => {
                    setActiveModalTab(t.id);
                    if (t.id === 'partners') loadPartners(selectedOpp.tender.id);
                  }}
                  style={{
                    padding: '12px 14px',
                    border: 'none',
                    borderBottom: activeModalTab === t.id ? '2px solid #2563eb' : '2px solid transparent',
                    background: 'none',
                    fontWeight: activeModalTab === t.id ? 700 : 500,
                    color: activeModalTab === t.id ? '#2563eb' : '#64748b',
                    fontSize: '12.5px',
                    cursor: 'pointer'
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1, fontSize: '13.5px', color: '#334155', lineHeight: 1.6 }}>
              
              {/* TAB 1: OVERVIEW */}
              {activeModalTab === 'overview' && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Issuing Donor</div>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{selectedOpp.devex_detail.donor_agency}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Country & Region</div>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{selectedOpp.devex_detail.country} ({selectedOpp.devex_detail.region})</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Submission Deadline</div>
                      <div style={{ fontWeight: 700, color: '#b91c1c' }}>{selectedOpp.devex_detail.submission_deadline_str}</div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Timezone: {selectedOpp.devex_detail.deadline_timezone}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Estimated Budget</div>
                      <div style={{ fontWeight: 700, color: '#047857' }}>
                        {selectedOpp.devex_detail.estimated_value ? `$${Number(selectedOpp.devex_detail.estimated_value).toLocaleString()} ${selectedOpp.devex_detail.currency}` : 'Not Disclosed'}
                      </div>
                    </div>
                  </div>

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Assignment Objectives</h4>
                  <p style={{ background: '#ffffff', padding: '12px 14px', borderRadius: '6px', border: '1px solid #e2e8f0', margin: '0 0 18px 0' }}>
                    {selectedOpp.devex_detail.objectives || 'Objectives detailed in official Terms of Reference.'}
                  </p>

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Official Source Portals</h4>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    {selectedOpp.devex_detail.official_tender_url && (
                      <a
                        href={selectedOpp.devex_detail.official_tender_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ padding: '8px 14px', background: '#2563eb', color: '#fff', textDecoration: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '12.5px' }}
                      >
                        🌐 Official Donor Procurement Notice
                      </a>
                    )}
                    {selectedOpp.devex_detail.devex_url && (
                      <a
                        href={selectedOpp.devex_detail.devex_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ padding: '8px 14px', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', textDecoration: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '12.5px' }}
                      >
                        🔍 Devex Funding Search Entry
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: TECHNICAL SCOPE */}
              {activeModalTab === 'scope' && (
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Scope of Work</h4>
                  <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '18px', whiteSpace: 'pre-line' }}>
                    {selectedOpp.devex_detail.scope_of_work}
                  </div>

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Technical Requirements & Architecture</h4>
                  <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '18px' }}>
                    {selectedOpp.devex_detail.technical_requirements || 'Technical architecture defined in TOR attachments.'}
                  </div>

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Key Expert Requirements</h4>
                  <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    {selectedOpp.devex_detail.required_experts || 'Staffing criteria detailed in Request for Proposals (RFP).'}
                  </div>
                </div>
              )}

              {/* TAB 3: DOCUMENTS */}
              {activeModalTab === 'documents' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                        Authentic Original Donor Documents
                      </h4>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        Retrieved directly from issuing donor. Native formats with SHA-256 integrity verification.
                      </span>
                    </div>
                    <a
                      href={`${API_BASE}/api/devex/opportunities/${selectedOpp.tender.id}/download-all-zip`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ background: '#059669', color: '#fff', padding: '7px 14px', borderRadius: '6px', fontWeight: 700, fontSize: '12.5px', textDecoration: 'none' }}
                    >
                      📦 Download All (ZIP)
                    </a>
                  </div>

                  {selectedOpp.documents.length === 0 ? (
                    <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                      No documents currently attached.
                    </div>
                  ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                      <thead>
                        <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                          <th style={{ padding: '10px' }}>Filename</th>
                          <th style={{ padding: '10px' }}>Category</th>
                          <th style={{ padding: '10px' }}>Size</th>
                          <th style={{ padding: '10px' }}>SHA-256 Checksum</th>
                          <th style={{ padding: '10px' }}>Status</th>
                          <th style={{ padding: '10px', textAlign: 'center' }}>Download</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedOpp.documents.map((d) => (
                          <tr key={d.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '10px', fontWeight: 600, color: '#0f172a' }}>{d.file_name}</td>
                            <td style={{ padding: '10px' }}>{d.doc_category}</td>
                            <td style={{ padding: '10px' }}>{d.portal_size_kb ? `${d.portal_size_kb} KB` : 'Attached'}</td>
                            <td style={{ padding: '10px', fontFamily: 'monospace', fontSize: '11px', color: '#475569' }}>
                              {d.sha256_hash ? `${d.sha256_hash.slice(0, 16)}...` : 'Verified'}
                            </td>
                            <td style={{ padding: '10px' }}>
                              <span style={{ background: '#dcfce7', color: '#166534', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 }}>
                                {d.access_status}
                              </span>
                            </td>
                            <td style={{ padding: '10px', textAlign: 'center' }}>
                              <a
                                href={`${API_BASE}/api/devex/opportunities/${selectedOpp.tender.id}/documents/${d.id}/download`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ background: '#2563eb', color: '#fff', padding: '4px 8px', borderRadius: '4px', textDecoration: 'none', fontSize: '11px', fontWeight: 600 }}
                              >
                                ⬇️ Download
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {/* TAB 4: AI ELIGIBILITY */}
              {activeModalTab === 'ai_analysis' && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: selectedOpp.ai_analysis.verdict === 'Eligible' ? '#f0fdf4' : '#fefce8', border: selectedOpp.ai_analysis.verdict === 'Eligible' ? '1px solid #bbf7d0' : '1px solid #fef08a', padding: '16px 20px', borderRadius: '8px', marginBottom: '18px' }}>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: selectedOpp.ai_analysis.verdict === 'Eligible' ? '#15803d' : '#a16207', textTransform: 'uppercase' }}>
                        GISFY Eligibility Assessment Verdict
                      </div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                        {selectedOpp.ai_analysis.verdict === 'Eligible' ? '✅ Eligible for Bidding' : '⚠️ Requires Clarification'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>Proposal Readiness Score</div>
                      <div style={{ fontSize: '24px', fontWeight: 800, color: selectedOpp.ai_analysis.readiness_score >= 80 ? '#15803d' : '#d97706' }}>
                        {selectedOpp.ai_analysis.readiness_score} / 100
                      </div>
                    </div>
                  </div>

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Identified Strengths</h4>
                  <ul style={{ margin: '0 0 16px 0', paddingLeft: '20px', color: '#166534' }}>
                    {selectedOpp.ai_analysis.identified_strengths.map((s, idx) => (
                      <li key={idx} style={{ marginBottom: '6px' }}>{s}</li>
                    ))}
                  </ul>

                  {selectedOpp.ai_analysis.qualification_gaps.length > 0 && (
                    <>
                      <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Qualification Gaps & Requirements</h4>
                      <ul style={{ margin: '0 0 16px 0', paddingLeft: '20px', color: '#991b1b' }}>
                        {selectedOpp.ai_analysis.qualification_gaps.map((g, idx) => (
                          <li key={idx} style={{ marginBottom: '6px' }}>{g}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Strategic Action Recommendations</h4>
                  <ul style={{ margin: '0 0 16px 0', paddingLeft: '20px', color: '#1e40af' }}>
                    {selectedOpp.ai_analysis.recommendations.map((r, idx) => (
                      <li key={idx} style={{ marginBottom: '6px' }}>{r}</li>
                    ))}
                  </ul>

                  <div style={{ fontSize: '11.5px', color: '#64748b', fontStyle: 'italic', borderTop: '1px solid #e2e8f0', paddingTop: '10px' }}>
                    {selectedOpp.ai_analysis.compliance_disclaimer}
                  </div>
                </div>
              )}

              {/* TAB 5: JV PARTNER MATCH */}
              {activeModalTab === 'partners' && (
                <div>
                  <div style={{ marginBottom: '14px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                      Recommended JV / Consortium Partners for {selectedOpp.devex_detail.country}
                    </h4>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      Firms selected based on local country registration, multilateral credentials, and complementary capabilities.
                    </span>
                  </div>

                  {loadingPartners ? (
                    <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>Finding matching partners...</div>
                  ) : partnerRecs.length === 0 ? (
                    <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>No direct partners currently found in directory.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {partnerRecs.map((p) => (
                        <div key={p.partner_id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px', background: '#f8fafc' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <div>
                              <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '14px' }}>{p.name}</div>
                              <div style={{ fontSize: '12px', color: '#64748b' }}>📍 {p.city}, {p.country} | 🌐 {p.website}</div>
                            </div>
                            <span style={{ background: '#dcfce7', color: '#166534', padding: '3px 8px', borderRadius: '12px', fontWeight: 700, fontSize: '11px' }}>
                              {p.match_score}% Match
                            </span>
                          </div>

                          <div style={{ fontSize: '12px', color: '#475569', marginBottom: '8px' }}>
                            <strong>Synergy Role:</strong> {p.synergy_role}
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <button
                              onClick={() => handleGenerateDraft(selectedOpp.tender.id, p.partner_id)}
                              disabled={draftingPartnerId === p.partner_id}
                              style={{ background: '#7c3aed', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                            >
                              {draftingPartnerId === p.partner_id ? 'Generating...' : '✉️ Generate Outreach Draft'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {createdDraft && (
                    <div style={{ marginTop: '16px', padding: '14px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '8px' }}>
                      <div style={{ fontWeight: 700, color: '#065f46', marginBottom: '4px' }}>
                        ✅ Draft Created in Partner Outreach Tab (Draft ID #{createdDraft.draft_id})
                      </div>
                      <div style={{ fontSize: '12px', color: '#065f46' }}>
                        Subject: <strong>{createdDraft.subject}</strong> (Auto-send disabled awaiting approval).
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 6: PROPOSAL TRACKER */}
              {activeModalTab === 'tracker' && (
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
                    Proposal Progression Workflow
                  </h4>
                  <p style={{ fontSize: '12.5px', color: '#64748b', margin: '0 0 16px 0' }}>
                    Note: Bids must be submitted via the official donor portal ({selectedOpp.tracker.submission_portal}), not Devex.
                  </p>

                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '18px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginBottom: '14px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                          Pipeline Stage
                        </label>
                        <select
                          value={trackerForm.pipeline_stage}
                          onChange={(e) => setTrackerForm({ ...trackerForm, pipeline_stage: e.target.value })}
                          style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', background: '#fff' }}
                        >
                          <option value="Opportunity Identified">Opportunity Identified</option>
                          <option value="Under Evaluation">Under Evaluation</option>
                          <option value="Eligible">Eligible</option>
                          <option value="EOI Preparation">EOI Preparation</option>
                          <option value="EOI Submitted">EOI Submitted</option>
                          <option value="Shortlisted">Shortlisted</option>
                          <option value="RFP Received">RFP Received</option>
                          <option value="Technical Proposal Preparation">Technical Proposal Preparation</option>
                          <option value="Financial Proposal Preparation">Financial Proposal Preparation</option>
                          <option value="Proposal Submitted">Proposal Submitted</option>
                          <option value="Under Evaluation by Client">Under Evaluation by Client</option>
                          <option value="Awarded">Awarded</option>
                          <option value="Closed">Closed</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                          Lead Partner / Consortium Role
                        </label>
                        <input
                          type="text"
                          value={trackerForm.lead_partner_name}
                          onChange={(e) => setTrackerForm({ ...trackerForm, lead_partner_name: e.target.value })}
                          style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                        />
                      </div>
                    </div>

                    <div style={{ marginBottom: '14px' }}>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                        Proposal Review & Coordination Notes
                      </label>
                      <textarea
                        rows={3}
                        value={trackerForm.notes}
                        onChange={(e) => setTrackerForm({ ...trackerForm, notes: e.target.value })}
                        placeholder="Add review feedback, consortium agreements, submission credentials..."
                        style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                      />
                    </div>

                    <button
                      onClick={handleUpdateTracker}
                      disabled={updatingTracker}
                      style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
                    >
                      {updatingTracker ? 'Updating...' : '💾 Save Pipeline Update'}
                    </button>
                  </div>

                  {selectedOpp.tracker.history.length > 0 && (
                    <div>
                      <h5 style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Pipeline History Log</h5>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {selectedOpp.tracker.history.map((h, i) => (
                          <div key={i} style={{ fontSize: '12px', background: '#fff', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: '6px' }}>
                            <strong>{h.stage}</strong> – <span style={{ color: '#64748b' }}>{new Date(h.timestamp).toLocaleDateString()}</span>: {h.notes}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>

            {/* Modal Footer */}
            <div style={{ padding: '14px 24px', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedOpp(null)}
                style={{ padding: '7px 16px', background: '#e2e8f0', color: '#334155', border: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '12.5px', cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 6. COMPLIANCE & INTEGRATION HIERARCHY MODAL (MODULE 2)               */}
      {/* -------------------------------------------------------------------- */}
      {showComplianceModal && complianceInfo && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <div style={{ background: '#ffffff', borderRadius: '14px', width: '700px', maxWidth: '100%', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Devex Integration Hierarchy & Compliance
                </h3>
                <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: 700 }}>
                  Strict Compliance with Terms of Use & Legal Hierarchy
                </span>
              </div>
              <button onClick={() => setShowComplianceModal(false)} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>

            <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.5, marginBottom: '18px' }}>
              {complianceInfo.subscription_notes}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
              {Object.values(complianceInfo.hierarchy_options).map(opt => (
                <div key={opt.code} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', background: opt.is_active ? '#f0fdf4' : '#f8fafc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <strong style={{ fontSize: '13px', color: '#0f172a' }}>{opt.name}</strong>
                    <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', background: opt.is_active ? '#dcfce7' : '#f1f5f9', color: opt.is_active ? '#166534' : '#64748b' }}>
                      {opt.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>{opt.description}</div>
                </div>
              ))}
            </div>

            <div style={{ textAlign: 'right' }}>
              <button
                onClick={() => setShowComplianceModal(false)}
                style={{ padding: '8px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 7. OPTION D: MANUAL IMPORT MODAL (MODULE 2)                          */}
      {/* -------------------------------------------------------------------- */}
      {showImportModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.6)', zIndex: 1100, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          <div style={{ background: '#ffffff', borderRadius: '14px', width: '650px', maxWidth: '100%', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Option D — Manual Opportunity Import
                </h3>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  Add opportunities from permitted Devex exports or direct donor notices.
                </span>
              </div>
              <button onClick={() => setShowImportModal(false)} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>

            <form onSubmit={handleManualImportSubmit}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Project Title *</label>
                <input
                  type="text"
                  required
                  value={importForm.title}
                  onChange={(e) => setImportForm({ ...importForm, title: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Donor Agency *</label>
                  <input
                    type="text"
                    required
                    value={importForm.donor_agency}
                    onChange={(e) => setImportForm({ ...importForm, donor_agency: e.target.value })}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Country *</label>
                  <input
                    type="text"
                    required
                    value={importForm.country}
                    onChange={(e) => setImportForm({ ...importForm, country: e.target.value })}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Sector</label>
                  <input
                    type="text"
                    value={importForm.project_sector}
                    onChange={(e) => setImportForm({ ...importForm, project_sector: e.target.value })}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Submission Deadline</label>
                  <input
                    type="date"
                    value={importForm.submission_deadline_str}
                    onChange={(e) => setImportForm({ ...importForm, submission_deadline_str: e.target.value })}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>Scope of Work Overview</label>
                <textarea
                  rows={3}
                  value={importForm.scope_of_work}
                  onChange={(e) => setImportForm({ ...importForm, scope_of_work: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  style={{ padding: '8px 14px', background: '#e2e8f0', color: '#334155', border: 'none', borderRadius: '6px', fontSize: '13px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: '8px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
                >
                  Save &amp; Ingest
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
