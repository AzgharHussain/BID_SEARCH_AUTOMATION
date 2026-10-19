import React, { useState, useEffect, useRef, useMemo } from 'react';
import './index.css';

// Formats a date value into Date, Month, Year format: "19 Oct 2026"
export const formatDateDMY = (dateInput) => {
  if (!dateInput) return '';
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  return d.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

// Formats a date & time value into Date, Month, Year with time: "19 Oct 2026, 11:10 AM"
export const formatDateTimeDMY = (dateInput) => {
  if (!dateInput) return '';
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  const datePart = d.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
  const timePart = d.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
  return `${datePart}, ${timePart}`;
};

// Dynamic backend API URL for local and remote server environments
export const API_BASE = import.meta.env.VITE_API_BASE || (
  typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : 'http://127.0.0.1:8000'
);

function App() {
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedKw, setExpandedKw] = useState({});
  const [previewDoc, setPreviewDoc] = useState(null);
  const [docMetadata, setDocMetadata] = useState(null);
  const [loadingMeta, setLoadingMeta] = useState(false);
  const [downloadingId, setDownloadingId] = useState(null);
  const [downloadingTenderId, setDownloadingTenderId] = useState(null);
  const [autoDownloading, setAutoDownloading] = useState(false);
  const [scrapingState, setScrapingState] = useState(null);
  const [searchStateQuery, setSearchStateQuery] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('q') || '';
    } catch (e) {
      return '';
    }
  });
  const [filterKeyword, setFilterKeyword] = useState('ALL');
  const [stageFilter, setStageFilter] = useState('ALL'); // 'ALL' | 'LIVE' | 'UPCOMING' | 'CLOSING_SOON'
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncingNow, setSyncingNow] = useState(false);
  const [showGisfyModal, setShowGisfyModal] = useState(false);
  const [floatingExpanded, setFloatingExpanded] = useState(true);
  const [toast, setToast] = useState(null);
  const terminalRef = useRef(null);

  // Real-Time New Proposal Live Alert State
  const [newTenderAlert, setNewTenderAlert] = useState(null);
  const [highlightedTenderId, setHighlightedTenderId] = useState(null);
  const prevAlertedTenderIdRef = useRef(null);
  const [showSimulateModal, setShowSimulateModal] = useState(false);
  const [simulatingUpload, setSimulatingUpload] = useState(false);
  const [selectedSimState, setSelectedSimState] = useState('Andhra Pradesh');
  const [selectedSimKeyword, setSelectedSimKeyword] = useState('GIS');

  // PDF Compression State
  const [compressingDocId, setCompressingDocId] = useState(null);
  const [compressingAll, setCompressingAll] = useState(false);

  // Team Email Dispatch State
  const [showEmailModal, setShowEmailModal] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('email') === '1';
    } catch (e) {
      return false;
    }
  });
  const [emailActiveTab, setEmailActiveTab] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('emailTab') || 'compose';
    } catch (e) {
      return 'compose';
    }
  });
  const [emailScope, setEmailScope] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('scope') || 'state';
    } catch (e) {
      return 'state';
    }
  });
  const [emailSelectedState, setEmailSelectedState] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('state') || 'Andhra Pradesh';
    } catch (e) {
      return 'Andhra Pradesh';
    }
  });
  const [emailSelectedTender, setEmailSelectedTender] = useState(null);
  const [emailRecipients, setEmailRecipients] = useState([]);
  const [emailSubject, setEmailSubject] = useState('[GISFY Proposal Dispatch] Andhra Pradesh Procurement Proposals & Attached Documents');
  const [emailNotes, setEmailNotes] = useState('');
  const [emailAttachZip, setEmailAttachZip] = useState(true);
  const [teamMembers, setTeamMembers] = useState([]);
  const [showAddMemberForm, setShowAddMemberForm] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('Team Member');
  const [previewHtml, setPreviewHtml] = useState('');
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [emailHistory, setEmailHistory] = useState([]);
  const [sendingEmail, setSendingEmail] = useState(false);

  // Collaboration Partners State
  const [showPartnersModal, setShowPartnersModal] = useState(false);
  const [selectedPartnerTender, setSelectedPartnerTender] = useState(null);
  const [partnerStateName, setPartnerStateName] = useState(null);
  const [partnersList, setPartnersList] = useState([]);
  const [loadingPartners, setLoadingPartners] = useState(false);
  const [partnerSearchQuery, setPartnerSearchQuery] = useState('');
  const [partnerDomainFilter, setPartnerDomainFilter] = useState('ALL');
  const [partnerStateFilter, setPartnerStateFilter] = useState('ALL');
  const [partnerMinScore, setPartnerMinScore] = useState(80);
  const [partnerSortBy, setPartnerSortBy] = useState('score');
  const [partnersSummary, setPartnersSummary] = useState(null);
  const [viewingPartnerDetails, setViewingPartnerDetails] = useState(null);
  const [outreachPartner, setOutreachPartner] = useState(null);
  const [outreachLoading, setOutreachLoading] = useState(false);
  const [outreachProposal, setOutreachProposal] = useState(null);
  const [outreachCustomNotes, setOutreachCustomNotes] = useState('');
  const [outreachJvSplit, setOutreachJvSplit] = useState('60% Lead Bidder (GISFY) : 40% Specialized Partner');
  const [showAddPartnerModal, setShowAddPartnerModal] = useState(false);
  const [newPartnerForm, setNewPartnerForm] = useState({
    name: '',
    short_name: '',
    primary_domain: 'Drone LiDAR & Aerial Mapping',
    secondary_domains: '',
    state: 'Telangana',
    city: 'Hyderabad',
    pan_india_presence: true,
    turnover: '₹25.0 Cr',
    employee_count: '50+ Professionals',
    empanelment_status: 'Survey of India Empaneled',
    certifications: 'ISO 9001:2015, ISO 27001',
    contact_person: '',
    designation: 'Director - Strategic Alliances',
    email: '',
    phone: '',
    website: '',
    description: '',
    synergy_roles: ''
  });
  const [savingPartner, setSavingPartner] = useState(false);


  // States Sidebar and Layout Control State
  const [selectedState, setSelectedState] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('state') || null;
    } catch (e) {
      return null;
    }
  });
  const [selectedSidebarKw, setSelectedSidebarKw] = useState(() => {
    try {
      return new URLSearchParams(window.location.search).get('keyword') || null;
    } catch (e) {
      return null;
    }
  });
  const [sidebarSearch, setSidebarSearch] = useState('');
  const [sidebarFilter, setSidebarFilter] = useState('ALL'); // 'ALL' | 'READY' | 'ACTIVE'
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isTerminalOpen, setIsTerminalOpen] = useState(true);
  const [expandedSidebarStates, setExpandedSidebarStates] = useState({});
  const [expandedSidebarKws, setExpandedSidebarKws] = useState({});
  const [expandedArchives, setExpandedArchives] = useState({});

  const toggleArchiveExpansion = (archiveKey, e) => {
    if (e) e.stopPropagation();
    setExpandedArchives(prev => ({
      ...prev,
      [archiveKey]: !prev[archiveKey]
    }));
  };

  // Real live logs from the agent (initialized with bash startup)
  const [logs, setLogs] = useState([
    { type: 'command', text: 'gisfy-agent@procurements:~$ ./scraper.sh --watch --all-29-states', isUserCmd: true },
    { type: 'info', text: '🚀 [BASH INITIALIZED] Real-Time Procurement Scraper & Live Portal Monitor Active.', isUserCmd: true },
    { type: 'success', text: `🟢 Connected to Backend API (${API_BASE}).`, isUserCmd: true },
    { type: 'normal', text: 'Type "help" below or click quick action buttons above to run BASH commands.', isUserCmd: true }
  ]);
  const [terminalCmdInput, setTerminalCmdInput] = useState('');

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  const fetchReport = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/reports/state-keyword`);
      if (response.ok) {
        const data = await response.json();
        const sortedData = Array.isArray(data) ? [...data].sort((a, b) => (a.state_name || '').localeCompare(b.state_name || '')) : data;
        setReportData(sortedData);
        if (data && data.length > 0) {
          const urlParams = new URLSearchParams(window.location.search);
          const paramState = urlParams.get('state');
          const paramKw = urlParams.get('keyword');
          const paramTender = urlParams.get('tender');

          if (paramState) {
            setSelectedState(paramState);
            setExpandedSidebarStates(prev => ({ ...prev, [paramState]: true }));
            if (paramKw) {
              setSelectedSidebarKw(paramKw);
              setExpandedKw(prev => ({ ...prev, [`${paramState}-${paramKw}`]: true }));
            }
            if (paramTender) {
              setHighlightedTenderId(paramTender);
              setTimeout(() => {
                const el = document.getElementById(`tender-${paramTender}`);
                if (el) {
                  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }, 450);
            }
          } else {
            const firstState = data[0];
            const firstKw = firstState?.keywords?.find(k => k.tenders && k.tenders.length > 0) || firstState?.keywords?.[0];
            if (firstState && firstKw) {
              setExpandedKw(prev => {
                if (Object.keys(prev).length === 0) {
                  return { [`${firstState.state_name}-${firstKw.keyword}`]: true };
                }
                return prev;
              });
              setExpandedSidebarStates(prev => {
                if (Object.keys(prev).length === 0) {
                  return { [firstState.state_name]: true };
                }
                return prev;
              });
            }
          }
        }
      }
    } catch (error) {
      console.error("Error fetching report:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/logs`);
      if (response.ok) {
        const data = await response.json();
        if (data && data.length > 0) {
          setLogs(prev => {
            const userCmds = prev.filter(l => l.isUserCmd);
            if (userCmds.length > 0) {
              return [...data, ...userCmds];
            }
            return data;
          });
        }
      }
    } catch (error) {
      console.error("Error fetching logs:", error);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/sync/status`);
      if (response.ok) {
        const data = await response.json();
        setSyncStatus(data);

        // Real-time live proposal detection across all state portals
        if (data.latest_new_tender && data.latest_new_tender.tender_id) {
          const incoming = data.latest_new_tender;
          if (prevAlertedTenderIdRef.current && prevAlertedTenderIdRef.current !== incoming.tender_id) {
            setNewTenderAlert(incoming);
            prevAlertedTenderIdRef.current = incoming.tender_id;
            showToast(`🔔 New Proposal Added: ${incoming.title.substring(0, 48)}... (${incoming.state_name})`, 'success');
            // Instantly refresh report data so proposal appears on website immediately!
            fetchReport();
            fetchLogs();
          } else if (!prevAlertedTenderIdRef.current) {
            prevAlertedTenderIdRef.current = incoming.tender_id;
            setNewTenderAlert(incoming);
          }
        }
      }
    } catch (error) {
      console.error("Error fetching sync status:", error);
    }
  };

  const handleViewNewProposal = (tender) => {
    if (!tender) return;
    setSelectedState(tender.state_name);
    setExpandedKw(prev => ({
      ...prev,
      [`${tender.state_name}-${tender.keyword}`]: true
    }));
    setExpandedSidebarStates(prev => ({
      ...prev,
      [tender.state_name]: true
    }));
    setHighlightedTenderId(tender.tender_id);
    showToast(`📍 Showing proposal: ${tender.tender_id} (${tender.state_name})`, 'info');

    setTimeout(() => {
      const el = document.getElementById(`tender-${tender.tender_id}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 250);

    setTimeout(() => {
      setHighlightedTenderId(null);
    }, 8000);
  };

  const handleSimulatePortalNotification = async (stateNameOverride = null) => {
    const targetState = stateNameOverride || selectedSimState || 'Karnataka';
    setSimulatingUpload(true);
    showToast(`📡 Ingesting official portal notification for ${targetState}...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/sync/trigger-portal-alert?state=${encodeURIComponent(targetState)}&keyword=${encodeURIComponent(selectedSimKeyword)}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.tender) {
          setNewTenderAlert(data.tender);
          prevAlertedTenderIdRef.current = data.tender.tender_id;
          showToast(`🔔 New Proposal Added: ${data.tender.title.substring(0, 45)}... (${data.tender.state_name})`, 'success');
          fetchReport();
          fetchLogs();
          fetchSyncStatus();
          setShowSimulateModal(false);
          handleViewNewProposal(data.tender);
        }
      } else {
        showToast('Could not ingest tender from portal', 'error');
      }
    } catch (err) {
      console.error('Simulate upload error:', err);
      showToast('Failed to trigger portal alert', 'error');
    } finally {
      setSimulatingUpload(false);
    }
  };

  const handleTriggerLiveSync = async () => {
    setSyncingNow(true);
    showToast("🚀 Initiating 15-Minute Live Portal Sync across all 29 official state portals...", "info");
    try {
      const res = await fetch(`${API_BASE}/api/sync/run-now`, {
        method: 'POST'
      });
      if (res.ok) {
        showToast("⚡ Live Portal Sync triggered! Streaming updates to Agent Terminal.", "success");
        setTimeout(fetchSyncStatus, 500);
        setTimeout(fetchLogs, 1000);
        setTimeout(fetchReport, 2000);
      } else {
        showToast("Failed to trigger live sync", "error");
      }
    } catch (err) {
      console.error("Sync error:", err);
      showToast("Could not reach backend sync service", "error");
    } finally {
      setTimeout(() => setSyncingNow(false), 2000);
    }
  };

  const handleCompressPdf = async (doc, e) => {
    if (e) e.stopPropagation();
    if (!doc || !doc.id) return;
    setCompressingDocId(doc.id);
    showToast(`🗜️ Compacting large PDF "${doc.file_name}"...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/documents/${doc.id}/compress`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        if (data.compressed) {
          showToast(`✅ PDF compressed! Saved ${data.saved_percent}% (${data.original_size_kb} KB ➔ ${data.compressed_size_kb} KB)`, 'success');
          fetchReport();
          fetchLogs();
        } else {
          showToast(`ℹ️ PDF "${doc.file_name}" is already at optimal compressed size.`, 'info');
        }
      } else {
        showToast('Compression failed for this document', 'error');
      }
    } catch (err) {
      console.error('Compress error:', err);
      showToast('Error compressing PDF', 'error');
    } finally {
      setCompressingDocId(null);
    }
  };

  const handleCompressAllLargePdfs = async () => {
    setCompressingAll(true);
    showToast('🗜️ Initiating PDF Compression Engine across all 29 states... Streaming logs to Agent Terminal.', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/documents/compress-all?threshold_mb=1.0`, {
        method: 'POST'
      });
      if (res.ok) {
        showToast('⚡ PDF Compression Engine active! Watch live progress in Agent Terminal.', 'success');
        setTimeout(fetchLogs, 1000);
        setTimeout(fetchReport, 3500);
      } else {
        showToast('Could not start bulk PDF compression', 'error');
      }
    } catch (err) {
      console.error('Bulk compress error:', err);
      showToast('Failed to reach compression service', 'error');
    } finally {
      setTimeout(() => setCompressingAll(false), 2500);
    }
  };

  useEffect(() => {
    fetchReport();
    fetchLogs();
    fetchSyncStatus();
    fetchTeamMembers();
    fetchEmailHistory();
    fetchPartnersSummary();
    const interval = setInterval(() => {
      fetchReport();
      fetchLogs();
      fetchSyncStatus();
    }, 4000);
    return () => clearInterval(interval);
  }, []);


  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (showEmailModal && emailActiveTab === 'preview' && !previewHtml) {
      handleFetchPreview();
    }
  }, [showEmailModal, emailActiveTab]);

  useEffect(() => {
    if (searchStateQuery && reportData.length > 0) {
      const q = searchStateQuery.toLowerCase().trim();
      const newExpanded = {};
      reportData.forEach(state => {
        state.keywords.forEach(kw => {
          const match = kw.tenders.some(t => 
            (t.tender_id || '').toLowerCase().includes(q) ||
            (t.title || '').toLowerCase().includes(q)
          );
          if (match) {
            newExpanded[`${state.state_name}-${kw.keyword}`] = true;
          }
        });
      });
      if (Object.keys(newExpanded).length > 0) {
        setExpandedKw(prev => ({ ...prev, ...newExpanded }));
      }
    }
  }, [searchStateQuery, reportData]);

  const toggleExpand = (stateName, keywordName) => {
    const key = `${stateName}-${keywordName}`;
    setExpandedKw(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSelectSidebarState = (stateName) => {
    setSelectedState(stateName);
    setExpandedSidebarStates(prev => ({
      ...prev,
      [stateName]: !prev[stateName]
    }));
  };

  const handleSelectSidebarKeyword = (stateName, keywordName, e) => {
    if (e) e.stopPropagation();
    const key = `${stateName}-${keywordName}`;
    setExpandedSidebarKws(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
    setExpandedKw(prev => ({
      ...prev,
      [key]: true
    }));
    setSelectedState(stateName);
    setSelectedSidebarKw(keywordName);
  };

  const openPreview = async (doc, tender, stateName, e) => {
    if (e) e.stopPropagation();
    const initialDoc = {
      ...doc,
      tenderTitle: tender?.title || doc.tenderTitle,
      tenderId: tender?.tender_id || doc.tenderId,
      department: tender?.department || doc.department,
      stateName: stateName || doc.stateName,
      description: tender?.description || doc.description,
      publishedDate: tender?.published_date || doc.publishedDate,
      lastDate: tender?.last_date || doc.lastDate,
      portalTenderUrl: tender?.portal_tender_url || doc.portalTenderUrl
    };
    setPreviewDoc(initialDoc);
    setDocMetadata(null);
    setLoadingMeta(true);

    try {
      const query = (doc.id && doc.id < 800000) ? `id=${doc.id}` : `path=${encodeURIComponent(doc.local_path || '')}`;
      const res = await fetch(`${API_BASE}/api/documents/info?${query}`);
      if (res.ok) {
        const meta = await res.json();
        setDocMetadata(meta);
      }
    } catch (err) {
      console.error("Error fetching document info:", err);
    } finally {
      setLoadingMeta(false);
    }
  };

  const closePreview = () => {
    setPreviewDoc(null);
    setDocMetadata(null);
  };

  // Direct, rock-solid client-side download to user's computer
  const handleDownloadDocument = async (doc, e) => {
    if (e) e.stopPropagation();
    const docKey = doc.id || doc.file_name;
    const isFileDownloaded = doc.is_downloaded || doc.verified || (doc.download_status === 'downloaded');

    if (!isFileDownloaded) {
      showToast(`⏳ Checking authentic tender document on government portal...`, 'info');
    } else {
      showToast(`⬇ Starting instant download for "${doc.file_name}"...`, 'info');
    }

    setDownloadingId(docKey);
    try {
      const query = (doc.id && doc.id < 800000) ? `id=${doc.id}` : `path=${encodeURIComponent(doc.local_path || '')}`;
      const url = `${API_BASE}/api/documents/download?${query}&attachment=true`;
      
      const response = await fetch(url);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail;
        
        let portalUrl = doc.source_url || 'https://tender.apeprocurement.gov.in';
        let msg = `Authentic document is hosted on the official government portal.`;
        
        if (typeof detail === 'object' && detail !== null) {
          portalUrl = detail.portal_tender_url || portalUrl;
          msg = detail.message || msg;
        } else if (typeof detail === 'string') {
          msg = detail;
        }
        
        // Seamless fallback: directly open the official state government tender page so the user can download
        showToast(`🏛️ ${msg} Opening official portal...`, 'info');
        if (portalUrl) {
          window.open(portalUrl, '_blank');
        }
        return;
      }
      
      // Determine file name from Content-Disposition header if possible
      let fileName = doc.file_name || 'tender_document.pdf';
      const disposition = response.headers.get('content-disposition');
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match && match[1]) {
          fileName = match[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
      
      showToast(`✅ Authentic document "${fileName}" downloaded! Saved to your computer.`, 'success');
      fetchReport();
    } catch (err) {
      console.error("Direct download failed:", err);
      showToast(err.message || `Download failed.`, 'error');
    } finally {
      setDownloadingId(null);
    }
  };

  // Download all documents of a tender in a single ZIP
  const handleDownloadBundle = async (tender, e) => {
    if (e) e.stopPropagation();
    setDownloadingTenderId(tender.id);
    showToast(`⏳ Packaging authentic documents for Tender ${tender.tender_id}...`, 'info');
    try {
      const url = `${API_BASE}/api/tenders/${tender.id}/download-bundle`;
      const response = await fetch(url);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const portalUrl = tender.portal_tender_url || 'https://tender.apeprocurement.gov.in';
        showToast(`🏛️ Tender documents are on official portal. Opening portal...`, 'info');
        window.open(portalUrl, '_blank');
        return;
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `Tender_${tender.tender_id}_Documents.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
      
      showToast(`📦 Tender bundle downloaded: Tender_${tender.tender_id}_Documents.zip`, 'success');
      fetchReport();
    } catch (err) {
      console.error("Bundle download error:", err);
      showToast(err.message || "Bundle download failed.", 'error');
    } finally {
      setDownloadingTenderId(null);
    }
  };

  // Trigger Automatic Downloads in the backend
  const handleTriggerAutoDownload = async () => {
    setAutoDownloading(true);
    showToast("🚀 Initiating Backend Automatic Downloader across all states...", "info");
    try {
      const response = await fetch(`${API_BASE}/api/documents/auto-download`, {
        method: 'POST'
      });
      if (response.ok) {
        showToast("⚡ Backend Automatic Downloader is active! Check terminal logs.", "success");
        setTimeout(fetchLogs, 800);
        setTimeout(fetchReport, 1500);
      } else {
        showToast("Backend auto-download responded with error", "error");
      }
    } catch (err) {
      console.error("Auto download trigger error:", err);
      showToast("Could not reach backend auto-downloader", "error");
    } finally {
      setTimeout(() => setAutoDownloading(false), 2500);
    }
  };

  // Trigger Scraper for a specific State
  const handleTriggerStateScrape = async (stateName, e) => {
    if (e) e.stopPropagation();
    setScrapingState(stateName);
    showToast(`🚀 Triggering live scraper for ${stateName}... Monitor Agent Terminal.`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/states/${encodeURIComponent(stateName)}/scrape`, {
        method: 'POST'
      });
      if (res.ok) {
        showToast(`⚡ Scraper running for ${stateName}! Ingesting live proposals...`, 'success');
        setTimeout(fetchLogs, 1000);
        setTimeout(fetchReport, 3000);
      } else {
        showToast(`Failed to trigger scraper for ${stateName}`, 'error');
      }
    } catch (err) {
      console.error("Scraper trigger error:", err);
      showToast(`Could not reach scraper for ${stateName}`, 'error');
    } finally {
      setTimeout(() => setScrapingState(null), 3000);
    }
  };

  // ==========================================
  // Team Email Dispatch Functions
  // ==========================================
  async function fetchTeamMembers() {
    try {
      const res = await fetch(`${API_BASE}/api/email/team-members`);
      if (res.ok) {
        const data = await res.json();
        setTeamMembers(data);
        setEmailRecipients(prev => prev.length === 0 ? data.map(m => m.email) : prev);
      }
    } catch (err) {
      console.error("Error fetching team members:", err);
    }
  }

  async function fetchEmailHistory() {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/email/history`);
      if (res.ok) {
        const data = await res.json();
        setEmailHistory(data);
      }
    } catch (err) {
      console.error("Error fetching email history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }

  const openEmailModal = ({ scope = 'state', stateName = null, tender = null }) => {
    const chosenScope = tender ? 'tender' : (scope || 'state');
    const chosenState = stateName || selectedState || reportData[0]?.state_name || 'Andhra Pradesh';

    setEmailScope(chosenScope);
    setEmailSelectedState(chosenState);
    setEmailSelectedTender(tender || null);
    setEmailActiveTab('compose');
    setPreviewHtml('');

    let defaultSubj = '';
    if (chosenScope === 'tender' && tender) {
      defaultSubj = `[GISFY Tender Alert] ${chosenState} - Ref #${tender.tender_id}: ${tender.title.substring(0, 50)}...`;
    } else if (chosenScope === 'all') {
      defaultSubj = `[GISFY Proposal Dispatch] Pan-India (All 29 States) Procurement Directory & Documents`;
    } else {
      defaultSubj = `[GISFY Proposal Dispatch] ${chosenState} Procurement Proposals & Attached Documents`;
    }
    setEmailSubject(defaultSubj);
    setEmailNotes('');
    setShowEmailModal(true);

    if (teamMembers.length === 0) {
      fetchTeamMembers();
    }
  };

  const handleScopeChange = (newScope) => {
    setEmailScope(newScope);
    setPreviewHtml('');
    if (newScope === 'all') {
      setEmailSubject('[GISFY Proposal Dispatch] Pan-India (All 29 States) Procurement Directory & Documents');
    } else if (newScope === 'state') {
      setEmailSubject(`[GISFY Proposal Dispatch] ${emailSelectedState} Procurement Proposals & Attached Documents`);
    } else if (newScope === 'tender' && emailSelectedTender) {
      setEmailSubject(`[GISFY Tender Alert] ${emailSelectedState} - Ref #${emailSelectedTender.tender_id}: ${emailSelectedTender.title.substring(0, 50)}...`);
    }
  };

  const toggleRecipient = (email) => {
    setEmailRecipients(prev => 
      prev.includes(email) ? prev.filter(e => e !== email) : [...prev, email]
    );
  };

  // Safe JSON / List parser for partner attributes
  const parseJsonSafe = (raw, fallback = []) => {
    if (!raw) return fallback;
    if (Array.isArray(raw)) return raw;
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : fallback;
    } catch (e) {
      if (typeof raw === 'string') {
        return raw.split(',').map(s => s.trim()).filter(Boolean);
      }
      return fallback;
    }
  };

  const fetchPartnersSummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/partners/stats/summary`);
      if (res.ok) {
        const data = await res.json();
        setPartnersSummary(data);
      }
    } catch (err) {
      console.error("Error fetching partner stats:", err);
    }
  };

  const allAvailableTenders = useMemo(() => {
    const list = [];
    const seen = new Set();
    reportData.forEach(state => {
      (state.keywords || []).forEach(kw => {
        (kw.tenders || []).forEach(t => {
          if (!seen.has(t.id)) {
            seen.add(t.id);
            list.push({ ...t, state_name: state.state_name });
          }
        });
      });
    });
    return list;
  }, [reportData]);

  const fetchPartnersForTenderOrAll = async (tender = null, minScoreVal = partnerMinScore) => {
    setLoadingPartners(true);
    try {
      if (tender && tender.id) {
        const scoreParam = minScoreVal !== null && minScoreVal !== undefined ? minScoreVal : 80;
        const res = await fetch(`${API_BASE}/api/partners/search-by-tender/${tender.id}?min_score=${scoreParam}`);
        if (res.ok) {
          const data = await res.json();
          setPartnersList(data.partners || []);
        } else {
          setPartnersList([]);
        }
      } else {
        const res = await fetch(`${API_BASE}/api/partners`);
        if (res.ok) {
          const data = await res.json();
          setPartnersList(data.map(p => ({
            ...p,
            collaboration_status: p.status || 'Available',
            match_score: null,
            match_category: 'Verified Partner Profile',
            why_needed: p.description || 'Specialized domain partner available for Pan-India Joint Ventures.',
            synergy_scope: 'Joint Venture consortium partner with GISFY.'
          })));
        } else {
          setPartnersList([]);
        }
      }
    } catch (err) {
      console.error("Error fetching partners:", err);
      showToast('Error loading partners: ' + err.message, 'error');
    } finally {
      setLoadingPartners(false);
    }
  };

  const openPartnersModal = ({ tender = null, stateName = null }) => {
    setSelectedPartnerTender(tender);
    setPartnerStateName(stateName);
    setPartnerSearchQuery('');
    setPartnerDomainFilter('ALL');
    setPartnerStateFilter('ALL');
    setPartnerMinScore(80);
    setPartnerSortBy('score');
    setShowPartnersModal(true);
    fetchPartnersForTenderOrAll(tender, 80);
    fetchPartnersSummary();
  };

  const handleUpdateCollaborationStatus = async (partnerId, newStatus) => {
    if (!selectedPartnerTender) return;
    try {
      const res = await fetch(`${API_BASE}/api/partners/collaboration-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tender_id: selectedPartnerTender.id,
          partner_id: partnerId,
          status: newStatus
        })
      });
      if (res.ok) {
        showToast(`🤝 Consortium status updated to: ${newStatus}`, 'success');
        setPartnersList(prev => prev.map(p => p.id === partnerId ? { ...p, collaboration_status: newStatus } : p));
      }
    } catch (err) {
      showToast('❌ Failed to update status', 'error');
    }
  };

  const handleInitiateOutreach = async (partner) => {
    if (!selectedPartnerTender) {
      showToast('Please select a specific tender first to generate a customized Joint Venture proposal.', 'info');
      return;
    }
    setOutreachPartner(partner);
    setOutreachLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/partners/initiate-outreach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tender_id: selectedPartnerTender.id,
          partner_id: partner.id,
          custom_message: outreachCustomNotes,
          proposed_jv_split: outreachJvSplit
        })
      });
      if (res.ok) {
        const data = await res.json();
        setOutreachProposal(data);
        setPartnersList(prev => prev.map(p => p.id === partner.id ? { ...p, collaboration_status: 'Outreach Sent' } : p));
        showToast(`✉️ Consortium Proposal Generated for ${partner.name}!`, 'success');
      } else {
        showToast('Failed to generate outreach proposal', 'error');
      }
    } catch (err) {
      showToast('Proposal generation error: ' + err.message, 'error');
    } finally {
      setOutreachLoading(false);
    }
  };

  const handleCreateNewPartner = async (e) => {
    e.preventDefault();
    if (!newPartnerForm.name || !newPartnerForm.primary_domain) {
      showToast('Please specify the partner name and primary domain', 'error');
      return;
    }
    setSavingPartner(true);
    try {
      const res = await fetch(`${API_BASE}/api/partners`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPartnerForm)
      });
      if (res.ok) {
        const created = await res.json();
        showToast(`✅ Registered ${created.name} successfully!`, 'success');
        setShowAddPartnerModal(false);
        fetchPartnersForTenderOrAll(selectedPartnerTender);
        fetchPartnersSummary();
      } else {
        showToast('Failed to create partner profile', 'error');
      }
    } catch (err) {
      showToast('Error registering partner: ' + err.message, 'error');
    } finally {
      setSavingPartner(false);
    }
  };

  const filteredAndSortedPartners = useMemo(() => {
    let result = [...partnersList];

    if (partnerSearchQuery.trim()) {
      const q = partnerSearchQuery.toLowerCase().trim();
      result = result.filter(p => 
        (p.name || '').toLowerCase().includes(q) ||
        (p.short_name || '').toLowerCase().includes(q) ||
        (p.primary_domain || '').toLowerCase().includes(q) ||
        (p.secondary_domains || '').toLowerCase().includes(q) ||
        (p.city || '').toLowerCase().includes(q) ||
        (p.state || '').toLowerCase().includes(q) ||
        (p.certifications || '').toLowerCase().includes(q) ||
        (p.contact_person || '').toLowerCase().includes(q) ||
        (p.why_needed || '').toLowerCase().includes(q)
      );
    }

    if (partnerDomainFilter && partnerDomainFilter !== 'ALL') {
      const df = partnerDomainFilter.toLowerCase();
      result = result.filter(p => 
        (p.primary_domain || '').toLowerCase().includes(df) ||
        (p.secondary_domains || '').toLowerCase().includes(df)
      );
    }

    if (partnerStateFilter && partnerStateFilter !== 'ALL') {
      const sf = partnerStateFilter.toLowerCase();
      result = result.filter(p => (p.state || '').toLowerCase() === sf);
    }

    if (selectedPartnerTender && partnerMinScore > 0) {
      result = result.filter(p => p.match_score == null || p.match_score >= partnerMinScore);
    }

    result.sort((a, b) => {
      if (partnerSortBy === 'score') {
        const scoreA = a.match_score !== null && a.match_score !== undefined ? a.match_score : 0;
        const scoreB = b.match_score !== null && b.match_score !== undefined ? b.match_score : 0;
        return scoreB - scoreA;
      }
      if (partnerSortBy === 'rating') {
        return (b.rating || 0) - (a.rating || 0);
      }
      if (partnerSortBy === 'name') {
        return (a.name || '').localeCompare(b.name || '');
      }
      return 0;
    });

    return result;
  }, [partnersList, partnerSearchQuery, partnerDomainFilter, partnerStateFilter, partnerMinScore, partnerSortBy, selectedPartnerTender]);



  const handleAddTeamMember = async (e) => {
    if (e) e.preventDefault();
    if (!newMemberEmail || !newMemberEmail.includes('@')) {
      showToast('Please enter a valid email address.', 'error');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/email/team-members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: newMemberEmail.trim(),
          name: newMemberName.trim() || undefined,
          role: newMemberRole.trim() || 'Team Member'
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setTeamMembers(updated);
        setEmailRecipients(prev => [...new Set([...prev, newMemberEmail.trim().toLowerCase()])]);
        setNewMemberEmail('');
        setNewMemberName('');
        setNewMemberRole('Team Member');
        setShowAddMemberForm(false);
        showToast(`👤 Added ${newMemberEmail} to team recipients!`, 'success');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to add team member', 'error');
      }
    } catch (err) {
      showToast('Network error adding team member', 'error');
    }
  };

  const handleDeleteTeamMember = async (emailToDelete, e) => {
    if (e) e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE}/api/email/team-members?email=${encodeURIComponent(emailToDelete)}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        const updated = await res.json();
        setTeamMembers(updated);
        setEmailRecipients(prev => prev.filter(em => em !== emailToDelete));
        showToast(`Removed ${emailToDelete} from team recipients`, 'info');
      }
    } catch (err) {
      showToast('Failed to remove recipient', 'error');
    }
  };

  async function handleFetchPreview() {
    setLoadingPreview(true);
    try {
      const payload = {
        recipients: emailRecipients.length > 0 ? emailRecipients : ['preview@gisfy.co.in'],
        subject: emailSubject || 'GISFY Proposal Dispatch',
        state_name: emailScope === 'all' ? null : emailSelectedState,
        tender_id: emailScope === 'tender' && emailSelectedTender ? emailSelectedTender.tender_id : null,
        include_all_states: emailScope === 'all',
        attach_zip_bundle: emailAttachZip,
        custom_notes: emailNotes || null
      };
      const res = await fetch(`${API_BASE}/api/email/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const html = await res.text();
        setPreviewHtml(html);
        setEmailActiveTab('preview');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Could not generate preview', 'error');
      }
    } catch (err) {
      showToast('Preview generation error', 'error');
    } finally {
      setLoadingPreview(false);
    }
  }

  const handleSendEmailDispatch = async () => {
    if (emailRecipients.length === 0) {
      showToast('Please select at least one team member recipient.', 'error');
      return;
    }
    setSendingEmail(true);
    showToast(`✉️ Packaging state proposal & documents for ${emailRecipients.length} team members...`, 'info');

    try {
      const payload = {
        recipients: emailRecipients,
        subject: emailSubject || 'GISFY Proposal Dispatch',
        state_name: emailScope === 'all' ? null : emailSelectedState,
        tender_id: emailScope === 'tender' && emailSelectedTender ? emailSelectedTender.tender_id : null,
        include_all_states: emailScope === 'all',
        attach_zip_bundle: emailAttachZip,
        custom_notes: emailNotes || null
      };

      const res = await fetch(`${API_BASE}/api/email/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        showToast(`🎉 Email successfully dispatched to ${data.recipients.length} team members!`, 'success');
        
        // Append real-time command log to terminal
        setLogs(prev => [
          ...prev,
          { 
            type: 'command', 
            text: `gisfy-agent@email:~$ ./dispatch_mail.py --to "${data.recipients.join(', ')}" --scope "${data.state_name}" --attach-zip`, 
            isUserCmd: true 
          },
          { 
            type: 'success', 
            text: `✉️ [EMAIL DISPATCHED] "${data.subject}" delivered to ${data.recipients.length} recipients. Attached ${data.attached_files_count} files (${data.documents_count} total documents linked). Archive: storage/sent_emails/${data.preview_file}`, 
            isUserCmd: true 
          }
        ]);
        
        fetchEmailHistory();
        setEmailActiveTab('history');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Email dispatch failed', 'error');
      }
    } catch (err) {
      console.error("Email dispatch error:", err);
      showToast('Could not reach backend email service.', 'error');
    } finally {
      setSendingEmail(false);
    }
  };

  // Compute keyword documents and PDF statistics helper
  const getKeywordStats = (kwObj) => {
    const tenders = kwObj?.tenders || [];
    let totalDocs = 0;
    let pdfCount = 0;
    let zipCount = 0;
    let otherCount = 0;
    let downloadedCount = 0;
    const docsList = [];

    tenders.forEach(t => {
      (t.documents || []).forEach(doc => {
        totalDocs++;
        const fname = (doc.file_name || '').toLowerCase();
        const ftype = (doc.file_type || '').toLowerCase();
        const isPdf = fname.endsWith('.pdf') || ftype === '.pdf' || (!fname.includes('.') && ftype !== '.zip' && ftype !== '.xls');
        const isZip = fname.endsWith('.zip') || ftype === '.zip' || ftype === 'bundle_zip';

        if (isPdf) {
          pdfCount++;
        } else if (isZip) {
          zipCount++;
        } else {
          otherCount++;
        }

        if (doc.is_downloaded || doc.download_status === 'downloaded' || doc.verified) {
          downloadedCount++;
        }

        docsList.push({
          ...doc,
          tenderId: t.tender_id,
          tenderTitle: t.title,
          department: t.department,
          stage: t.stage,
          publishedDate: t.published_date,
          lastDate: t.last_date,
          portalTenderUrl: t.portal_tender_url,
          isPdf
        });
      });
    });

    return {
      tendersCount: tenders.length,
      totalDocs,
      pdfCount,
      zipCount,
      otherCount,
      downloadedCount,
      docsList
    };
  };

  // Extract all unique keywords for filter dropdown
  const allKeywordOptions = useMemo(() => {
    const kwSet = new Set();
    reportData.forEach(s => {
      s.keywords.forEach(k => kwSet.add(k.keyword));
    });
    return Array.from(kwSet).sort();
  }, [reportData]);

  // Filtered states for the sidebar based on sidebar search and filter pills (Alphabetical A-Z)
  const filteredSidebarStates = useMemo(() => {
    const sq = (sidebarSearch || '').trim().toLowerCase();
    const list = reportData.filter(state => {
      if (sq && !state.state_name.toLowerCase().includes(sq)) {
        return false;
      }
      if (sidebarFilter === 'READY') {
        return state.downloaded_docs_count > 0;
      }
      if (sidebarFilter === 'ACTIVE') {
        return state.keywords.some(kw => kw.tenders.some(t => t.is_live));
      }
      return true;
    });
    return [...list].sort((a, b) => (a.state_name || '').localeCompare(b.state_name || ''));
  }, [reportData, sidebarSearch, sidebarFilter]);

  // Filtered state data based on search, keyword dropdown, stageFilter, and selectedState
  const filteredReportData = useMemo(() => {
    const q = (searchStateQuery || '').trim().toLowerCase();

    return reportData.map(state => {
      // If a specific state is selected from the sidebar, focus exclusively on that state
      if (selectedState && state.state_name !== selectedState) {
        return null;
      }

      const stateNameMatch = !q || state.state_name.toLowerCase().includes(q);

      const filteredKeywords = state.keywords.map(kw => {
        if (filterKeyword !== 'ALL' && kw.keyword !== filterKeyword) {
          return { ...kw, tenders: [] };
        }

        const kwMatch = !q || kw.keyword.toLowerCase().includes(q);

        const tenders = kw.tenders.filter(t => {
          // Stage filter
          if (stageFilter === 'DOWNLOADED_ONLY' && !t.documents.some(d => d.is_downloaded || d.download_status === 'downloaded')) return false;
          if (stageFilter === 'LIVE' && !t.is_live) return false;
          if (stageFilter === 'UPCOMING' && !t.is_upcoming) return false;
          if (stageFilter === 'CLOSING_SOON' && !t.is_closing_soon) return false;

          // Search query match (state, kw, tender_id, title, description, or department)
          if (!q) return true;
          if (stateNameMatch || kwMatch) return true;
          const titleMatch = (t.title || '').toLowerCase().includes(q);
          const descMatch = (t.description || '').toLowerCase().includes(q);
          const idMatch = (t.tender_id || '').toLowerCase().includes(q);
          const deptMatch = (t.department || '').toLowerCase().includes(q);
          return titleMatch || descMatch || idMatch || deptMatch;
        });

        return { ...kw, tenders };
      }).filter(kw => filterKeyword === 'ALL' || kw.keyword === filterKeyword);

      const hasAnyTender = filteredKeywords.some(k => k.tenders.length > 0);
      if (q && !stateNameMatch && !hasAnyTender) {
        return null;
      }
      if (stageFilter !== 'ALL' && !hasAnyTender) {
        return null;
      }

      return {
        ...state,
        keywords: filteredKeywords
      };
    }).filter(Boolean).sort((a, b) => (a.state_name || '').localeCompare(b.state_name || ''));
  }, [reportData, searchStateQuery, filterKeyword, stageFilter, selectedState]);

  // State Names List across all 29 Indian States & UTs (Sorted Alphabetically A-Z)
  const allStateNames = useMemo(() => {
    if (reportData && reportData.length > 0) {
      return reportData.map(s => s.state_name).filter(Boolean).sort((a, b) => a.localeCompare(b));
    }
    return [
      "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
      "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", 
      "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", 
      "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", 
      "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
      "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
    ];
  }, [reportData]);

  // Calculate stats
  const totalStates = reportData.length;
  let totalTenders = 0;
  let liveActiveCount = 0;
  let upcomingCount = 0;
  let closingSoonCount = 0;
  let totalKeywordsSearched = 0;

  const allUniqueDocIds = new Set();
  const downloadedUniqueDocIds = new Set();

  reportData.forEach(state => {
    state.keywords.forEach(kw => {
      totalKeywordsSearched++;
      kw.tenders.forEach(t => {
        totalTenders++;
        if (t.stage === 'upcoming') {
          upcomingCount++;
        } else if (t.stage === 'closing_soon') {
          closingSoonCount++;
          liveActiveCount++;
        } else {
          liveActiveCount++;
        }

        if (t.documents) {
          t.documents.forEach(d => {
            const docKey = d.id || d.file_name;
            allUniqueDocIds.add(docKey);
            if (d.is_downloaded || d.download_status === 'downloaded') {
              downloadedUniqueDocIds.add(docKey);
            }
          });
        }
      });
    });
  });

  const totalDocsCount = allUniqueDocIds.size;
  const downloadedDocsCount = downloadedUniqueDocIds.size;

  // Interactive BASH Command Execution for Agent Terminal
  const handleRunTerminalCommand = (cmdText) => {
    const rawCmd = (typeof cmdText === 'string' ? cmdText : terminalCmdInput).trim();
    if (!rawCmd) return;
    setTerminalCmdInput('');

    const cmdEntry = {
      type: 'command',
      text: `gisfy-agent@procurements:~$ ${rawCmd}`,
      isUserCmd: true
    };

    const lower = rawCmd.toLowerCase();

    if (lower === 'clear' || lower === 'cls') {
      setLogs([
        { type: 'command', text: 'gisfy-agent@procurements:~$ clear', isUserCmd: true },
        { type: 'info', text: 'Terminal cleared. Type "help" or click quick action buttons above.', isUserCmd: true }
      ]);
      return;
    }

    if (lower === 'help') {
      setLogs(prev => [
        ...prev,
        cmdEntry,
        { type: 'info', text: '═════════════════ AGENT BASH COMMANDS ═════════════════', isUserCmd: true },
        { type: 'normal', text: '  • sync             - Trigger immediate 15-min portal sync across all 29 states', isUserCmd: true },
        { type: 'normal', text: '  • scrape <state>   - Trigger scraper for a state (e.g. "scrape AP" or "scrape Maharashtra")', isUserCmd: true },
        { type: 'normal', text: '  • download         - Start backend auto-downloader for pending proposals', isUserCmd: true },
        { type: 'normal', text: '  • status           - View live portal monitor timer & database document metrics', isUserCmd: true },
        { type: 'normal', text: '  • states / ls      - List all 29 Indian States & proposal breakdown', isUserCmd: true },
        { type: 'normal', text: '  • clear            - Clear terminal screen', isUserCmd: true },
        { type: 'info', text: '══════════════════════════════════════════════════════════', isUserCmd: true }
      ]);
      return;
    }

    if (lower === 'status' || lower === 'info') {
      const remainingMin = syncStatus?.seconds_remaining !== undefined 
        ? `${Math.floor(syncStatus.seconds_remaining / 60)}m ${syncStatus.seconds_remaining % 60}s` 
        : 'Active';
      setLogs(prev => [
        ...prev,
        cmdEntry,
        { type: 'info', text: '📊 AGENT SYSTEM METRICS:', isUserCmd: true },
        { type: 'normal', text: `  🏛️ States Monitored: ${totalStates} across India`, isUserCmd: true },
        { type: 'normal', text: `  🟢 Active Live Bids: ${liveActiveCount}`, isUserCmd: true },
        { type: 'normal', text: `  ⏳ Upcoming Proposals: ${upcomingCount}`, isUserCmd: true },
        { type: 'normal', text: `  ⚠️ Closing in ≤ 3 Days: ${closingSoonCount}`, isUserCmd: true },
        { type: 'normal', text: `  📁 Verified Documents on Disk: ${downloadedDocsCount} / ${totalDocsCount}`, isUserCmd: true },
        { type: 'normal', text: `  ⏳ Next 15-Min Live Portal Sync in: ${remainingMin} (Cycle #${syncStatus?.cycles_completed || 0})`, isUserCmd: true }
      ]);
      return;
    }

    if (lower === 'sync' || lower === 'sync-portals') {
      setLogs(prev => [
        ...prev,
        cmdEntry,
        { type: 'info', text: '🚀 [BASH] Executing live sync across all 29 official state portals...', isUserCmd: true }
      ]);
      handleTriggerLiveSync();
      return;
    }

    if (lower === 'download' || lower === 'auto-download') {
      setLogs(prev => [
        ...prev,
        cmdEntry,
        { type: 'info', text: '🚀 [BASH] Triggering backend automated downloader for pending proposals...', isUserCmd: true }
      ]);
      handleTriggerAutoDownload();
      return;
    }

    if (lower.startsWith('scrape')) {
      const parts = rawCmd.split(/\s+/);
      const stateTarget = parts.slice(1).join(' ').trim();
      if (!stateTarget) {
        setLogs(prev => [
          ...prev,
          cmdEntry,
          { type: 'warning', text: 'Usage: scrape <state_name> (e.g. "scrape AP", "scrape Maharashtra", "scrape Delhi")', isUserCmd: true }
        ]);
        return;
      }

      const match = reportData.find(s => 
        s.state_name.toLowerCase().includes(stateTarget.toLowerCase()) || 
        (stateTarget.toLowerCase() === 'ap' && s.state_name.toLowerCase().includes('andhra')) ||
        (stateTarget.toLowerCase() === 'up' && s.state_name.toLowerCase().includes('uttar'))
      );

      if (match) {
        setLogs(prev => [
          ...prev,
          cmdEntry,
          { type: 'info', text: `🚀 [BASH] Dispatching scraper agent to official portal for ${match.state_name}...`, isUserCmd: true }
        ]);
        handleTriggerStateScrape(match.state_name);
      } else {
        setLogs(prev => [
          ...prev,
          cmdEntry,
          { type: 'error', text: `bash: state "${stateTarget}" not found in 29 Indian States & UTs. Type "states" to view all.`, isUserCmd: true }
        ]);
      }
      return;
    }

    if (lower === 'states' || lower === 'ls') {
      const lines = reportData.map(s => {
        const count = s.keywords.reduce((acc, k) => acc + k.tenders.length, 0);
        return `  🏛️ ${s.state_name.padEnd(20, ' ')} : ${count} tenders (${s.downloaded_docs_count} verified files)`;
      });
      setLogs(prev => [
        ...prev,
        cmdEntry,
        { type: 'info', text: `=== ALL 29 MONITORED INDIAN STATES & UTs ===`, isUserCmd: true },
        ...lines.map(l => ({ type: 'normal', text: l, isUserCmd: true }))
      ]);
      return;
    }

    // Command not recognized
    setLogs(prev => [
      ...prev,
      cmdEntry,
      { type: 'error', text: `bash: ${rawCmd}: command not found. Type "help" to see available commands.`, isUserCmd: true }
    ]);
  };

  return (
    <div className="app-container">
      {/* Toast Alert */}
      {toast && (
        <div className={`toast-notification ${toast.type}`}>
          <span className="toast-text">{toast.message}</span>
          <button className="toast-close" onClick={() => setToast(null)}>✕</button>
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="header-brand-wrap">
            <button 
              className="gisfy-logo-btn"
              onClick={() => setShowGisfyModal(true)}
              title="Click to view GISFY details (Powered by GISFY)"
            >
              <img src="/gisfy_logo.png" alt="GISFY - Building a Smart World" className="gisfy-header-logo" />
            </button>
            <div className="header-text-block">
              <h1>Agentic Procurements</h1>
              <p className="header-subtitle">Real-Time State Portal Scraper & Document Automation across all 29 Indian States & UTs</p>
            </div>
          </div>
        </div>
        <div className="header-actions">
          <div 
            className="gisfy-brand-widget"
            onClick={() => setShowGisfyModal(true)}
            title="Click to view Powered by GISFY enterprise details"
          >
            <div className="gisfy-capsule-pill">
              <span className="gisfy-capsule-label">POWERED BY</span>
              <img src="/gisfy_logo.png" alt="GISFY" className="gisfy-capsule-logo" />
            </div>
            <div className="gisfy-circle-button">
              <img src="/gisfy_logo.png" alt="GISFY" className="gisfy-circle-logo" />
            </div>
          </div>
          <button 
            className={`auto-dl-btn ${autoDownloading ? 'loading' : ''}`}
            onClick={handleTriggerAutoDownload}
            disabled={autoDownloading}
            title="Trigger backend downloader to automatically verify all pending documents"
          >
            {autoDownloading ? '⚡ Downloading in Backend...' : '⚡ Run Backend Auto-Download'}
          </button>
          <button 
            className={`auto-compress-btn ${compressingAll ? 'loading' : ''}`}
            onClick={handleCompressAllLargePdfs}
            disabled={compressingAll}
            title="Scan and compress all large MB/GB PDF files across all 29 states to optimize storage and loading speed"
          >
            {compressingAll ? '🗜️ Compressing PDFs...' : '🗜️ Compress Large PDFs'}
          </button>
          <button 
            className="email-team-header-btn"
            onClick={() => openEmailModal({ scope: selectedState ? 'state' : 'all', stateName: selectedState })}
            title="Dispatch state procurement proposals and attached documents through email to team members"
          >
            ✉️ Email Team
          </button>
          <button 
            id="collab-partners-header-btn"
            className="collab-partners-header-btn"
            onClick={() => openPartnersModal({ tender: null })}
            title="Search & identify collaboration partners, JV consortiums, and specialized capability providers based on tenders"
          >
            🤝 Collaboration Partners
            {partnersSummary?.total_partners > 0 && (
              <span className="partners-count-badge">{partnersSummary.total_partners}</span>
            )}
          </button>

          <a
            href={`${API_BASE}/api/reports/proposals-excel`}
            className="excel-export-header-btn"
            target="_blank"
            rel="noopener noreferrer"
            title="Download Master Excel Spreadsheet containing all states, keywords, proposals, and document download links"
          >
            📥 Export to Excel (.xlsx)
          </a>
          <a
            href={`${API_BASE}/api/reports/excel-view`}
            className="excel-export-header-btn"
            style={{ background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)' }}
            target="_blank"
            rel="noopener noreferrer"
            title="Open Interactive Spreadsheet Table in Browser"
          >
            📊 Spreadsheet Grid
          </a>
          <div className="status-badge">
            <div className="pulse"></div>
            Agent Online & Active
          </div>
        </div>
      </header>

      {/* 15-Minute Live Portal Sync Command Bar */}
      <section className="live-sync-bar">
        <div className="sync-left">
          <div className="sync-pulse-indicator">
            <span className="live-radar-dot"></span>
            <span className="sync-title">15-MINUTE LIVE PORTAL MONITOR</span>
            <span className="sync-badge-active">AUTO-SYNC ACTIVE</span>
          </div>
          <div className="sync-countdown">
            <span className="timer-icon">⏳</span> Next portal update in: 
            <b className="timer-val">
              {syncStatus?.seconds_remaining !== undefined 
                ? `${Math.floor(syncStatus.seconds_remaining / 60).toString().padStart(2, '0')}:${(syncStatus.seconds_remaining % 60).toString().padStart(2, '0')}`
                : '15:00'}
            </b>
          </div>
          <div className="sync-last-time" title={syncStatus?.last_sync_time ? formatDateTimeDMY(syncStatus.last_sync_time) : ''}>
            Last cycle: {syncStatus?.last_sync_time ? formatDateTimeDMY(syncStatus.last_sync_time) : 'Active'} 
            {syncStatus?.cycles_completed > 0 && ` (Cycle #${syncStatus.cycles_completed})`}
          </div>
        </div>

        <div className="sync-right">
          <button 
            className="simulate-portal-btn"
            onClick={() => setShowSimulateModal(true)}
            title="Test a new tender notification arriving from any state portal"
          >
            ⚡ Test Portal Notification
          </button>
          <button 
            className={`sync-now-btn ${syncingNow || syncStatus?.is_syncing ? 'spinning' : ''}`}
            onClick={handleTriggerLiveSync}
            disabled={syncingNow || syncStatus?.is_syncing}
            title="Poll all 29 official government portals immediately for new and upcoming tenders"
          >
            {syncingNow || syncStatus?.is_syncing ? '🔄 Syncing 29 Portals...' : '🔄 Sync Portals Now (15-Min Check)'}
          </button>
        </div>
      </section>

      {/* Real-Time Live Proposal Alert Banner */}
      {newTenderAlert && (
        <section className="new-tender-live-banner" role="alert">
          <div className="banner-left-glow">
            <div className="banner-bell-wrapper">
              <span className="banner-bell-icon">🔔</span>
              <span className="banner-bell-pulse"></span>
            </div>
            <div className="banner-content">
              <div className="banner-headline">
                <span className="badge-new-alert">NEW PROPOSAL ADDED</span>
                <span className="badge-state-alert">🏛️ {newTenderAlert.state_name}</span>
                <span className="badge-ref-alert">Ref #{newTenderAlert.tender_id}</span>
                <span className="banner-time-badge" title={newTenderAlert.ingested_at ? formatDateTimeDMY(newTenderAlert.ingested_at) : ''}>
                  {newTenderAlert.ingested_at ? formatDateTimeDMY(newTenderAlert.ingested_at) : 'Live'}
                </span>
              </div>
              <div className="banner-tender-title" title={newTenderAlert.title}>
                {newTenderAlert.title}
              </div>
              <div className="banner-tender-sub">
                <span className="sub-dept">🏢 {newTenderAlert.department || 'Official State Directorate'}</span>
                <span className="sub-sep">•</span>
                <span className="sub-kw">🏷️ Keyword: <b>{newTenderAlert.keyword}</b></span>
                <span className="sub-sep">•</span>
                <span className="sub-docs">📄 <b>{newTenderAlert.documents_count || 4} Authentic Documents</b> verified & ready on disk</span>
              </div>
            </div>
          </div>
          <div className="banner-actions">
            <button 
              className="btn-view-new-tender"
              onClick={() => handleViewNewProposal(newTenderAlert)}
              title="Navigate directly to this proposal on the website"
            >
              <span>🔍 View Proposal</span>
              <span className="arrow-icon">↗</span>
            </button>
            <button 
              className="btn-close-new-tender"
              onClick={() => setNewTenderAlert(null)}
              title="Dismiss notification"
            >
              ✕
            </button>
          </div>
        </section>
      )}

      {/* Stats Row */}
      <section className="stats-row">
        <div className="stat-card">
          <div className="stat-label">States Monitored</div>
          <div className="stat-value">{totalStates}</div>
          <div className="stat-sub">Across 29 Indian States & UTs</div>
        </div>
        <div className="stat-card stat-live">
          <div className="stat-label">🟢 Live Active Bids</div>
          <div className="stat-value accent">{liveActiveCount}</div>
          <div className="stat-sub">Currently Open for Bidding</div>
        </div>
        <div className="stat-card stat-upcoming">
          <div className="stat-label">⏳ Upcoming Proposals</div>
          <div className="stat-value info">{upcomingCount}</div>
          <div className="stat-sub">Scheduled for Future Opening</div>
        </div>
        <div className="stat-card stat-closing">
          <div className="stat-label">⚠️ Closing Soon</div>
          <div className="stat-value warning">{closingSoonCount}</div>
          <div className="stat-sub">Deadline in ≤ 3 Days</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Original Documents</div>
          <div className="stat-value success">{downloadedDocsCount} <span className="stat-sub-val">/ {totalDocsCount}</span></div>
          <div className="stat-sub">100% Genuine Files on Disk</div>
        </div>
      </section>

      {/* Layout Controls Bar */}
      <div className="layout-controls-bar">
        <div className="layout-toggle-group">
          <button 
            className={`layout-btn ${isSidebarOpen ? 'active' : ''}`}
            onClick={() => setIsSidebarOpen(prev => !prev)}
            title="Toggle States & UTs Directory Sidebar"
          >
            🏛️ {isSidebarOpen ? 'Hide States Sidebar' : 'Show States Sidebar (29)'}
          </button>
          <button 
            className={`layout-btn ${isTerminalOpen ? 'active' : ''}`}
            onClick={() => setIsTerminalOpen(prev => !prev)}
            title="Toggle Agent Terminal Live Stream"
          >
            💻 {isTerminalOpen ? 'Hide Terminal Feed' : 'Show Terminal Feed'}
          </button>
        </div>

        {selectedState ? (
          <div className="layout-filter-indicator">
            <span>Filtered by State:</span>
            <span className="filter-active-pill">🏛️ {selectedState}</span>
            {selectedSidebarKw && (
              <span className="filter-active-pill" style={{ background: '#fef3c7', color: '#b45309' }}>
                🏷️ {selectedSidebarKw}
              </span>
            )}
            <button 
              className="clear-filter-link"
              onClick={() => { setSelectedState(null); setSelectedSidebarKw(null); }}
              title="Reset to view all 29 states"
            >
              ✕ Show All States
            </button>
          </div>
        ) : (
          <div className="layout-filter-indicator" style={{ color: '#64748b' }}>
            <span>🌐 Showing All 29 Indian States & UTs</span>
          </div>
        )}
      </div>

      {/* Main Grid with States Sidebar, Results, and Terminal */}
      <div className={`dashboard-grid ${!isSidebarOpen ? 'no-sidebar' : ''} ${!isTerminalOpen ? 'no-terminal' : ''}`}>
        {/* Left Sidebar: 29 States Directory (Simple & Clean Format) */}
        {isSidebarOpen && (
          <aside className="states-sidebar">
            <div className="sidebar-header">
              <div className="sidebar-header-top">
                <span className="sidebar-header-title">
                  <span>🏛️</span> States Directory
                </span>
                <span className="sidebar-count-badge">29 States</span>
              </div>

              <div className="sidebar-search-box">
                <span className="sidebar-search-icon">🔍</span>
                <input 
                  type="text"
                  placeholder="Filter 29 states (e.g. Maharashtra, AP)..."
                  value={sidebarSearch}
                  onChange={(e) => setSidebarSearch(e.target.value)}
                />
                {sidebarSearch && (
                  <button 
                    className="sidebar-search-clear-btn"
                    onClick={() => setSidebarSearch('')}
                    title="Clear search"
                  >
                    ✕
                  </button>
                )}
              </div>

              <div className="sidebar-filter-pills">
                <button 
                  className={`sidebar-filter-pill ${sidebarFilter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setSidebarFilter('ALL')}
                >
                  All (29)
                </button>
                <button 
                  className={`sidebar-filter-pill ${sidebarFilter === 'READY' ? 'active' : ''}`}
                  onClick={() => setSidebarFilter('READY')}
                  title="States with authentic files downloaded on disk"
                >
                  ✓ With Files
                </button>
                <button 
                  className={`sidebar-filter-pill ${sidebarFilter === 'ACTIVE' ? 'active' : ''}`}
                  onClick={() => setSidebarFilter('ACTIVE')}
                  title="States with active live tenders"
                >
                  🟢 Active Live
                </button>
              </div>

              <button 
                className={`sidebar-all-overview-btn ${selectedState === null ? 'active' : ''}`}
                onClick={() => { setSelectedState(null); setSelectedSidebarKw(null); }}
              >
                <span>🌐 All States Overview</span>
                <span className="badge-bid-count">{totalTenders} bids</span>
              </button>
            </div>

            <div className="sidebar-state-list">
              {filteredSidebarStates.map((state, sIdx) => {
                const stateTendersCount = state.keywords.reduce((acc, k) => acc + k.tenders.length, 0);
                const isSelected = selectedState === state.state_name;
                const isExpanded = expandedSidebarStates[state.state_name];

                return (
                  <div 
                    key={sIdx} 
                    className={`sidebar-state-group ${isSelected ? 'selected' : ''}`}
                  >
                    {/* Clean single-line State row */}
                    <div 
                      className={`sidebar-state-item ${isSelected ? 'active' : ''}`}
                      onClick={() => handleSelectSidebarState(state.state_name)}
                      title={`Click to view keywords & tenders for ${state.state_name}`}
                    >
                      <div className="sidebar-state-item-left">
                        <span className="sidebar-state-item-icon">🏛️</span>
                        <span className="sidebar-state-item-name">{state.state_name}</span>
                      </div>
                      <div className="sidebar-state-item-right">
                        {state.downloaded_docs_count > 0 && (
                          <span className="sidebar-doc-pill" title={`${state.downloaded_docs_count} genuine files ready on disk`}>
                            ✓ {state.downloaded_docs_count}
                          </span>
                        )}
                        <span className="sidebar-bid-pill">{stateTendersCount}</span>
                        <span className={`sidebar-chevron-arrow ${isExpanded ? 'open' : ''}`}>
                          {isExpanded ? '▾' : '▸'}
                        </span>
                      </div>
                    </div>

                    {/* Keywords sub-level: clean, indented list */}
                    {isExpanded && (
                      <div className="sidebar-kw-sublist">
                        {state.keywords.map((kw, kIdx) => {
                          const stats = getKeywordStats(kw);
                          const kwKey = `${state.state_name}-${kw.keyword}`;
                          const isKwExpanded = expandedSidebarKws[kwKey];
                          const hasResults = stats.tendersCount > 0;
                          const isKwSelected = selectedSidebarKw === kw.keyword && isSelected;

                          return (
                            <div key={kIdx} className="sidebar-kw-group">
                              <div 
                                className={`sidebar-kw-item ${isKwSelected ? 'active' : ''} ${hasResults ? 'has-bids' : 'empty'}`}
                                onClick={(e) => handleSelectSidebarKeyword(state.state_name, kw.keyword, e)}
                                title={`Click to show ${kw.keyword} documents`}
                              >
                                <div className="sidebar-kw-item-left">
                                  <span className="sidebar-kw-bullet">🏷️</span>
                                  <span className="sidebar-kw-label">{kw.keyword}</span>
                                </div>
                                <div className="sidebar-kw-item-right">
                                  {hasResults ? (
                                    <>
                                      <span className="sidebar-kw-count-text">
                                        {stats.totalDocs} docs ({stats.pdfCount} PDFs)
                                      </span>
                                      <span className="sidebar-kw-arrow">{isKwExpanded ? '▾' : '▸'}</span>
                                    </>
                                  ) : (
                                    <span className="sidebar-kw-zero">0</span>
                                  )}
                                </div>
                              </div>

                              {/* Document sub-level: clean compact rows */}
                              {isKwExpanded && stats.totalDocs > 0 && (
                                <div className="sidebar-doc-compact-list">
                                  <div className="sidebar-doc-compact-header">
                                    <span>📄 {stats.totalDocs} Files Found</span>
                                    <span className="pdf-tag">📕 {stats.pdfCount} PDFs</span>
                                  </div>

                                  {stats.docsList.map((doc, dIdx) => (
                                    <div key={dIdx} className="sidebar-doc-compact-row">
                                      <span className={`file-badge-mini ${doc.isPdf ? 'pdf' : (doc.file_type === '.zip' || (doc.file_name || '').endsWith('.zip') ? 'zip' : 'doc')}`}>
                                        {doc.isPdf ? 'PDF' : (doc.file_type ? doc.file_type.replace('.', '').toUpperCase() : 'DOC')}
                                      </span>
                                      <span 
                                        className="sidebar-doc-compact-name" 
                                        title={doc.file_name}
                                        onClick={(e) => openPreview(doc, null, state.state_name, e)}
                                      >
                                        {doc.file_name}
                                      </span>
                                      <div className="sidebar-doc-compact-btns">
                                        <button 
                                          className="sidebar-btn-xs preview"
                                          onClick={(e) => openPreview(doc, null, state.state_name, e)}
                                          title="View content preview"
                                        >
                                          👁 View
                                        </button>
                                        <button 
                                          className="sidebar-btn-xs download"
                                          onClick={(e) => handleDownloadDocument(doc, e)}
                                          disabled={downloadingId === (doc.id || doc.file_name)}
                                          title="Download original document"
                                        >
                                          {downloadingId === (doc.id || doc.file_name) ? '⏳' : '⬇ Save'}
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
              {filteredSidebarStates.length === 0 && (
                <div style={{ padding: '1rem', textAlign: 'center', color: '#64748b', fontSize: '0.84rem' }}>
                  No state matches "{sidebarSearch}".
                </div>
              )}
            </div>
          </aside>
        )}

        {/* States Section */}
        <section className="states-section">
          {/* Streamlined Breadcrumb Context Bar */}
          {selectedState && (
            <div className="state-selection-banner">
              <div className="banner-left">
                <span className="banner-breadcrumb-link" onClick={() => { setSelectedState(null); setSelectedSidebarKw(null); }}>
                  🌐 All 29 States
                </span>
                <span className="banner-breadcrumb-sep">›</span>
                <span className="banner-breadcrumb-current">🏛️ {selectedState}</span>
                {selectedSidebarKw && (
                  <>
                    <span className="banner-breadcrumb-sep">›</span>
                    <span className="banner-breadcrumb-kw">🏷️ {selectedSidebarKw}</span>
                  </>
                )}
              </div>
              <div className="banner-right" style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                <button 
                  className="email-state-banner-btn"
                  onClick={() => openEmailModal({ scope: 'state', stateName: selectedState })}
                  title={`Email ${selectedState} proposals and documents to team members`}
                >
                  ✉️ Email {selectedState} Docs
                </button>
                <button 
                  className="view-all-states-btn"
                  onClick={() => { setSelectedState(null); setSelectedSidebarKw(null); }}
                  title="Return to viewing all 29 states"
                >
                  ✕ Show All 29 States
                </button>
              </div>
            </div>
          )}

          <div className="section-header-bar">
            <h2>{selectedState ? `Proposals for ${selectedState}` : 'State Results & Tender Documents'}</h2>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button 
                className="email-section-btn"
                onClick={() => openEmailModal({ scope: selectedState ? 'state' : 'all', stateName: selectedState })}
                title="Dispatch state details and documents to team members"
              >
                ✉️ Email {selectedState ? `${selectedState} Docs` : 'Proposals to Team'}
              </button>
              <button className="refresh-btn" onClick={() => { fetchReport(); fetchLogs(); fetchSyncStatus(); }} title="Refresh results">
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Proposal Stage Filter Tabs */}
          <div className="stage-filter-tabs">
            <button 
              className={`stage-tab ${stageFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStageFilter('ALL')}
            >
              🌐 All Proposals ({totalTenders})
            </button>
            <button 
              className={`stage-tab ${stageFilter === 'DOWNLOADED_ONLY' ? 'active' : ''}`}
              onClick={() => setStageFilter('DOWNLOADED_ONLY')}
              style={stageFilter === 'DOWNLOADED_ONLY' ? { background: '#059669', color: '#ffffff', borderColor: '#059669', fontWeight: 600 } : { borderColor: '#10b981', color: '#047857' }}
              title="Filter directly to tenders with authentic original files downloaded on disk"
            >
              📥 100% Original Files Ready ({downloadedDocsCount})
            </button>
            <button 
              className={`stage-tab live ${stageFilter === 'LIVE' ? 'active' : ''}`}
              onClick={() => setStageFilter('LIVE')}
            >
              🟢 Live Active ({liveActiveCount})
            </button>
            <button 
              className={`stage-tab upcoming ${stageFilter === 'UPCOMING' ? 'active' : ''}`}
              onClick={() => setStageFilter('UPCOMING')}
            >
              ⏳ Upcoming ({upcomingCount})
            </button>
            <button 
              className={`stage-tab closing ${stageFilter === 'CLOSING_SOON' ? 'active' : ''}`}
              onClick={() => setStageFilter('CLOSING_SOON')}
            >
              ⚠️ Closing Soon ({closingSoonCount})
            </button>
          </div>

          {/* Search & Filter Bar */}
          <div className="filter-toolbar">
            <div className="search-input-box">
              <span className="search-icon">🔍</span>
              <input 
                type="text" 
                placeholder="Search States, Tenders, or Keywords (Design, Blockchain, Digital, Empanelment)..."
                value={searchStateQuery}
                onChange={(e) => setSearchStateQuery(e.target.value)}
              />
            </div>
            <select 
              className="filter-select"
              value={filterKeyword}
              onChange={(e) => setFilterKeyword(e.target.value)}
            >
              <option value="ALL">🏷️ All Keywords ({allKeywordOptions.length})</option>
              {allKeywordOptions.map((kw, i) => (
                <option key={i} value={kw}>🏷️ {kw}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <span>Loading procurement portal data...</span>
            </div>
          ) : (
            <div className="states-grid">
              {filteredReportData.map((state, idx) => {
                const stateTenders = state.keywords.reduce((acc, kw) => acc + kw.tenders.length, 0);
                const isCurrentlyScraping = scrapingState === state.state_name;
                
                return (
                  <div className="state-card" key={idx}>
                    <div className="state-header">
                      <div>
                        <h3>{state.state_name}</h3>
                        <span className="state-sub">
                          {state.downloaded_docs_count > 0 
                            ? `🟢 ${state.downloaded_docs_count} Authentic Original Documents Ready for Instant Download` 
                            : `🏛️ Official e-Procurement Portal Directory`}
                        </span>
                      </div>
                      <div className="state-actions-row">
                        {state.downloaded_docs_count > 0 && (
                          <span className="authentic-badge-pill" style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '0.25rem 0.6rem', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600 }}>
                            ✓ {state.downloaded_docs_count} Original Files Ready
                          </span>
                        )}
                        <button 
                          className="email-state-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            openEmailModal({ scope: 'state', stateName: state.state_name });
                          }}
                          title={`Email ${state.state_name} proposals and documents to team members`}
                        >
                          ✉️ Email State Docs
                        </button>
                        <button 
                          className="scrape-state-btn"
                          onClick={(e) => handleTriggerStateScrape(state.state_name, e)}
                          disabled={isCurrentlyScraping}
                          title={`Trigger live crawler for ${state.state_name}`}
                        >
                          {isCurrentlyScraping ? '⏳ Crawling...' : '⚡ Scrape Portal'}
                        </button>
                        <span className="total-tenders">{stateTenders} Tenders</span>
                      </div>
                    </div>

                    <div className="keyword-list">
                      {state.keywords
                        .filter(kw => filterKeyword === 'ALL' || kw.keyword === filterKeyword)
                        .map((kw, i) => {
                          const isExpanded = expandedKw[`${state.state_name}-${kw.keyword}`];
                          const hasResults = kw.tenders.length > 0;
                          const kwStats = getKeywordStats(kw);
                          
                          return (
                            <div className="keyword-wrapper" key={i}>
                              <div 
                                className={`keyword-item ${hasResults ? 'clickable' : 'empty'}`} 
                                onClick={() => hasResults && toggleExpand(state.state_name, kw.keyword)}
                              >
                                <div className="kw-item-left">
                                  <span className="kw-name">🏷️ {kw.keyword}</span>
                                  <span className={`kw-count ${hasResults ? 'has-results' : ''}`}>
                                    {kw.tenders.length} {kw.tenders.length === 1 ? 'proposal' : 'proposals'}
                                  </span>
                                </div>
                                <div className="kw-item-right">
                                  {hasResults && (
                                    <span className="kw-docs-badge">
                                      📄 {kwStats.totalDocs} docs • <span className="pdf-tag">📕 {kwStats.pdfCount} PDFs</span>
                                    </span>
                                  )}
                                  {hasResults && (
                                    <span className="expand-indicator">{isExpanded ? '▼' : '▶'}</span>
                                  )}
                                </div>
                              </div>
                              
                              {isExpanded && hasResults && (
                                <div className="tenders-dropdown">
                                  {/* Keyword Documents and PDFs Breakdown Bar */}
                                  <div className="kw-docs-summary-bar">
                                    <div className="summary-col">
                                      <span className="summary-title">📁 Documentation Breakdown for "{kw.keyword}":</span>
                                    </div>
                                    <div className="summary-badges-group">
                                      <span className="doc-pill total">
                                        📄 <b>{kwStats.totalDocs}</b> Documents Total
                                      </span>
                                      <span className="doc-pill pdf">
                                        📕 <b>{kwStats.pdfCount}</b> PDF Files
                                      </span>
                                      {kwStats.zipCount > 0 && (
                                        <span className="doc-pill zip">
                                          📦 <b>{kwStats.zipCount}</b> Archives (.zip)
                                        </span>
                                      )}
                                      {kwStats.downloadedCount > 0 && (
                                        <span className="doc-pill ready">
                                          🟢 <b>{kwStats.downloadedCount}</b> Original Files Ready on Disk
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {kw.tenders.map((tender, tIdx) => (
                                    <div 
                                      id={`tender-${tender.tender_id}`}
                                      className={`tender-item ${highlightedTenderId === tender.tender_id ? 'new-tender-highlighted' : ''}`} 
                                      key={tIdx}
                                    >
                                      <div className="tender-header-row">
                                        <div className="tender-id-badge">ID: {tender.tender_id}</div>
                                        {highlightedTenderId === tender.tender_id && (
                                          <span className="stage-pill newly-added-pulse">🔔 NEW PROPOSAL ADDED</span>
                                        )}
                                        {tender.stage === 'upcoming' && (
                                          <span className="stage-pill upcoming">⏳ UPCOMING</span>
                                        )}
                                        {tender.stage === 'closing_soon' && (
                                          <span className="stage-pill closing">⚠️ CLOSING IN {tender.days_left}D</span>
                                        )}
                                        {tender.stage === 'live' && (
                                          <span className="stage-pill live">🟢 LIVE ACTIVE</span>
                                        )}
                                        <span 
                                          className="stage-pill collab-indicator"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            openPartnersModal({ tender: tender, stateName: state.state_name });
                                          }}
                                          title="View matched JV & consortium partners for this tender"
                                        >
                                          🤝 JV Partner Match
                                        </span>
                                        {tender.department && (
                                          <div className="tender-dept">{tender.department}</div>
                                        )}
                                        <button 
                                          className="collab-partner-tender-btn"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            openPartnersModal({ tender: tender, stateName: state.state_name });
                                          }}
                                          title={`Search and view collaboration partners for Tender #${tender.tender_id}`}
                                        >
                                          🤝 Collaboration Partners
                                        </button>
                                        <button 
                                          className="bundle-dl-btn"
                                          onClick={(e) => handleDownloadBundle(tender, e)}

                                          disabled={downloadingTenderId === tender.id}
                                          title="Download all documents of this tender as a ZIP archive"
                                        >
                                          {downloadingTenderId === tender.id ? '⏳ Zipping...' : '📦 Download Bundle (.zip)'}
                                        </button>
                                        <button 
                                          className="email-tender-btn"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            openEmailModal({ scope: 'tender', stateName: state.state_name, tender: tender });
                                          }}
                                          title={`Email Tender #${tender.tender_id} and its documents to team members`}
                                        >
                                          ✉️ Email Team
                                        </button>
                                      </div>

                                      <div className="tender-title">📄 {tender.title}</div>

                                      {tender.description && (
                                        <div className="tender-desc-text" style={{ fontSize: '0.82rem', color: '#475569', margin: '0.3rem 0', background: '#f8fafc', padding: '0.4rem 0.6rem', borderRadius: '6px' }}>
                                          ℹ️ {tender.description}
                                        </div>
                                      )}
                                      
                                      {(tender.published_date || tender.last_date) && (
                                        <div className="tender-meta-dates">
                                          {tender.published_date && (
                                            <span>📅 Published: {formatDateDMY(tender.published_date)}</span>
                                          )}
                                          {tender.last_date && (
                                            <span className="due-date">⏰ Due Date: {formatDateDMY(tender.last_date)}</span>
                                          )}
                                          {tender.portal_tender_url && (
                                            <a 
                                              href={tender.portal_tender_url} 
                                              target="_blank" 
                                              rel="noopener noreferrer"
                                              style={{ color: 'var(--accent-primary)', fontSize: '0.78rem', textDecoration: 'none', marginLeft: 'auto' }}
                                            >
                                              🔗 Portal Link ↗
                                            </a>
                                          )}
                                        </div>
                                      )}

                                      <div className="tender-docs-container">
                                        {(() => {
                                          const docs = tender.documents || [];
                                          const topLevelCount = docs.length;
                                          const totalExtractedCount = docs.reduce((acc, d) => acc + (d.sub_documents?.length || 0), 0);
                                          return (
                                            <div className="docs-label">
                                              ATTACHED PROPOSAL DOCUMENTS ({topLevelCount} Portal Files{totalExtractedCount > 0 ? ` · ${totalExtractedCount} Extracted Sections` : ''}):
                                            </div>
                                          );
                                        })()}
                                        <div className="tender-docs">
                                          {tender.documents && tender.documents.length > 0 ? (
                                            tender.documents.map((doc, dIdx) => {
                                              const isDownloaded = doc.is_downloaded || (doc.download_status === 'downloaded');
                                              const isCurrentDownloading = downloadingId === (doc.id || doc.file_name);
                                              const extBadge = (doc.file_type || doc.file_name.split('.').pop() || 'doc').toUpperCase().replace('.', '');
                                              const archiveKey = `${tender.id || tender.tender_id}-${doc.id || doc.file_name}`;
                                              const hasSubDocs = Array.isArray(doc.sub_documents) && doc.sub_documents.length > 0;
                                              const isArchiveExpanded = !!expandedArchives[archiveKey];

                                              if (doc.is_bundle) {
                                                return (
                                                  <div 
                                                    className={`doc-card bundle-package-card ${isDownloaded ? "ready-card" : ""}`} 
                                                    key={dIdx}
                                                    onClick={(e) => openPreview(doc, tender, state.state_name, e)}
                                                    title="All-in-One Compressed ZIP package containing all document files of this tender"
                                                    style={{ cursor: 'pointer' }}
                                                  >
                                                    <div className="doc-main-info">
                                                      <span className="file-badge badge-zip-bundle">
                                                        📦 ZIP BUNDLE
                                                      </span>
                                                      <div className="doc-details">
                                                        <div className="doc-title bundle-title" title={doc.file_name}>
                                                          <b>📦 {doc.file_name}</b>
                                                        </div>
                                                        <div className="doc-sub-info">
                                                          <span className="bundle-tag-pill">
                                                            🗜️ ALL-IN-ONE COMPRESSED PACKAGE ({doc.bundle_file_count || 'ALL'} FILES)
                                                          </span>
                                                          <span className="status-pill ready">🟢 Verified on Disk</span>
                                                          {doc.file_size_kb && (
                                                            <span className="size-pill bundle-size">{doc.file_size_kb} KB</span>
                                                          )}
                                                        </div>
                                                      </div>
                                                    </div>

                                                    <div className="doc-actions" onClick={(e) => e.stopPropagation()}>
                                                      <button 
                                                        className="doc-btn preview-btn"
                                                        onClick={(e) => openPreview(doc, tender, state.state_name, e)}
                                                        title="Inspect archive contents and view individual documents"
                                                      >
                                                        👁️ Inspect Archive
                                                      </button>
                                                      
                                                      <button 
                                                        className="doc-btn download-action-btn bundle-download-btn"
                                                        onClick={(e) => handleDownloadDocument(doc, e)}
                                                        disabled={isCurrentDownloading}
                                                        title="Download complete compressed package with all files for this tender"
                                                      >
                                                        {isCurrentDownloading ? '⏳ Downloading...' : '📦 Download All Files (.zip)'}
                                                      </button>
                                                    </div>
                                                  </div>
                                                );
                                              }

                                              return (
                                                <div className="doc-group-container" key={dIdx}>
                                                  <div 
                                                    className={`doc-card ${isDownloaded ? "ready-card" : ""} ${hasSubDocs ? "parent-archive-card" : ""}`} 
                                                    onClick={(e) => hasSubDocs ? toggleArchiveExpansion(archiveKey, e) : openPreview(doc, tender, state.state_name, e)}
                                                    title={hasSubDocs ? "Click to toggle unpacked section documents" : "Click to preview authentic document content and information"}
                                                    style={{ cursor: 'pointer' }}
                                                  >
                                                    <div className="doc-main-info">
                                                      <span className={`file-badge badge-${extBadge.toLowerCase()}`}>
                                                        {extBadge}
                                                      </span>
                                                      <div className="doc-details">
                                                        <span className="doc-title" title={doc.file_name}>
                                                          {doc.file_name}
                                                        </span>
                                                        <div className="doc-sub-info">
                                                          <span className={`status-pill ${isDownloaded ? 'ready' : 'pending'}`}>
                                                            {isDownloaded ? '🟢 Original File Ready' : '🏛️ Govt Portal Notice'}
                                                          </span>
                                                          {doc.is_large && (
                                                            <span className="large-pdf-pill">
                                                              🗜️ Large PDF ({(doc.file_size_kb / 1024).toFixed(1)} MB)
                                                            </span>
                                                          )}
                                                          {doc.file_size_kb && (
                                                            <span className="size-pill">{doc.file_size_kb} KB</span>
                                                          )}
                                                          {hasSubDocs && (
                                                            <button 
                                                              type="button"
                                                              className={`archive-expand-pill ${isArchiveExpanded ? 'expanded' : ''}`}
                                                              onClick={(e) => toggleArchiveExpansion(archiveKey, e)}
                                                              title={isArchiveExpanded ? "Collapse extracted sections" : "Expand to view unpacked sections"}
                                                            >
                                                              📂 {doc.sub_documents.length} Extracted Sections {isArchiveExpanded ? '▲ Hide' : '▼ Expand'}
                                                            </button>
                                                          )}
                                                        </div>
                                                      </div>
                                                    </div>

                                                    <div className="doc-actions" onClick={(e) => e.stopPropagation()}>
                                                      {hasSubDocs && (
                                                        <button 
                                                          className={`doc-btn expand-action-btn ${isArchiveExpanded ? 'active' : ''}`}
                                                          onClick={(e) => toggleArchiveExpansion(archiveKey, e)}
                                                          title={isArchiveExpanded ? "Collapse section list" : "Expand section list"}
                                                        >
                                                          {isArchiveExpanded ? '▲ Hide Sections' : `📂 View Sections (${doc.sub_documents.length})`}
                                                        </button>
                                                      )}

                                                      {doc.is_large && (
                                                        <button 
                                                          className="doc-btn compress-action-btn"
                                                          onClick={(e) => handleCompressPdf(doc, e)}
                                                          disabled={compressingDocId === doc.id}
                                                          title="Compress this large PDF to optimize file size"
                                                        >
                                                          {compressingDocId === doc.id ? '⏳ Compacting...' : '🗜️ Compress PDF'}
                                                        </button>
                                                      )}

                                                      <button 
                                                        className="doc-btn preview-btn"
                                                        onClick={(e) => openPreview(doc, tender, state.state_name, e)}
                                                        title="Preview this proposal document and view complete details"
                                                      >
                                                        👁 Content
                                                      </button>
                                                      
                                                      <button 
                                                        className="doc-btn download-action-btn"
                                                        onClick={(e) => handleDownloadDocument(doc, e)}
                                                        disabled={isCurrentDownloading}
                                                        title="Download original document directly to your device"
                                                      >
                                                        {isCurrentDownloading ? '⏳ Downloading...' : (isDownloaded ? '⬇ Download Original' : '🏛️ Download from Portal')}
                                                      </button>
                                                    </div>
                                                  </div>

                                                  {/* Expandable Sub-Documents Accordion Tray */}
                                                  {hasSubDocs && isArchiveExpanded && (
                                                    <div className="sub-docs-tray">
                                                      <div className="sub-docs-tray-header">
                                                        <div className="sub-docs-header-title">
                                                          📂 Extracted Sections from <b>{doc.file_name}</b> ({doc.sub_documents.length} files)
                                                        </div>
                                                        <div className="sub-docs-header-subtitle">
                                                          Unpacked from the official government portal archive for instant search & preview:
                                                        </div>
                                                      </div>
                                                      <div className="sub-docs-list">
                                                        {doc.sub_documents.map((subDoc, sIdx) => {
                                                          const subExt = (subDoc.file_type || subDoc.file_name.split('.').pop() || 'pdf').toUpperCase().replace('.', '');
                                                          const isSubDownloading = downloadingId === (subDoc.id || subDoc.file_name);
                                                          return (
                                                            <div 
                                                              className="sub-doc-row" 
                                                              key={sIdx}
                                                              onClick={(e) => openPreview(subDoc, tender, state.state_name, e)}
                                                              title="Preview this authentic section"
                                                            >
                                                              <div className="sub-doc-left">
                                                                <span className={`file-badge badge-${subExt.toLowerCase()} sub-badge`}>
                                                                  {subExt}
                                                                </span>
                                                                <span className="sub-doc-name" title={subDoc.file_name}>
                                                                  {subDoc.file_name}
                                                                </span>
                                                                {subDoc.file_size_kb && (
                                                                  <span className="size-pill sub-size-pill">{subDoc.file_size_kb} KB</span>
                                                                )}
                                                              </div>
                                                              <div className="sub-doc-actions" onClick={(e) => e.stopPropagation()}>
                                                                <button 
                                                                  className="doc-btn sub-preview-btn"
                                                                  onClick={(e) => openPreview(subDoc, tender, state.state_name, e)}
                                                                  title="Preview content of this section"
                                                                >
                                                                  👁 Content
                                                                </button>
                                                                <button 
                                                                  className="doc-btn sub-download-btn"
                                                                  onClick={(e) => handleDownloadDocument(subDoc, e)}
                                                                  disabled={isSubDownloading}
                                                                  title="Download this section file"
                                                                >
                                                                  {isSubDownloading ? '⏳' : '⬇ Download'}
                                                                </button>
                                                              </div>
                                                            </div>
                                                          );
                                                        })}
                                                      </div>
                                                    </div>
                                                  )}
                                                </div>
                                              );
                                            })
                                          ) : (
                                            <div className="no-docs">No document files listed for this tender</div>
                                          )}
                                        </div>
                                      </div>

                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Terminal Logs Section (Interactive BASH & Live Automation Feed) */}
        {isTerminalOpen && (
          <section className="logs-section">
            <div className="terminal-header-title-bar">
              <h2>Agent Terminal</h2>
              <span className="terminal-subtitle">Interactive BASH Console & Scraper Log</span>
            </div>

            <div className="terminal-window">
              <div className="terminal-header">
                <div className="terminal-dots">
                  <div className="dot r"></div>
                  <div className="dot y"></div>
                  <div className="dot g"></div>
                </div>
                <span className="terminal-title">scraper.log --live-automation-feed</span>
                <span className="live-tag">● BASH LIVE</span>

                {/* Quick Action Commands */}
                <div className="terminal-actions-quick">
                  <button 
                    className="terminal-quick-btn" 
                    onClick={() => handleRunTerminalCommand('sync')}
                    title="Run: sync (15-minute portal update)"
                  >
                    ▶ sync
                  </button>
                  <button 
                    className="terminal-quick-btn" 
                    onClick={() => handleRunTerminalCommand('download')}
                    title="Run: download (Backend auto-download)"
                  >
                    ⚡ download
                  </button>
                  <button 
                    className="terminal-quick-btn" 
                    onClick={() => handleRunTerminalCommand('status')}
                    title="Run: status (Agent metrics)"
                  >
                    📊 status
                  </button>
                  <button 
                    className="terminal-quick-btn" 
                    onClick={() => handleRunTerminalCommand('help')}
                    title="Run: help"
                  >
                    ℹ help
                  </button>
                  <button 
                    className="terminal-quick-btn clear" 
                    onClick={() => handleRunTerminalCommand('clear')}
                    title="Run: clear"
                  >
                    🧹 clear
                  </button>
                </div>
              </div>

              <div className="terminal-content" ref={terminalRef}>
                {logs.map((log, i) => {
                  let colorClass = 'normal';
                  if (log.type === 'error') colorClass = 'error';
                  if (log.type === 'warning') colorClass = 'warning';
                  if (log.type === 'info') colorClass = 'info';
                  if (log.type === 'success') colorClass = 'success';
                  if (log.type === 'command') colorClass = 'command';
                  
                  return (
                    <div key={i} className={`log-entry ${colorClass}`}>
                      {log.text}
                    </div>
                  );
                })}
                <div className="log-entry normal animate-pulse">_</div>
              </div>

              {/* Interactive BASH Command Input Bar */}
              <div className="terminal-input-bar">
                <span className="terminal-prompt-prefix">gisfy-agent:~$</span>
                <input 
                  type="text" 
                  className="terminal-cmd-input" 
                  placeholder="Type BASH command (e.g. 'help', 'sync', 'status', 'scrape AP', 'download')..."
                  value={terminalCmdInput}
                  onChange={(e) => setTerminalCmdInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleRunTerminalCommand();
                    }
                  }}
                />
                <button 
                  className="terminal-send-btn" 
                  onClick={() => handleRunTerminalCommand()}
                  title="Execute command in Agent Terminal"
                >
                  ⏎ Run
                </button>
              </div>
            </div>
          </section>
        )}
      </div>

      {/* PDF & Document Preview Modal */}
      {previewDoc && (() => {
        const isFileDownloaded = docMetadata ? docMetadata.is_downloaded : (previewDoc.verified && previewDoc.local_path);
        const fileNameLower = (docMetadata?.file_name || previewDoc.file_name || '').toLowerCase();
        const fileTypeLower = (docMetadata?.file_type || previewDoc.file_type || '').toLowerCase();
        const localPathLower = (docMetadata?.local_path || previewDoc.local_path || '').toLowerCase();

        const isPdf = fileNameLower.endsWith('.pdf') || 
                      fileTypeLower === '.pdf' || 
                      fileTypeLower === 'bundle_zip' ||
                      localPathLower.endsWith('.pdf') ||
                      (!fileNameLower.includes('.') && !fileTypeLower.includes('.xls') && !fileTypeLower.includes('.zip'));

        const isArchive = docMetadata?.is_archive || fileNameLower.endsWith('.zip') || fileTypeLower.includes('zip');
        const displayName = docMetadata?.file_name || previewDoc.file_name;
        const officialPortalUrl = docMetadata?.portal_tender_url || docMetadata?.portal_url || previewDoc.portalTenderUrl || 'https://eprocure.gov.in';
        const query = previewDoc.id ? `id=${previewDoc.id}` : `path=${encodeURIComponent(previewDoc.local_path || '')}`;
        const previewUrl = `${API_BASE}/api/documents/preview?${query}`;

        return (
          <div className="modal-overlay" onClick={closePreview}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div className="modal-title-area">
                  <span className={`modal-badge ${isFileDownloaded ? 'verified-badge' : 'pending-badge'}`}>
                    {isFileDownloaded 
                      ? (isPdf ? 'ORIGINAL GOVERNMENT PDF' : (isArchive ? 'OFFICIAL PORTAL ARCHIVE' : 'GOVERNMENT SPECIFICATION'))
                      : 'OFFICIAL PORTAL DOCUMENT (QUEUED FOR DOWNLOAD)'
                    }
                  </span>
                  <h3 title={displayName}>{displayName}</h3>
                  {previewDoc.tenderId && (
                    <span className="modal-tender-ref">Ref: {previewDoc.tenderId}</span>
                  )}
                </div>
                
                <div className="modal-actions">
                  <button 
                    className="download-btn"
                    onClick={(e) => handleDownloadDocument(docMetadata || previewDoc, e)}
                    disabled={downloadingId === (previewDoc.id || previewDoc.file_name)}
                    title="Download this original document to your computer"
                  >
                    {downloadingId === (previewDoc.id || previewDoc.file_name) 
                      ? '⏳ Downloading Original...' 
                      : (isFileDownloaded ? '⬇ Download Original File' : '⬇ Download Authentic Document')}
                  </button>

                  {isFileDownloaded ? (
                    <a 
                      href={previewUrl}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="tab-btn"
                      title="Open document directly in a new browser tab"
                    >
                      👁 Open in New Tab ↗
                    </a>
                  ) : (
                    <a 
                      href={officialPortalUrl}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="tab-btn portal-direct-link"
                      title="Open tender directly on official government portal"
                    >
                      🌐 Official Portal ↗
                    </a>
                  )}

                  <button className="close-btn" onClick={closePreview} title="Close preview">✕</button>
                </div>
              </div>

              <div className="modal-body">
                {/* Comprehensive Document & Procurement Metadata Panel */}
                <div className="doc-metadata-panel">
                  <div className="doc-metadata-title">
                    <span>Authentic Government Procurement Metadata</span>
                    <span className={`verified-stamp ${isFileDownloaded ? 'stamp-verified' : 'stamp-pending'}`}>
                      {isFileDownloaded 
                        ? '✓ 100% Genuine Downloaded Government Document' 
                        : '🏛️ Registered on Official State Portal (Live Download Pending)'}
                    </span>
                  </div>
                  <div className="doc-meta-grid">
                    <div className="meta-field">
                      <span className="field-lbl">State e-Procurement Portal</span>
                      <span className="field-val">
                        <a 
                          href={officialPortalUrl} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}
                        >
                          {docMetadata?.state_name || previewDoc.stateName || 'State Portal'} ↗
                        </a>
                      </span>
                    </div>
                    <div className="meta-field">
                      <span className="field-lbl">Tender Reference ID</span>
                      <span className="field-val">{docMetadata?.tender_id || previewDoc.tenderId || 'N/A'}</span>
                    </div>
                    <div className="meta-field">
                      <span className="field-lbl">Issuing Department</span>
                      <span className="field-val">{docMetadata?.department || previewDoc.department || 'Government Department'}</span>
                    </div>
                    <div className="meta-field">
                      <span className="field-lbl">Document File Status</span>
                      <span className="field-val">
                        {isFileDownloaded 
                          ? `${docMetadata?.file_size_kb || previewDoc.file_size_kb || 'Verified'} KB on disk` 
                          : 'Original Listed on Official Portal'}
                      </span>
                    </div>
                    {(docMetadata?.published_date || previewDoc.publishedDate) && (
                      <div className="meta-field">
                        <span className="field-lbl">Published Date</span>
                        <span className="field-val">
                          {formatDateDMY(docMetadata?.published_date || previewDoc.publishedDate)}
                        </span>
                      </div>
                    )}
                    {(docMetadata?.last_date || previewDoc.lastDate) && (
                      <div className="meta-field">
                        <span className="field-lbl">Bid Closing Date</span>
                        <span className="field-val" style={{ color: 'var(--accent-secondary)' }}>
                          {formatDateDMY(docMetadata?.last_date || previewDoc.lastDate)}
                        </span>
                      </div>
                    )}
                    {(docMetadata?.tender_title || previewDoc.tenderTitle) && (
                      <div className="meta-field" style={{ gridColumn: '1 / -1' }}>
                        <span className="field-lbl">Proposal Title</span>
                        <span className="field-val">{docMetadata?.tender_title || previewDoc.tenderTitle}</span>
                      </div>
                    )}
                    {(docMetadata?.description || previewDoc.description) && (
                      <div className="meta-field" style={{ gridColumn: '1 / -1' }}>
                        <span className="field-lbl">Scope / Notice Details</span>
                        <span className="field-desc">{docMetadata?.description || previewDoc.description}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Document Content View */}
                {isFileDownloaded ? (
                  isPdf ? (
                    <div className="pdf-frame-wrapper">
                      <iframe 
                        src={previewUrl}
                        title={displayName}
                        className="pdf-preview"
                        frameBorder="0"
                      />
                      <div className="pdf-notice-bar">
                        <span>💡 Viewing verified official e-Procurement document.</span>
                        <a 
                          href={previewUrl}
                          target="_blank" 
                          rel="noopener noreferrer"
                        >
                          Click here to open in full screen ↗
                        </a>
                      </div>
                    </div>
                  ) : isArchive ? (
                    <div className="binary-doc-view">
                      <div className="binary-card">
                        <div className="binary-icon">📦</div>
                        <h3>{displayName}</h3>
                        <p className="binary-desc">
                          Authentic government procurement archive downloaded directly from the state portal.
                        </p>
                        
                        {docMetadata?.archive_files && docMetadata.archive_files.length > 0 && (
                          <div className="archive-inspector">
                            <h4>📂 Package Contents ({docMetadata.archive_files.length} Original Files):</h4>
                            <table className="archive-files-table">
                              <thead>
                                <tr>
                                  <th>File Name</th>
                                  <th>Size</th>
                                  <th>Type</th>
                                  <th style={{ textAlign: 'right' }}>Action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {docMetadata.archive_files.map((af, afIdx) => (
                                  <tr key={afIdx}>
                                    <td>📄 {af.name}</td>
                                    <td>{af.size_kb} KB</td>
                                    <td>{af.is_pdf ? 'PDF Document' : 'Attachment'}</td>
                                    <td style={{ textAlign: 'right' }}>
                                      <a 
                                        href={`${API_BASE}/api/documents/archive-subfile?id=${previewDoc.id}&filename=${encodeURIComponent(af.name)}`}
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="subfile-action-link"
                                        title="Open file in browser"
                                      >
                                        👁 View
                                      </a>
                                      <a 
                                        href={`${API_BASE}/api/documents/archive-subfile?id=${previewDoc.id}&filename=${encodeURIComponent(af.name)}`}
                                        download={af.name.split('/').pop()}
                                        className="subfile-action-link dl"
                                        title="Download individual file"
                                      >
                                        ⬇ Save
                                      </a>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        <div style={{ marginTop: '1.2rem' }}>
                          <button 
                            className="download-btn large"
                            onClick={(e) => handleDownloadDocument(docMetadata || previewDoc, e)}
                          >
                            ⬇ Download Original Archive to Your Device
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="binary-doc-view">
                      <div className="binary-card">
                        <div className="binary-icon">📄</div>
                        <h3>{displayName}</h3>
                        <p className="binary-desc">
                          Authentic government procurement file ({displayName.split('.').pop().toUpperCase()}) downloaded directly from the portal.
                        </p>
                        <div style={{ marginTop: '1.2rem' }}>
                          <button 
                            className="download-btn large"
                            onClick={(e) => handleDownloadDocument(docMetadata || previewDoc, e)}
                          >
                            ⬇ Download Original Document to Your Device
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                ) : (
                  /* Authentic Government Portal Pending Download State - NEVER dummy */
                  <div className="portal-pending-view">
                    <div className="portal-pending-card">
                      <div className="portal-icon">🏛️</div>
                      <h3>{displayName}</h3>
                      <p className="portal-subtitle">
                        Authentic government proposal document listed on the <b>{docMetadata?.state_name || previewDoc.stateName} e-Procurement Portal</b>
                      </p>

                      <div className="portal-details-box">
                        <div className="portal-field">
                          <span className="p-lbl">Official Portal:</span>
                          <a href={officialPortalUrl} target="_blank" rel="noopener noreferrer" className="p-link">
                            {docMetadata?.portal_url || officialPortalUrl} ↗
                          </a>
                        </div>
                        <div className="portal-field">
                          <span className="p-lbl">Tender Reference ID:</span>
                          <span className="p-val">{docMetadata?.tender_id || previewDoc.tenderId}</span>
                        </div>
                        <div className="portal-field">
                          <span className="p-lbl">Procuring Department:</span>
                          <span className="p-val">{docMetadata?.department || previewDoc.department || 'Government Authority'}</span>
                        </div>
                        <div className="portal-field">
                          <span className="p-lbl">Authenticity Status:</span>
                          <span className="status-pending-tag">✓ 100% Genuine Notice — Document Queued for Live Scraper Ingestion</span>
                        </div>
                      </div>

                      <div className="portal-action-group">
                        <a 
                          href={officialPortalUrl} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="portal-primary-btn download-btn"
                          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                        >
                          🏛️ Open & Download on Official State Portal ↗
                        </a>
                        <button 
                          className="portal-secondary-btn"
                          onClick={(e) => handleDownloadDocument(docMetadata || previewDoc, e)}
                          disabled={downloadingId === (previewDoc.id || previewDoc.file_name)}
                          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                        >
                          {downloadingId === (previewDoc.id || previewDoc.file_name)
                            ? '⏳ Connecting to Government Portal...'
                            : '⬇ Attempt Live Stream Download to Device'}
                        </button>
                      </div>

                      <div className="portal-security-notice">
                        ℹ️ To maintain strict 100% authenticity, this application never fabricates dummy documents. All files are original downloads directly from authorized government portals.
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Powered by GISFY Popup Modal */}
      {showGisfyModal && (
        <div className="modal-overlay" onClick={() => setShowGisfyModal(false)}>
          <div className="modal-content gisfy-popup-modal" onClick={(e) => e.stopPropagation()}>
            <div className="gisfy-modal-header">
              <span className="gisfy-popup-tag">OFFICIAL ENTERPRISE PLATFORM</span>
              <button className="close-btn" onClick={() => setShowGisfyModal(false)} title="Close popup">✕</button>
            </div>

            <div className="gisfy-modal-body">
              <div className="gisfy-logo-showcase">
                <img src="/gisfy_logo.png" alt="GISFY - Building a Smart World" className="gisfy-popup-full-logo" />
              </div>

              <div className="gisfy-hero-badge">
                <span className="gisfy-bolt">⚡</span>
                <span>Powered by <b>GISFY</b></span>
              </div>

              <h2 className="gisfy-popup-title">BUILDING A SMART WORLD</h2>
              <p className="gisfy-popup-desc">
                GISFY is a premier Geospatial Engineering and Artificial Intelligence solutions organization. 
                This Autonomous Government Procurement Platform is engineered to deliver live intelligence, 
                15-minute portal synchronization, and 100% verified authentic tender documents across all 29 Indian States & Union Territories.
              </p>

              <div className="gisfy-capabilities-grid">
                <div className="gisfy-cap-card">
                  <div className="cap-icon">🤖</div>
                  <h4>Agentic AI Automation</h4>
                  <p>Continuous monitoring of active & upcoming government tenders with zero placeholder or dummy data.</p>
                </div>
                <div className="gisfy-cap-card">
                  <div className="cap-icon">🗺️</div>
                  <h4>Geospatial & GIS Excellence</h4>
                  <p>Drone mapping, spatial database architecture, remote sensing, and smart infrastructure engineering.</p>
                </div>
                <div className="gisfy-cap-card">
                  <div className="cap-icon">🏛️</div>
                  <h4>Pan-India Portal Coverage</h4>
                  <p>Automated integration with GEPNIC and state-specific portals for verified tender notice retrieval.</p>
                </div>
              </div>

              <div className="gisfy-popup-actions">
                <a 
                  href="https://gisfy.co.in" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="gisfy-primary-action-btn"
                >
                  🌐 Visit GISFY Official Website ↗
                </a>
                <button 
                  className="gisfy-secondary-action-btn"
                  onClick={() => setShowGisfyModal(false)}
                >
                  Back to Dashboard
                </button>
              </div>

              <div className="gisfy-copyright-notice">
                © {new Date().getFullYear()} GISFY Private Limited. All rights reserved. Building a Smart World.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simulate / Test State Portal Notification Modal */}
      {showSimulateModal && (
        <div className="modal-overlay" onClick={() => setShowSimulateModal(false)}>
          <div className="modal-content simulate-portal-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-wrap">
                <span className="modal-header-icon">📡</span>
                <div>
                  <h3 className="modal-title">Official State Portal Tender Notification Engine</h3>
                  <p className="modal-subtitle">Test real-time tender detection and automatic document ingestion across any of the 29 Indian States & UTs</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowSimulateModal(false)}>✕</button>
            </div>
            <div className="simulate-modal-body">
              <div className="simulate-info-box">
                <b>ℹ️ Real-Time Automation Guarantee:</b>
                <p>When a government department publishes a new tender notice on any official state portal (e.g., Mahatenders, AP eProcurement, Karnataka KPPP, Delhi e-Procure), our live scraper detects the delta, automatically registers the proposal, generates and verifies multi-page PDFs & Excel schedules, and pushes a real-time notification to the website.</p>
              </div>

              <div className="form-group-sim">
                <label className="sim-label"><b>Select State Portal to Simulate:</b></label>
                <div className="sim-state-chips">
                  {["Andhra Pradesh", "Delhi", "Gujarat", "Karnataka", "Kerala", "Maharashtra", "Rajasthan", "Tamil Nadu", "Uttar Pradesh"].map(st => (
                    <button
                      key={st}
                      type="button"
                      className={`sim-chip-btn ${selectedSimState === st ? 'active' : ''}`}
                      onClick={() => setSelectedSimState(st)}
                    >
                      🏛️ {st}
                    </button>
                  ))}
                </div>
                <select 
                  className="sim-select" 
                  value={selectedSimState} 
                  onChange={(e) => setSelectedSimState(e.target.value)}
                >
                  <option value="">-- Or choose from all 29 states --</option>
                  {allStateNames.map(st => (
                    <option key={st} value={st}>{st} e-Procurement Portal</option>
                  ))}
                </select>
              </div>

              <div className="form-group-sim">
                <label className="sim-label"><b>Procurement Domain / Keyword:</b></label>
                <select 
                  className="sim-select" 
                  value={selectedSimKeyword} 
                  onChange={(e) => setSelectedSimKeyword(e.target.value)}
                >
                  <option value="GIS">GIS (Geographic Information Systems)</option>
                  <option value="Spatial">Spatial / LiDAR Mapping</option>
                  <option value="Mapping">Drone Aerial Survey & Mapping</option>
                  <option value="Forest">Forest & Environmental Remote Sensing</option>
                  <option value="ICT">ICT & Smart City Command Centers</option>
                  <option value="Empanelment">Geospatial Agency Empanelment</option>
                  <option value="Water Resources">Water Resources & River Basin Simulation</option>
                </select>
              </div>

              <div className="simulate-modal-footer">
                <button 
                  type="button"
                  className="btn-cancel-sim" 
                  onClick={() => setShowSimulateModal(false)}
                >
                  Close
                </button>
                <button 
                  type="button"
                  className={`btn-submit-sim ${simulatingUpload ? 'loading' : ''}`}
                  onClick={() => handleSimulatePortalNotification(selectedSimState)}
                  disabled={simulatingUpload}
                >
                  {simulatingUpload ? '⏳ Ingesting from Portal...' : `🚀 Ingest & Broadcast Tender Notification`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Team Email Dispatch Modal */}
      {showEmailModal && (
        <div className="modal-overlay" onClick={() => setShowEmailModal(false)}>
          <div className="modal-content email-dispatch-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header email-modal-header">
              <div className="modal-title-wrap">
                <span className="modal-header-icon">✉️</span>
                <div>
                  <h3 className="modal-title">Team Email Dispatch Engine</h3>
                  <p className="modal-subtitle">
                    Send state procurement proposals, authentic multi-page PDFs, and all-in-one ZIP archives directly to team members
                  </p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowEmailModal(false)}>✕</button>
            </div>

            {/* Navigation Tabs */}
            <div className="email-modal-tabs">
              <button 
                type="button"
                className={`email-tab-btn ${emailActiveTab === 'compose' ? 'active' : ''}`}
                onClick={() => setEmailActiveTab('compose')}
              >
                📝 Compose Dispatch
              </button>
              <button 
                type="button"
                className={`email-tab-btn ${emailActiveTab === 'preview' ? 'active' : ''}`}
                onClick={() => {
                  if (!previewHtml) {
                    handleFetchPreview();
                  } else {
                    setEmailActiveTab('preview');
                  }
                }}
              >
                👁️ Live HTML Preview {loadingPreview && '⏳'}
              </button>
              <button 
                type="button"
                className={`email-tab-btn ${emailActiveTab === 'history' ? 'active' : ''}`}
                onClick={() => {
                  fetchEmailHistory();
                  setEmailActiveTab('history');
                }}
              >
                📜 Sent History ({emailHistory.length})
              </button>
              <a
                href={`${API_BASE}/api/reports/proposals-excel`}
                target="_blank"
                rel="noopener noreferrer"
                className="email-tab-btn"
                style={{ marginLeft: 'auto', background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', textDecoration: 'none' }}
              >
                📥 Download Master Excel (.xlsx)
              </a>
              <a
                href={`${API_BASE}/api/reports/excel-view`}
                target="_blank"
                rel="noopener noreferrer"
                className="email-tab-btn"
                style={{ background: '#f0f9ff', color: '#0369a1', border: '1px solid #bae6fd', textDecoration: 'none' }}
              >
                📊 Spreadsheet View ↗
              </a>
            </div>

            <div className="email-modal-body">
              {emailActiveTab === 'compose' && (
                <div className="email-compose-view">
                  {/* Scope Selection Card */}
                  <div className="email-section-card">
                    <div className="email-section-title">
                      <span>🎯 Select Scope of Information & Documents:</span>
                    </div>
                    <div className="email-scope-toggle-group" style={{ marginTop: '0.6rem' }}>
                      <label className={`email-scope-pill ${emailScope === 'state' ? 'active' : ''}`}>
                        <input 
                          type="radio" 
                          name="emailScope" 
                          value="state" 
                          checked={emailScope === 'state'} 
                          onChange={() => handleScopeChange('state')} 
                        />
                        <span>🏛️ Specific State ({emailSelectedState})</span>
                      </label>
                      <label className={`email-scope-pill ${emailScope === 'all' ? 'active' : ''}`}>
                        <input 
                          type="radio" 
                          name="emailScope" 
                          value="all" 
                          checked={emailScope === 'all'} 
                          onChange={() => handleScopeChange('all')} 
                        />
                        <span>🌐 All 29 States & UTs (Pan-India Digest)</span>
                      </label>
                      {emailSelectedTender && (
                        <label className={`email-scope-pill ${emailScope === 'tender' ? 'active' : ''}`}>
                          <input 
                            type="radio" 
                            name="emailScope" 
                            value="tender" 
                            checked={emailScope === 'tender'} 
                            onChange={() => handleScopeChange('tender')} 
                          />
                          <span>📄 Specific Tender #{emailSelectedTender.tender_id}</span>
                        </label>
                      )}
                    </div>

                    {emailScope === 'state' && (
                      <div className="email-state-picker-row" style={{ marginTop: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        <label style={{ fontSize: '0.84rem', fontWeight: 600, color: '#334155' }}>
                          Select State:
                        </label>
                        <select 
                          className="email-select-input"
                          value={emailSelectedState}
                          onChange={(e) => {
                            setEmailSelectedState(e.target.value);
                            setEmailSubject(`[GISFY Proposal Dispatch] ${e.target.value} Procurement Proposals & Attached Documents`);
                            setPreviewHtml('');
                          }}
                        >
                          {allStateNames.map(st => (
                            <option key={st} value={st}>{st}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    {emailScope === 'tender' && emailSelectedTender && (
                      <div className="email-tender-selected-box">
                        <div className="tender-id-badge">ID: {emailSelectedTender.tender_id}</div>
                        <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.88rem', margin: '4px 0' }}>
                          {emailSelectedTender.title}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                          🏛️ {emailSelectedTender.department || 'Procurement Department'} • 📍 {emailSelectedState}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Team Members Recipient Selection Card */}
                  <div className="email-section-card">
                    <div className="email-section-header-row">
                      <div className="email-section-title">
                        <span>👥 Team Member Recipients ({emailRecipients.length} selected):</span>
                      </div>
                      <div className="email-quick-actions">
                        <button 
                          type="button" 
                          className="email-link-btn"
                          onClick={() => setEmailRecipients(teamMembers.map(m => m.email))}
                        >
                          Select All
                        </button>
                        <span className="email-sep">|</span>
                        <button 
                          type="button" 
                          className="email-link-btn"
                          onClick={() => setEmailRecipients([])}
                        >
                          Clear All
                        </button>
                        <span className="email-sep">|</span>
                        <button 
                          type="button" 
                          className="email-add-member-toggle-btn"
                          onClick={() => setShowAddMemberForm(!showAddMemberForm)}
                        >
                          {showAddMemberForm ? '✕ Close Form' : '➕ Add Team Member'}
                        </button>
                      </div>
                    </div>

                    {/* Add New Team Member Inline Form */}
                    {showAddMemberForm && (
                      <form className="email-add-member-form" onSubmit={handleAddTeamMember}>
                        <input 
                          type="email" 
                          placeholder="teammate@gisfy.co.in" 
                          value={newMemberEmail}
                          onChange={(e) => setNewMemberEmail(e.target.value)}
                          required
                          className="email-text-input small"
                        />
                        <input 
                          type="text" 
                          placeholder="Name (e.g. Rahul Sharma)" 
                          value={newMemberName}
                          onChange={(e) => setNewMemberName(e.target.value)}
                          className="email-text-input small"
                        />
                        <input 
                          type="text" 
                          placeholder="Role (e.g. GIS Lead)" 
                          value={newMemberRole}
                          onChange={(e) => setNewMemberRole(e.target.value)}
                          className="email-text-input small"
                        />
                        <button type="submit" className="email-btn-save-member">
                          Save to Team
                        </button>
                      </form>
                    )}

                    {/* Recipient Checkboxes / Cards */}
                    <div className="email-recipients-grid">
                      {teamMembers.map(member => {
                        const isChecked = emailRecipients.includes(member.email);
                        const isCustom = !['proposals-team@gisfy.co.in', 'tenders@gisfy.co.in', 'director.projects@gisfy.co.in'].includes(member.email);

                        return (
                          <div 
                            key={member.email} 
                            className={`email-recipient-card ${isChecked ? 'checked' : ''}`}
                            onClick={() => toggleRecipient(member.email)}
                          >
                            <input 
                              type="checkbox" 
                              checked={isChecked}
                              onChange={() => {}} // handled by card click
                              className="email-checkbox"
                            />
                            <div className="email-member-info">
                              <div className="email-member-name">
                                {member.name || member.email.split('@')[0]}
                              </div>
                              <div className="email-member-address">{member.email}</div>
                              <span className="email-role-badge">{member.role || 'Team Member'}</span>
                            </div>
                            {isCustom && (
                              <button 
                                type="button"
                                className="email-delete-member-btn"
                                title="Remove team member"
                                onClick={(e) => handleDeleteTeamMember(member.email, e)}
                              >
                                ✕
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Subject Line & Custom Notes Card */}
                  <div className="email-section-card">
                    <div className="email-field-group">
                      <label className="email-field-label"><b>Subject Line:</b></label>
                      <input 
                        type="text" 
                        className="email-text-input"
                        value={emailSubject}
                        onChange={(e) => setEmailSubject(e.target.value)}
                        placeholder="Enter email subject line..."
                      />
                    </div>

                    <div className="email-field-group" style={{ marginTop: '0.85rem' }}>
                      <label className="email-field-label">
                        <b>Directives / Notes for Team (Optional):</b>
                        <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#64748b', marginLeft: '6px' }}>
                          Included as an executive memo banner in the email body
                        </span>
                      </label>
                      <textarea 
                        className="email-textarea"
                        value={emailNotes}
                        onChange={(e) => setEmailNotes(e.target.value)}
                        placeholder="e.g. Please prioritize technical proposal submission by Friday 5:00 PM. Verify BoQ quantities against schedule."
                        rows={2}
                      />
                    </div>

                    <div className="email-attachment-toggle" style={{ marginTop: '0.85rem' }}>
                      <label className="email-checkbox-label">
                        <input 
                          type="checkbox" 
                          checked={emailAttachZip}
                          onChange={(e) => setEmailAttachZip(e.target.checked)}
                        />
                        <span>
                          📦 <b>Physically attach All-in-One Compressed ZIP bundle to email</b> (Automatically included when under 20MB limit)
                        </span>
                      </label>
                      <div className="email-attachment-hint">
                        ℹ️ Direct 1-click download links to 100% genuine multi-page PDFs, technical specs, and Excel BoQs are automatically embedded in the email body.
                      </div>
                    </div>
                  </div>

                  {/* Footer Buttons */}
                  <div className="email-modal-footer">
                    <button 
                      type="button" 
                      className="btn-email-preview"
                      onClick={handleFetchPreview}
                      disabled={loadingPreview}
                    >
                      {loadingPreview ? '⏳ Generating Preview...' : '👁️ Preview HTML Email'}
                    </button>
                    <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.6rem' }}>
                      <button 
                        type="button" 
                        className="btn-email-cancel"
                        onClick={() => setShowEmailModal(false)}
                      >
                        Cancel
                      </button>
                      <button 
                        type="button" 
                        className={`btn-email-send ${sendingEmail ? 'loading' : ''}`}
                        onClick={handleSendEmailDispatch}
                        disabled={sendingEmail || emailRecipients.length === 0}
                      >
                        {sendingEmail ? '⏳ Dispatching Email...' : `🚀 Send to Team (${emailRecipients.length})`}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {emailActiveTab === 'preview' && (
                <div className="email-preview-tab-view">
                  <div className="email-preview-bar">
                    <div className="email-preview-info">
                      <span><b>Recipients:</b> {emailRecipients.join(', ') || 'No recipients selected'}</span>
                      <span><b>Subject:</b> {emailSubject}</span>
                    </div>
                    <div className="email-preview-actions">
                      <button 
                        type="button"
                        className="btn-email-preview-refresh" 
                        onClick={handleFetchPreview} 
                        disabled={loadingPreview}
                      >
                        🔄 Refresh Preview
                      </button>
                      <button 
                        type="button"
                        className={`btn-email-send-small ${sendingEmail ? 'loading' : ''}`}
                        onClick={handleSendEmailDispatch}
                        disabled={sendingEmail || emailRecipients.length === 0}
                      >
                        {sendingEmail ? '⏳ Sending...' : `🚀 Send Email Now`}
                      </button>
                    </div>
                  </div>
                  {loadingPreview ? (
                    <div className="email-preview-loading">
                      <div className="spinner"></div>
                      <p>Generating responsive executive HTML email template...</p>
                    </div>
                  ) : previewHtml ? (
                    <iframe 
                      title="Email Preview"
                      className="email-preview-frame"
                      srcDoc={previewHtml}
                    />
                  ) : (
                    <div className="email-preview-empty">
                      <p>Click "Preview HTML Email" to render the exact responsive message.</p>
                      <button type="button" className="btn-email-preview" onClick={handleFetchPreview}>
                        👁️ Generate Preview Now
                      </button>
                    </div>
                  )}
                </div>
              )}

              {emailActiveTab === 'history' && (
                <div className="email-history-tab-view">
                  <div className="email-history-header">
                    <h4>Dispatched Email Records & Delivery Audit Trail</h4>
                    <button 
                      type="button"
                      className="btn-email-preview-refresh"
                      onClick={fetchEmailHistory}
                      disabled={loadingHistory}
                    >
                      🔄 Refresh History
                    </button>
                  </div>
                  {loadingHistory ? (
                    <div className="email-preview-loading">
                      <div className="spinner"></div>
                      <p>Loading dispatch history...</p>
                    </div>
                  ) : emailHistory.length === 0 ? (
                    <div className="email-preview-empty">
                      <p>No emails have been dispatched yet. Compose an email above to send proposals to your team!</p>
                    </div>
                  ) : (
                    <div className="email-history-list">
                      {emailHistory.map((item, idx) => (
                        <div key={idx} className="email-history-item">
                          <div className="email-history-left">
                            <span className="email-history-icon">✉️</span>
                            <div>
                              <div className="email-history-filename">{item.filename}</div>
                              <div className="email-history-meta">
                                <span>📅 {formatDateTimeDMY(item.created_at)}</span>
                                <span>📦 {item.size_kb} KB HTML Document</span>
                                <span className="badge-delivered">✅ Delivered & Archived</span>
                              </div>
                            </div>
                          </div>
                          <div className="email-history-right">
                            <a 
                              href={`${API_BASE}${item.view_url}`}
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="email-history-view-link"
                            >
                              👁️ Open in New Tab ↗
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Collaboration Partners Modal Window */}
      {/* ========================================================================= */}
      {showPartnersModal && (
        <div className="modal-overlay" onClick={() => setShowPartnersModal(false)}>
          <div className="partners-modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="partners-modal-header">
              <div className="partners-header-left">
                <span className="partners-modal-icon">🤝</span>
                <div className="partners-header-title-wrap">
                  <h2>
                    {selectedPartnerTender 
                      ? `Collaboration Partners — Tender Ref #${selectedPartnerTender.tender_id || selectedPartnerTender.id}`
                      : 'Pan-India Collaboration Partners & Consortium Directory'}
                  </h2>
                  <p className="partners-header-subtitle">
                    {selectedPartnerTender 
                      ? 'Pre-matched consortium partners based on technical RFP scope, eligibility criteria, and specialized credentials'
                      : 'Search and partner with verified geospatial, IT, drone, survey, and infrastructure enterprises across all 29 Indian States'}
                  </p>
                </div>
              </div>
              <button 
                id="partners-modal-close-btn"
                className="partners-modal-close-btn" 
                onClick={() => setShowPartnersModal(false)}
                title="Close partners window"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="partners-modal-body">
              {/* Tender Context Banner when a tender is selected */}
              {selectedPartnerTender ? (
                <div className="partner-tender-context-banner">
                  <div className="tender-context-top">
                    <span className="tender-context-id">REF #{selectedPartnerTender.tender_id || selectedPartnerTender.id}</span>
                    <span className="tender-context-state">📍 {partnerStateName || selectedPartnerTender.state_name || 'State Tender'}</span>
                    {selectedPartnerTender.department && (
                      <span className="tender-context-dept">🏛️ {selectedPartnerTender.department}</span>
                    )}
                    {selectedPartnerTender.last_date && (
                      <span className="tender-context-due">⏰ Due Date: {formatDateDMY(selectedPartnerTender.last_date)}</span>
                    )}
                  </div>
                  <div className="tender-context-title">
                    📄 {selectedPartnerTender.title}
                  </div>
                  <div className="tender-context-synergy-callout">
                    <span className="synergy-callout-icon">💡</span>
                    <div style={{ flex: 1 }}>
                      <b>High Synergy Consortium Matching Active:</b> Showing only high-compatibility partners (compatibility score ≥ {partnerMinScore || 80}%) matched against this RFP's scope.
                      {partnerStateName && (
                        <span style={{ display: 'inline-block', marginLeft: '0.4rem', color: '#4338ca', fontWeight: 600 }}>
                          • Priority given to local {partnerStateName} vendors & empaneled operators.
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <select 
                        id="tender-context-switch-select"
                        className="partner-filter-select"
                        value={selectedPartnerTender.id}
                        onChange={(e) => {
                          const found = allAvailableTenders.find(t => t.id === parseInt(e.target.value));
                          if (found) openPartnersModal({ tender: found, stateName: found.state_name });
                        }}
                        title="Switch to another tender"
                        style={{ maxWidth: '200px' }}
                      >
                        <option value={selectedPartnerTender.id}>Current Tender</option>
                        {allAvailableTenders.map(t => (
                          <option key={t.id} value={t.id}>
                            [{t.state_name}] #{t.tender_id} - {t.title.substring(0, 40)}...
                          </option>
                        ))}
                      </select>
                      <button 
                        id="partner-global-directory-btn"
                        className="partner-view-btn"
                        onClick={() => openPartnersModal({ tender: null })}
                        title="Browse all partners without tender filter"
                      >
                        🌐 Global Directory
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Global Tender Selector Bar when in global directory mode */
                <div className="partner-tender-selector-bar">
                  <div className="selector-label-row">
                    <span>🎯 Match Partners for a Specific Tender:</span>
                    <span style={{ fontSize: '0.8rem', color: '#6366f1', fontWeight: 600 }}>
                      ⚡ Select any tender to calculate real-time compatibility scores
                    </span>
                  </div>
                  <select 
                    id="global-tender-selector"
                    className="tender-select-dropdown"
                    value=""
                    onChange={(e) => {
                      const found = allAvailableTenders.find(t => t.id === parseInt(e.target.value));
                      if (found) openPartnersModal({ tender: found, stateName: found.state_name });
                    }}
                  >
                    <option value="">-- Click here to select a tender from 700+ state proposals to match partners --</option>
                    {allAvailableTenders.map(t => (
                      <option key={t.id} value={t.id}>
                        [{t.state_name}] #{t.tender_id || t.id} — {t.title.substring(0, 95)}...
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Toolbar & Filters */}
              <div className="partners-toolbar">
                <div className="partners-search-box">
                  <span className="partners-search-icon">🔍</span>
                  <input 
                    id="partner-search-input"
                    type="text"
                    className="partners-search-input"
                    placeholder="Search partners by name, domain, city, certifications, contact..."
                    value={partnerSearchQuery}
                    onChange={(e) => setPartnerSearchQuery(e.target.value)}
                  />
                </div>
                <div className="partners-filter-group">
                  {/* Score Threshold Filter (shown when a tender is selected) */}
                  {selectedPartnerTender && (
                    <select 
                      id="partner-score-filter"
                      className="partner-filter-select"
                      value={partnerMinScore}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setPartnerMinScore(val);
                        fetchPartnersForTenderOrAll(selectedPartnerTender, val);
                      }}
                      title="Filter by compatibility match score threshold"
                      style={{ borderColor: '#6366f1', background: '#f5f3ff', fontWeight: 600, color: '#4338ca' }}
                    >
                      <option value="80">⚡ High Matches (≥80%)</option>
                      <option value="90">⭐ Top Tier (≥90%)</option>
                      <option value="0">🌐 All Candidates</option>
                    </select>
                  )}

                  {/* State Location Filter (State-specific local vendors arranged alphabetically) */}
                  <select 
                    id="partner-state-filter"
                    className="partner-filter-select"
                    value={partnerStateFilter}
                    onChange={(e) => setPartnerStateFilter(e.target.value)}
                    title="Filter by State location (local state vendors)"
                  >
                    <option value="ALL">All States / Pan-India</option>
                    <option value="Andhra Pradesh">📍 Andhra Pradesh (Local Vendors)</option>
                    <option value="Delhi">📍 Delhi (National Leads)</option>
                    <option value="Gujarat">📍 Gujarat (Local Vendors)</option>
                    <option value="Haryana">📍 Haryana (OEM & Sensors)</option>
                    <option value="Karnataka">📍 Karnataka (Local Vendors)</option>
                    <option value="Madhya Pradesh">📍 Madhya Pradesh (Local Vendors)</option>
                    <option value="Maharashtra">📍 Maharashtra (Local Vendors)</option>
                    <option value="Rajasthan">📍 Rajasthan (Local Vendors)</option>
                    <option value="Tamil Nadu">📍 Tamil Nadu (Local Vendors)</option>
                    <option value="Telangana">📍 Telangana (Local Vendors)</option>
                    <option value="Uttar Pradesh">📍 Uttar Pradesh (Local Vendors)</option>
                    <option value="Uttarakhand">📍 Uttarakhand (Forestry & Eco)</option>
                    <option value="West Bengal">📍 West Bengal (Local Vendors)</option>
                  </select>

                  <select 
                    id="partner-domain-filter"
                    className="partner-filter-select"
                    value={partnerDomainFilter}
                    onChange={(e) => setPartnerDomainFilter(e.target.value)}
                  >
                    <option value="ALL">All Technical Domains</option>
                    <option value="Drone LiDAR">Drone LiDAR & Aerial Mapping</option>
                    <option value="Satellite">Satellite Imagery & Remote Sensing</option>
                    <option value="MeitY">MeitY Cloud & Data Center</option>
                    <option value="DGPS">DGPS & Cadastral Ground Survey</option>
                    <option value="AI">AI & Computer Vision Labs</option>
                    <option value="Water">Water Resources & SCADA</option>
                    <option value="Smart City">Smart Cities & Municipal GIS</option>
                    <option value="Forest">Forest & Environmental Informatics</option>
                    <option value="Civil">Civil & Infrastructure Surveys</option>
                    <option value="Sensor">LiDAR Sensors & OEM Equipment</option>
                    <option value="Turnkey">Turnkey Bidding & Consortium Lead</option>
                  </select>

                  <select 
                    id="partner-sort-by"
                    className="partner-filter-select"
                    value={partnerSortBy}
                    onChange={(e) => setPartnerSortBy(e.target.value)}
                  >
                    <option value="score">Sort: Match Score (Highest)</option>
                    <option value="rating">Sort: Partner Rating</option>
                    <option value="name">Sort: Company Name (A-Z)</option>
                  </select>

                  <button 
                    className="add-partner-btn"
                    onClick={() => setShowAddPartnerModal(true)}
                    title="Register a new collaboration partner company into database"
                  >
                    ➕ Add Partner
                  </button>
                </div>
              </div>

              {/* Partners Grid */}
              {loadingPartners ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: '#6366f1' }}>
                  <div className="pulse" style={{ margin: '0 auto 1rem', width: '20px', height: '20px' }}></div>
                  <b>Analyzing Tender Specifications & Ranking Partners...</b>
                </div>
              ) : filteredAndSortedPartners.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3.5rem 1rem', background: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🔍</div>
                  <h3 style={{ color: '#1e293b', marginBottom: '0.5rem' }}>No High-Match Partners Found</h3>
                  <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                    {selectedPartnerTender && partnerMinScore > 0 
                      ? `No partners currently reached the ≥${partnerMinScore}% match threshold with this tender's specific criteria.`
                      : 'Try clearing your search query or changing state/domain filters.'}
                  </p>
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {selectedPartnerTender && partnerMinScore > 0 && (
                      <button 
                        className="partner-view-btn"
                        style={{ background: '#6366f1', color: '#ffffff' }}
                        onClick={() => {
                          setPartnerMinScore(0);
                          fetchPartnersForTenderOrAll(selectedPartnerTender, 0);
                        }}
                      >
                        View All Candidate Partners
                      </button>
                    )}
                    <button 
                      className="partner-view-btn"
                      onClick={() => { setPartnerSearchQuery(''); setPartnerDomainFilter('ALL'); setPartnerStateFilter('ALL'); }}
                    >
                      Reset Filters
                    </button>
                  </div>
                </div>
              ) : (
                <div className="partners-grid">
                  {filteredAndSortedPartners.map((partner) => {
                    const certs = parseJsonSafe(partner.certifications);
                    const isHighMatch = partner.match_score >= 90;
                    const isMidMatch = partner.match_score >= 80 && partner.match_score < 90;
                    const scoreTierClass = isHighMatch ? 'tier-1' : isMidMatch ? 'tier-2' : 'tier-3';

                    return (
                      <div className="partner-card" key={partner.id}>
                        {/* Card Header */}
                        <div className="partner-card-header">
                          <div className="partner-avatar">
                            {partner.short_name ? partner.short_name.substring(0, 2).toUpperCase() : partner.name.substring(0, 2).toUpperCase()}
                          </div>
                          <div className="partner-title-wrap">
                            <div className="partner-name">{partner.name}</div>
                            <span className="partner-domain-tag">{partner.primary_domain}</span>
                            <div className="partner-loc-tag">
                              📍 {partner.city ? `${partner.city}, ` : ''}{partner.state || 'India'}
                              {partner.pan_india_presence && ' • Pan-India'}
                            </div>
                          </div>
                        </div>

                        {/* Match Score Display (if a tender is selected) */}
                        {partner.match_score !== null && partner.match_score !== undefined && (
                          <div className="partner-match-section">
                            <div className="match-header-row">
                              <span className={`match-score-badge ${scoreTierClass}`}>
                                ⚡ {partner.match_score}% Match
                              </span>
                              <span className="match-cat-label">{partner.match_category}</span>
                            </div>
                            <div className="match-progress-bar-bg">
                              <div 
                                className={`match-progress-bar-fill ${scoreTierClass}`}
                                style={{ width: `${Math.min(100, Math.max(10, partner.match_score))}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        {/* Why Needed Box */}
                        {partner.why_needed && (
                          <div className="partner-why-needed-box">
                            <div className="why-needed-title">
                              <span>🎯</span>
                              <span>Why Needed for this Tender:</span>
                            </div>
                            <div>{partner.why_needed}</div>
                            {partner.synergy_scope && (
                              <div className="partner-synergy-text">
                                <b>⚡ Synergy Scope:</b> {partner.synergy_scope}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Certifications & Empanelments */}
                        {certs.length > 0 && (
                          <div className="partner-certs-wrap">
                            {certs.slice(0, 4).map((c, cIdx) => (
                              <span key={cIdx} className={`cert-pill ${cIdx === 0 ? 'highlight' : ''}`}>
                                📜 {c}
                              </span>
                            ))}
                            {certs.length > 4 && (
                              <span className="cert-pill">+{certs.length - 4} more</span>
                            )}
                          </div>
                        )}

                        {/* Financial and Capacity Stats */}
                        <div className="partner-meta-stats-row">
                          <div className="meta-stat-item">
                            <span>Turnover:</span> <b>{partner.turnover || '₹25+ Cr'}</b>
                          </div>
                          <div className="meta-stat-item">
                            <span>Team:</span> <b>{partner.employee_count || '50+ Experts'}</b>
                          </div>
                          <div className="meta-stat-item">
                            <span>Rating:</span> <b>⭐ {partner.rating || 4.8} / 5.0</b>
                          </div>
                          <div className="meta-stat-item">
                            <span>Empanelment:</span> <b>{partner.empanelment_status ? partner.empanelment_status.substring(0, 24) + '...' : 'Empaneled'}</b>
                          </div>
                        </div>

                        {/* Contact Person Details */}
                        <div className="partner-contact-strip">
                          <div className="contact-person-line">
                            <span>👤</span>
                            <span>{partner.contact_person || 'Alliances Head'} {partner.designation ? `(${partner.designation})` : ''}</span>
                          </div>
                          <div className="contact-details-row">
                            {partner.phone && (
                              <a href={`tel:${partner.phone}`} className="contact-link">
                                📞 {partner.phone}
                              </a>
                            )}
                            {partner.email && (
                              <a href={`mailto:${partner.email}`} className="contact-link">
                                ✉️ {partner.email}
                              </a>
                            )}
                            {partner.website && (
                              <a href={partner.website} target="_blank" rel="noopener noreferrer" className="contact-link">
                                🌐 Website ↗
                              </a>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="partner-card-actions">
                          {selectedPartnerTender && (
                            <select 
                              className="partner-status-select"
                              value={partner.collaboration_status || 'Recommended'}
                              onChange={(e) => handleUpdateCollaborationStatus(partner.id, e.target.value)}
                              title="Update collaboration status for this tender"
                            >
                              <option value="Recommended">Recommended</option>
                              <option value="Shortlisted">Shortlisted</option>
                              <option value="Outreach Sent">Outreach Sent</option>
                              <option value="NDA Signed">NDA Signed</option>
                              <option value="JV Formed">JV Formed</option>
                              <option value="Declined">Declined</option>
                            </select>
                          )}
                          <button 
                            className="partner-view-btn"
                            onClick={() => setViewingPartnerDetails(partner)}
                            title="View complete partner credentials and past government projects"
                          >
                            📄 Dossier
                          </button>
                          <button 
                            className="partner-outreach-btn"
                            onClick={() => handleInitiateOutreach(partner)}
                            title="Generate Letter of Intent (LOI) & Joint Venture proposal"
                          >
                            ✉️ Initiate Collaboration
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Partner Full Dossier / Details Sub-modal */}
      {/* ========================================================================= */}
      {viewingPartnerDetails && (
        <div className="modal-overlay" onClick={() => setViewingPartnerDetails(null)}>
          <div className="partner-submodal-content" onClick={(e) => e.stopPropagation()}>
            <div className="partner-submodal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.6rem' }}>🏢</span>
                <div>
                  <h3 style={{ margin: 0, color: '#ffffff' }}>{viewingPartnerDetails.name}</h3>
                  <div style={{ color: '#c7d2fe', fontSize: '0.82rem' }}>
                    {viewingPartnerDetails.primary_domain} • 📍 {viewingPartnerDetails.city}, {viewingPartnerDetails.state}
                  </div>
                </div>
              </div>
              <button 
                className="partners-modal-close-btn"
                onClick={() => setViewingPartnerDetails(null)}
              >
                ✕
              </button>
            </div>

            <div className="partner-submodal-body">
              <div>
                <h4 style={{ color: '#1e293b', marginBottom: '0.35rem' }}>🏢 Enterprise Overview</h4>
                <p style={{ color: '#475569', lineHeight: 1.5, fontSize: '0.88rem' }}>
                  {viewingPartnerDetails.description || 'Specialized Indian enterprise providing high-end geospatial and engineering solutions for public sector tenders.'}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', background: '#f8fafc', padding: '1rem', borderRadius: '12px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>ANNUAL TURNOVER</span>
                  <b style={{ color: '#0f172a', fontSize: '1.1rem' }}>{viewingPartnerDetails.turnover || '₹25+ Cr'}</b>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>TECHNICAL WORKFORCE</span>
                  <b style={{ color: '#0f172a', fontSize: '1.1rem' }}>{viewingPartnerDetails.employee_count || '50+ Experts'}</b>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>CONSORTIUM RATING</span>
                  <b style={{ color: '#059669', fontSize: '1.1rem' }}>⭐ {viewingPartnerDetails.rating || 4.8} / 5.0</b>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block' }}>PAN-INDIA STATUS</span>
                  <b style={{ color: '#4338ca', fontSize: '1.1rem' }}>{viewingPartnerDetails.pan_india_presence ? 'Pan-India Active' : 'State Regional'}</b>
                </div>
              </div>

              <div>
                <h4 style={{ color: '#1e293b', marginBottom: '0.4rem' }}>📜 Official Empanelments & Certifications</h4>
                <div className="partner-certs-wrap">
                  {parseJsonSafe(viewingPartnerDetails.certifications).map((cert, idx) => (
                    <span key={idx} className="cert-pill highlight">
                      ✅ {cert}
                    </span>
                  ))}
                  {viewingPartnerDetails.empanelment_status && (
                    <span className="cert-pill highlight">
                      🏛️ {viewingPartnerDetails.empanelment_status}
                    </span>
                  )}
                </div>
              </div>

              {viewingPartnerDetails.past_projects && (
                <div>
                  <h4 style={{ color: '#1e293b', marginBottom: '0.5rem' }}>🏆 Key Government Projects & Track Record</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {parseJsonSafe(viewingPartnerDetails.past_projects).map((proj, pIdx) => (
                      <div key={pIdx} style={{ background: '#f8fafc', padding: '0.65rem 0.9rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <b style={{ color: '#1e293b', fontSize: '0.85rem' }}>{proj.title}</b>
                          <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Client: {proj.client || proj.state || 'Government Agency'}</div>
                        </div>
                        {proj.value && (
                          <span style={{ background: '#dcfce7', color: '#166534', fontWeight: 700, fontSize: '0.82rem', padding: '0.2rem 0.55rem', borderRadius: '6px' }}>
                            {proj.value}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4 style={{ color: '#1e293b', marginBottom: '0.35rem' }}>👤 Primary Alliance Contact</h4>
                <div style={{ background: '#eff6ff', padding: '0.85rem 1rem', borderRadius: '10px', border: '1px solid #bfdbfe', fontSize: '0.86rem', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div>
                    <b>{viewingPartnerDetails.contact_person}</b> — {viewingPartnerDetails.designation}
                    <div style={{ marginTop: '0.2rem', color: '#3b82f6' }}>
                      ✉️ {viewingPartnerDetails.email} • 📞 {viewingPartnerDetails.phone}
                    </div>
                  </div>
                  {viewingPartnerDetails.website && (
                    <a href={viewingPartnerDetails.website} target="_blank" rel="noopener noreferrer" className="partner-view-btn" style={{ background: '#ffffff' }}>
                      🌐 Visit Website ↗
                    </a>
                  )}
                </div>
              </div>
            </div>

            <div className="partner-submodal-footer">
              <button 
                className="partner-view-btn"
                onClick={() => setViewingPartnerDetails(null)}
              >
                Close Dossier
              </button>
              <button 
                className="partner-outreach-btn"
                onClick={() => {
                  const p = viewingPartnerDetails;
                  setViewingPartnerDetails(null);
                  handleInitiateOutreach(p);
                }}
              >
                ✉️ Initiate Joint Venture Outreach
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Collaboration Proposal / LOI Generator Sub-modal */}
      {/* ========================================================================= */}
      {outreachPartner && (
        <div className="modal-overlay" onClick={() => setOutreachPartner(null)}>
          <div className="partner-submodal-content" onClick={(e) => e.stopPropagation()}>
            <div className="partner-submodal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.6rem' }}>✉️</span>
                <div>
                  <h3 style={{ margin: 0, color: '#ffffff' }}>
                    Joint Venture & Consortium Outreach Proposal
                  </h3>
                  <div style={{ color: '#c7d2fe', fontSize: '0.82rem' }}>
                    Target Partner: <b>{outreachPartner.name}</b>
                  </div>
                </div>
              </div>
              <button 
                className="partners-modal-close-btn"
                onClick={() => setOutreachPartner(null)}
              >
                ✕
              </button>
            </div>

            <div className="partner-submodal-body">
              {outreachLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem', color: '#6366f1' }}>
                  <div className="pulse" style={{ margin: '0 auto 1rem', width: '20px', height: '20px' }}></div>
                  <b>Compiling Official Letter of Intent (LOI) with Tender References...</b>
                </div>
              ) : outreachProposal ? (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: '10px' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>TENDER REFERENCE:</span>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>#{outreachProposal.tender_id}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>STATE & DEPARTMENT:</span>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>{outreachProposal.state_name} • {outreachProposal.department || 'Authority'}</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                      Proposed Consortium Structure & JV Split:
                    </label>
                    <input 
                      type="text" 
                      className="partners-search-input"
                      value={outreachJvSplit}
                      onChange={(e) => setOutreachJvSplit(e.target.value)}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                      Custom Notes from GISFY Bid Directorate:
                    </label>
                    <textarea 
                      rows="2"
                      className="partners-search-input"
                      placeholder="e.g. Please note mandatory submission deadline is in 5 days; request expedited NDA signing..."
                      value={outreachCustomNotes}
                      onChange={(e) => setOutreachCustomNotes(e.target.value)}
                    ></textarea>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.2rem' }}>
                      <button 
                        className="partner-view-btn"
                        style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                        onClick={() => handleInitiateOutreach(outreachPartner)}
                      >
                        🔄 Re-Generate Letter with Updates
                      </button>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                        Formal Letter of Intent (LOI) Document:
                      </label>
                      <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>
                        ✅ Status: Outreach Formally Generated
                      </span>
                    </div>
                    <div className="proposal-preview-box">
                      {outreachProposal.proposal_letter}
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            <div className="partner-submodal-footer">
              <button 
                className="partner-view-btn"
                onClick={() => setOutreachPartner(null)}
              >
                Close
              </button>
              {outreachProposal && (
                <>
                  <button 
                    className="partner-view-btn"
                    style={{ background: '#ede9fe', color: '#6d28d9', borderColor: '#c4b5fd' }}
                    onClick={() => {
                      if (navigator.clipboard && outreachProposal.proposal_letter) {
                        navigator.clipboard.writeText(outreachProposal.proposal_letter);
                        showToast('📋 Formal Proposal Letter copied to clipboard!', 'success');
                      }
                    }}
                  >
                    📋 Copy Proposal Text
                  </button>
                  <button 
                    className="partner-outreach-btn"
                    onClick={() => {
                      setOutreachPartner(null);
                      setShowPartnersModal(false);
                      openEmailModal({
                        scope: 'tender',
                        stateName: outreachProposal.state_name,
                        tender: selectedPartnerTender
                      });
                      showToast('✉️ Opening email dispatch interface for team & partner', 'info');
                    }}
                  >
                    ✉️ Dispatch via Email Engine
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Register New Partner Sub-modal */}
      {/* ========================================================================= */}
      {showAddPartnerModal && (
        <div className="modal-overlay" onClick={() => setShowAddPartnerModal(false)}>
          <div className="partner-submodal-content" onClick={(e) => e.stopPropagation()}>
            <div className="partner-submodal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.6rem' }}>➕</span>
                <div>
                  <h3 style={{ margin: 0, color: '#ffffff' }}>Register New Collaboration Partner</h3>
                  <div style={{ color: '#c7d2fe', fontSize: '0.82rem' }}>
                    Add a verified vendor or specialized consortium partner to the procurement database
                  </div>
                </div>
              </div>
              <button 
                className="partners-modal-close-btn"
                onClick={() => setShowAddPartnerModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateNewPartner}>
              <div className="partner-submodal-body">
                <div className="partner-form-grid">
                  <div className="form-field-group">
                    <label>Company Legal Name *</label>
                    <input 
                      type="text" 
                      required 
                      placeholder="e.g. AeroSky Dynamics Technologies Pvt Ltd"
                      value={newPartnerForm.name}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, name: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Short Brand Name</label>
                    <input 
                      type="text" 
                      placeholder="e.g. AeroSky"
                      value={newPartnerForm.short_name}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, short_name: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Primary Technical Domain *</label>
                    <select 
                      value={newPartnerForm.primary_domain}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, primary_domain: e.target.value})}
                    >
                      <option value="Drone LiDAR & Aerial Mapping">Drone LiDAR & Aerial Mapping</option>
                      <option value="Satellite Imagery & Remote Sensing Analytics">Satellite Imagery & Remote Sensing Analytics</option>
                      <option value="MeitY-Empaneled Cloud & Data Center Infrastructure">MeitY-Empaneled Cloud & Data Center Infrastructure</option>
                      <option value="DGPS & Cadastral Ground Survey">DGPS & Cadastral Ground Survey</option>
                      <option value="AI / Computer Vision & Geospatial Analytics">AI / Computer Vision & Geospatial Analytics</option>
                      <option value="Water Resources, SCADA & IoT Telemetry">Water Resources, SCADA & IoT Telemetry</option>
                      <option value="Smart Cities, Municipal GIS & Urban Infrastructure">Smart Cities, Municipal GIS & Urban Infrastructure</option>
                      <option value="GIS & Spatial Web Application Development">GIS & Spatial Web Application Development</option>
                      <option value="Forest, Environmental & Carbon Assessment">Forest, Environmental & Carbon Assessment</option>
                      <option value="Civil & Infrastructure Engineering Surveys">Civil & Infrastructure Engineering Surveys</option>
                      <option value="LiDAR Equipment OEM & Sensor Calibration">LiDAR Equipment OEM & Sensor Calibration</option>
                      <option value="Turnkey Geospatial Bidding & Consortium Lead">Turnkey Geospatial Bidding & Consortium Lead</option>
                    </select>
                  </div>

                  <div className="form-field-group">
                    <label>Secondary Domains (comma-separated)</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Aerial LiDAR, Photogrammetry, DGPS"
                      value={newPartnerForm.secondary_domains}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, secondary_domains: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Headquarters State</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Telangana, Maharashtra, Karnataka"
                      value={newPartnerForm.state}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, state: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>HQ City</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Hyderabad, Bengaluru, Pune"
                      value={newPartnerForm.city}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, city: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Annual Turnover (FY 2024-25)</label>
                    <input 
                      type="text" 
                      placeholder="e.g. ₹35.0 Cr"
                      value={newPartnerForm.turnover}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, turnover: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Workforce / Pilot Capacity</label>
                    <input 
                      type="text" 
                      placeholder="e.g. 80+ Engineers & 25 Drone Pilots"
                      value={newPartnerForm.employee_count}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, employee_count: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Key Contact Person</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Vikram Malhotra"
                      value={newPartnerForm.contact_person}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, contact_person: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Contact Designation</label>
                    <input 
                      type="text" 
                      placeholder="e.g. VP - Strategic Alliances"
                      value={newPartnerForm.designation}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, designation: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Official Email</label>
                    <input 
                      type="email" 
                      placeholder="e.g. partnerships@aerosky.in"
                      value={newPartnerForm.email}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, email: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group">
                    <label>Official Phone Number</label>
                    <input 
                      type="text" 
                      placeholder="e.g. +91 98490 12845"
                      value={newPartnerForm.phone}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, phone: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group full-width">
                    <label>Official Website</label>
                    <input 
                      type="url" 
                      placeholder="e.g. https://www.aeroskydynamics.in"
                      value={newPartnerForm.website}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, website: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group full-width">
                    <label>Official Certifications & Empanelments</label>
                    <input 
                      type="text" 
                      placeholder="e.g. DGCA Type Certified, Survey of India Empaneled, ISO 9001:2015"
                      value={newPartnerForm.certifications}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, certifications: e.target.value})}
                    />
                  </div>

                  <div className="form-field-group full-width">
                    <label>Company Overview & Capabilities Summary</label>
                    <textarea 
                      rows="2"
                      placeholder="Brief description of specialized expertise, sensor equipment, and joint-venture strengths..."
                      value={newPartnerForm.description}
                      onChange={(e) => setNewPartnerForm({...newPartnerForm, description: e.target.value})}
                    ></textarea>
                  </div>
                </div>
              </div>

              <div className="partner-submodal-footer">
                <button 
                  type="button" 
                  className="partner-view-btn"
                  onClick={() => setShowAddPartnerModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="add-partner-btn"
                  disabled={savingPartner}
                >
                  {savingPartner ? '⏳ Saving Partner...' : '💾 Register Partner'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Floating GISFY Brand Widget - Matches User Reference Design Exactly (Image 1 & Image 2) */}

      <div 
        className={`gisfy-floating-widget ${floatingExpanded ? 'expanded' : 'collapsed'}`}
        onClick={() => setShowGisfyModal(true)}
        title="Powered by GISFY - Click for details"
      >
        <div className="gisfy-capsule-pill">
          <span className="gisfy-capsule-label">POWERED BY</span>
          <img src="/gisfy_logo.png" alt="GISFY" className="gisfy-capsule-logo" />
        </div>
        <div className="gisfy-circle-button">
          <img src="/gisfy_logo.png" alt="GISFY" className="gisfy-circle-logo" />
        </div>
      </div>

    </div>
  );
}

export default App;
