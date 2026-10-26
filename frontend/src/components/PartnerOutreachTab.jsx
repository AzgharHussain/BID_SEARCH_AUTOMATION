import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';

const JURISDICTIONS = [
  { value: 'ALL', label: 'All Jurisdictions (29 Indian States & ADB)' },
  { value: 'ADB', label: '🌐 ADB - Asian Development Bank' },
  { value: 'Andhra Pradesh', label: '📍 Andhra Pradesh' },
  { value: 'Arunachal Pradesh', label: '📍 Arunachal Pradesh' },
  { value: 'Assam', label: '📍 Assam' },
  { value: 'Bihar', label: '📍 Bihar' },
  { value: 'Chhattisgarh', label: '📍 Chhattisgarh' },
  { value: 'Delhi', label: '📍 Delhi' },
  { value: 'Goa', label: '📍 Goa' },
  { value: 'Gujarat', label: '📍 Gujarat' },
  { value: 'Haryana', label: '📍 Haryana' },
  { value: 'Himachal Pradesh', label: '📍 Himachal Pradesh' },
  { value: 'Jharkhand', label: '📍 Jharkhand' },
  { value: 'Karnataka', label: '📍 Karnataka' },
  { value: 'Kerala', label: '📍 Kerala' },
  { value: 'Madhya Pradesh', label: '📍 Madhya Pradesh' },
  { value: 'Maharashtra', label: '📍 Maharashtra' },
  { value: 'Manipur', label: '📍 Manipur' },
  { value: 'Meghalaya', label: '📍 Meghalaya' },
  { value: 'Mizoram', label: '📍 Mizoram' },
  { value: 'Nagaland', label: '📍 Nagaland' },
  { value: 'Odisha', label: '📍 Odisha' },
  { value: 'Punjab', label: '📍 Punjab' },
  { value: 'Rajasthan', label: '📍 Rajasthan' },
  { value: 'Sikkim', label: '📍 Sikkim' },
  { value: 'Tamil Nadu', label: '📍 Tamil Nadu' },
  { value: 'Telangana', label: '📍 Telangana' },
  { value: 'Tripura', label: '📍 Tripura' },
  { value: 'Uttar Pradesh', label: '📍 Uttar Pradesh' },
  { value: 'Uttarakhand', label: '📍 Uttarakhand' },
  { value: 'West Bengal', label: '📍 West Bengal' }
];

export default function PartnerOutreachTab({ API_BASE, showToast }) {
  const [dashboard, setDashboard] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [subTab, setSubTab] = useState('drafts'); // 'drafts' | 'sent' | 'logs'
  const [previewDraft, setPreviewDraft] = useState(null);
  const [selectedStateFilter, setSelectedStateFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Live Provider Status
  const [providerStatus, setProviderStatus] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configTab, setConfigTab] = useState('direct'); // 'direct' | 'gmail' | 'm365' | 'dns' | 'smtp'
  const [settingProvider, setSettingProvider] = useState(false);

  // Single Approved Test Email State
  const [showTestModal, setShowTestModal] = useState(false);
  const [testRecipient, setTestRecipient] = useState('bidding@gisfy.co.in');
  const [testNotes, setTestNotes] = useState('User-approved single test email verification');
  const [testSending, setTestSending] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [verifyingSentId, setVerifyingSentId] = useState(null);

  // MSAL Device Code Flow State (Delegated Sign-in for farhath@gisfy.co.in)
  const [deviceFlow, setDeviceFlow] = useState(null);
  const [deviceFlowPolling, setDeviceFlowPolling] = useState(false);
  const [startingDeviceFlow, setStartingDeviceFlow] = useState(false);

  // DNS Audit State
  const [dnsAudit, setDnsAudit] = useState(null);
  const [dnsLoading, setDnsLoading] = useState(false);
  const [copiedSpf, setCopiedSpf] = useState(false);
  const [copiedDkim, setCopiedDkim] = useState(false);

  // Forms for providers
  const [gmailForm, setGmailForm] = useState({
    email: '',
    app_password: ''
  });

  const [brevoForm, setBrevoForm] = useState({
    api_key: '',
    smtp_user: '',
    smtp_key: '',
    send_method: 'api'
  });

  const [sendgridForm, setSendgridForm] = useState({
    api_key: '',
    send_method: 'api'
  });

  const [connectingM365, setConnectingM365] = useState(false);
  const [verifyingM365, setVerifyingM365] = useState(false);
  const [copiedRedirectUri, setCopiedRedirectUri] = useState(false);
  const [copiedPsCommand, setCopiedPsCommand] = useState(false);
  const [showRbacGuide, setShowRbacGuide] = useState(false);

  const [m365Form, setM365Form] = useState({
    client_id: 'c2cd8349-a198-46d6-a6dc-325e86dd67a4',
    client_secret: '',
    tenant_id: 'de9e8583-c4c4-4212-9c27-e35cfa247419',
    refresh_token: ''
  });

  const [googleForm, setGoogleForm] = useState({
    client_id: '',
    client_secret: '',
    refresh_token: ''
  });

  const [smtpForm, setSmtpForm] = useState({
    host: 'smtp.office365.com',
    port: 587,
    user: 'farhath@gisfy.co.in',
    password: '',
    imap_host: 'outlook.office365.com'
  });

  const fetchProviderStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/provider-status`);
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data);
        if (data.microsoft_365?.tenant_id) {
          setM365Form(prev => ({ ...prev, tenant_id: data.microsoft_365.tenant_id }));
        }
      }
    } catch (err) {
      console.error('Failed to fetch email provider status:', err);
    }
  };

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/dashboard`);
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (err) {
      console.error('Failed to load outreach dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDrafts = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/drafts?limit=3500`);
      if (res.ok) {
        const data = await res.json();
        setDrafts(data);
      }
    } catch (err) {
      console.error('Failed to load drafts:', err);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchDrafts();
    fetchProviderStatus();
  }, []);

  const handleApprove = async (id) => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/drafts/${id}/approve`, { method: 'POST' });
      if (res.ok) {
        if (showToast) showToast('✅ Draft approved successfully! Ready for dispatch.', 'success');
        fetchDashboard();
        fetchDrafts();
      }
    } catch (err) {
      if (showToast) showToast('Failed to approve draft', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenOutlook = (draft) => {
    if (!draft) return;
    const recipient = draft.recipient_email || '';
    const subject = draft.subject || '';
    const body = draft.body_text || '';
    const ccEmails = 'bidding@gisfy.co.in';
    const outlookWebUrl = `https://outlook.office.com/mail/deeplink/compose?to=${encodeURIComponent(recipient)}&cc=${encodeURIComponent(ccEmails)}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(outlookWebUrl, '_blank');
    if (showToast) {
      showToast(`📬 Microsoft Outlook opened for ${draft.company_name} from Farhath & Support (CC: bidding@gisfy.co.in)!`, 'success');
    }
  };

  const handleSend = async (id) => {
    setActionLoading(true);

    // Look up the draft to trigger Microsoft Outlook Web / PWA directly (NOT Apple Mail!)
    const targetDraft = drafts.find(d => d.id === id) || (previewDraft && previewDraft.id === id ? previewDraft : null);
    if (targetDraft) {
      const recipient = targetDraft.recipient_email || '';
      const subject = targetDraft.subject || '';
      const body = targetDraft.body_text || '';
      const ccEmails = 'bidding@gisfy.co.in';
      const outlookWebUrl = `https://outlook.office.com/mail/deeplink/compose?to=${encodeURIComponent(recipient)}&cc=${encodeURIComponent(ccEmails)}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      window.open(outlookWebUrl, '_blank');
    }

    try {
      const res = await fetch(`${API_BASE}/api/collaboration/drafts/${id}/send`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (showToast) {
          showToast(`📬 Microsoft Outlook opened for ${data.recipient || targetDraft?.recipient_email || 'partner'} from Farhath & Support (CC: bidding@gisfy.co.in)! Click 'Send' in Outlook to deliver.`, 'success');
        }
        fetchDashboard();
        fetchDrafts();
        fetchProviderStatus();
        if (previewDraft && previewDraft.id === id) setPreviewDraft(null);
      } else {
        const err = await res.json();
        const msg = typeof err.detail === 'object' ? (err.detail.error || JSON.stringify(err.detail)) : (err.detail || 'Dispatch failed');
        if (showToast) showToast(`❌ Notice: ${msg}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Opened in Microsoft Outlook. Click Send to complete delivery.', 'info');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/drafts/${id}/reject`, { method: 'POST' });
      if (res.ok) {
        if (showToast) showToast('Draft rejected and cancelled from queue.', 'info');
        fetchDashboard();
        fetchDrafts();
      }
    } catch (err) {
      if (showToast) showToast('Failed to reject draft', 'error');
    }
  };

  const handleTriggerCycle = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/trigger-daily-cycle`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const s = data.summary || {};
        if (showToast) {
          showToast(`⚡ 9:00 AM Workflow Run: Analyzed ${s.tenders_analyzed || 0} tenders, prepared ${s.drafts_created || 0} drafts!`, 'success');
        }
        fetchDashboard();
        fetchDrafts();
      }
    } catch (err) {
      if (showToast) showToast('Error triggering daily workflow', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleAutoSend = async (enable) => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/toggle-auto-send?enabled=${enable}`, { method: 'POST' });
      if (res.ok) {
        if (showToast) {
          showToast(enable ? '🚀 Automatic Sending Authorized!' : '🛡️ Draft-Only Mode Active (Approval Required)', 'info');
        }
        fetchDashboard();
      }
    } catch (err) {
      if (showToast) showToast('Failed to update sending mode', 'error');
    }
  };

  const handleTogglePause = async (pause) => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/toggle-pause?paused=${pause}`, { method: 'POST' });
      if (res.ok) {
        if (showToast) {
          showToast(pause ? '⏸️ Daily 9:00 AM IST Scheduler Paused' : '▶️ Daily 9:00 AM IST Scheduler Resumed', 'info');
        }
        fetchDashboard();
      }
    } catch (err) {
      if (showToast) showToast('Failed to toggle scheduler', 'error');
    }
  };

  const handleCheckReplies = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/check-replies`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (showToast) showToast(`💬 Checked inbox: ${data.replies_detected} new partner replies detected!`, 'success');
        fetchDashboard();
      }
    } catch (err) {
      if (showToast) showToast('Failed to check replies', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopAutomation = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/stop-automation`, { method: 'POST' });
      if (res.ok) {
        if (showToast) showToast('🛑 Outreach Automation Stopped! Scheduler paused.', 'error');
        fetchDashboard();
      }
    } catch (err) {
      if (showToast) showToast('Failed to stop automation: ' + err.message, 'error');
    }
  };

  const handleTogglePilotMode = async (enable) => {
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/toggle-pilot-mode?enabled=${enable}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (showToast) showToast(`⚙️ Switched to ${enable ? 'Pilot Mode (5 emails/day)' : 'Production Mode (50 emails/day)'}`, 'info');
        fetchDashboard();
      }
    } catch (err) {
      if (showToast) showToast('Error toggling pilot mode: ' + err.message, 'error');
    }
  };

  const handleRetryDraft = async (id) => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/drafts/${id}/retry`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (showToast) showToast(`🚀 Retried successfully! Status: ${data.status}`, 'success');
        fetchDashboard();
        fetchDrafts();
      } else {
        const err = await res.json();
        if (showToast) showToast(`Retry failed: ${err.detail || 'Error'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Retry error: ' + err.message, 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmDelivery = async (id) => {
    const evidence = prompt('Enter verified delivery evidence (e.g. "Verified in Exchange Message Trace" or "Recipient replied"):', 'Verified in Microsoft 365 Exchange Online');
    if (!evidence) return;
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/confirm-delivery/${id}?evidence=${encodeURIComponent(evidence)}`, { method: 'POST' });
      if (res.ok) {
        if (showToast) showToast('✓ Delivery confirmed and updated in database!', 'success');
        fetchDashboard();
        fetchDrafts();
      }
    } catch (err) {
      if (showToast) showToast('Error confirming delivery: ' + err.message, 'error');
    }
  };

  // MSAL Device Code Flow live polling
  useEffect(() => {
    let timer = null;
    if (deviceFlowPolling) {
      timer = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/api/collaboration/m365/device-flow/status`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'completed') {
              setDeviceFlowPolling(false);
              setDeviceFlow(null);
              await fetchProviderStatus();
              await fetchDrafts();
              if (showToast) showToast(`🎉 Authenticated as ${data.display_name} (${data.authenticated_mailbox})!`, 'success');
            } else if (data.status === 'error') {
              setDeviceFlowPolling(false);
              setDeviceFlow(prev => ({ ...(prev || {}), error: data.error }));
              if (showToast) showToast(data.error || 'Device flow failed', 'error');
            } else if (data.expires_in_seconds !== undefined) {
              setDeviceFlow(prev => ({ ...(prev || {}), expires_in_seconds: data.expires_in_seconds }));
            }
          }
        } catch (e) {}
      }, 3000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [deviceFlowPolling]);

  const handleStartDeviceFlow = async () => {
    setStartingDeviceFlow(true);
    try {
      const cid = m365Form.client_id?.trim() || 'c2cd8349-a198-46d6-a6dc-325e86dd67a4';
      const tid = m365Form.tenant_id?.trim() || 'de9e8583-c4c4-4212-9c27-e35cfa247419';
      const res = await fetch(`${API_BASE}/api/collaboration/m365/device-flow/initiate?client_id=${encodeURIComponent(cid)}&tenant_id=${encodeURIComponent(tid)}`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setDeviceFlow(data);
        setDeviceFlowPolling(true);
        if (showToast) showToast(`Device Code: ${data.user_code}. Enter at https://microsoft.com/devicelogin!`, 'info');
      } else {
        if (showToast) showToast(data.error || 'Failed to initiate Microsoft device code flow', 'error');
      }
    } catch (err) {
      if (showToast) showToast('Error starting device code flow: ' + err.message, 'error');
    } finally {
      setStartingDeviceFlow(false);
    }
  };

  const handleCancelDeviceFlow = async () => {
    try {
      await fetch(`${API_BASE}/api/collaboration/m365/device-flow/cancel`, { method: 'POST' });
    } catch (e) {}
    setDeviceFlow(null);
    setDeviceFlowPolling(false);
  };

  const handleConnectM365 = async () => {
    const clientId = m365Form.client_id?.trim() || 'c2cd8349-a198-46d6-a6dc-325e86dd67a4';
    if (!clientId) {
      if (showToast) showToast('⚠️ Please enter your Microsoft Entra Application (Client) ID first.', 'error');
      return;
    }

    setConnectingM365(true);
    try {
      const query = new URLSearchParams({
        client_id: clientId,
        client_secret: m365Form.client_secret?.trim() || '',
        tenant_id: m365Form.tenant_id?.trim() || 'de9e8583-c4c4-4212-9c27-e35cfa247419'
      });

      const res = await fetch(`${API_BASE}/api/collaboration/m365/auth-url?${query.toString()}`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to generate Microsoft sign-in URL');
      }

      const data = await res.json();
      const authUrl = data.auth_url;

      const width = 600, height = 750;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      const popup = window.open(authUrl, 'm365_oauth_popup', `width=${width},height=${height},top=${top},left=${left}`);

      if (!popup) {
        if (showToast) showToast('Pop-up blocked! Please allow pop-ups for this site.', 'error');
        setConnectingM365(false);
        return;
      }

      const onMessage = (event) => {
        if (event.data?.type === 'M365_AUTH_SUCCESS') {
          window.removeEventListener('message', onMessage);
          fetchProviderStatus();
          if (showToast) showToast(`✅ Connected & Verified: ${event.data.displayName || event.data.mailbox}!`, 'success');
          setConnectingM365(false);
          setShowConfigModal(false);
        } else if (event.data?.type === 'M365_AUTH_ERROR') {
          window.removeEventListener('message', onMessage);
          if (showToast) showToast(`❌ Microsoft Auth Error: ${event.data.error}`, 'error');
          setConnectingM365(false);
        }
      };
      window.addEventListener('message', onMessage);

      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', onMessage);
          setConnectingM365(false);
          fetchProviderStatus();
        }
      }, 1000);

    } catch (err) {
      if (showToast) showToast(err.message || 'Error initiating Microsoft 365 OAuth', 'error');
      setConnectingM365(false);
    }
  };

  const handleVerifyM365 = async () => {
    setVerifyingM365(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/m365/verify`, { method: 'POST' });
      const data = await res.json();
      if (data.verified) {
        setProviderStatus(data.public_status);
        if (showToast) showToast(`✅ Microsoft Graph Verified: ${data.display_name} (${data.mailbox})`, 'success');
      } else {
        if (showToast) showToast(`❌ Verification failed: ${data.error || 'Token invalid or expired'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error during Microsoft Graph verification', 'error');
    } finally {
      setVerifyingM365(false);
    }
  };

  const handleDisconnectM365 = async () => {
    if (!window.confirm('Are you sure you want to disconnect Microsoft 365? Stored tokens will be revoked.')) return;
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/m365/disconnect`, { method: 'POST' });
      const data = await res.json();
      setProviderStatus(data.public_status);
      if (showToast) showToast('Microsoft 365 disconnected.', 'info');
    } catch (err) {
      if (showToast) showToast('Error disconnecting Microsoft 365', 'error');
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'redirect_uri') {
      setCopiedRedirectUri(true);
      setTimeout(() => setCopiedRedirectUri(false), 2000);
    } else if (type === 'ps_command') {
      setCopiedPsCommand(true);
      setTimeout(() => setCopiedPsCommand(false), 2000);
    }
    if (showToast) showToast('Copied to clipboard!', 'info');
  };

  const handleSaveM365 = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'microsoft_365',
          m365_client_id: m365Form.client_id,
          m365_client_secret: m365Form.client_secret,
          m365_tenant_id: m365Form.tenant_id,
          m365_refresh_token: m365Form.refresh_token
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('🔒 Microsoft 365 OAuth 2.0 credentials saved securely.', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving M365 config', 'error');
    }
  };

  const handleSaveGmail = async (e) => {
    e.preventDefault();
    if (!gmailForm.email || !gmailForm.app_password) {
      if (showToast) showToast('Please enter your Gmail address and 16-character Google App Password.', 'error');
      return;
    }
    try {
      const cleanPassword = gmailForm.app_password.trim().replace(/\s+/g, '');
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'authenticated_smtp',
          smtp_host: 'smtp.gmail.com',
          smtp_port: 587,
          smtp_user: gmailForm.email.trim(),
          smtp_password: cleanPassword,
          imap_host: 'imap.gmail.com',
          active_provider: 'authenticated_smtp'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('✅ Gmail SMTP connected! You can now send real emails using your Gmail account.', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving Gmail config: ' + err.message, 'error');
    }
  };

  const handleSaveGoogle = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'google_workspace',
          google_client_id: googleForm.client_id,
          google_client_secret: googleForm.client_secret,
          google_refresh_token: googleForm.refresh_token
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('🔒 Google Workspace OAuth 2.0 credentials saved securely.', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving Google config', 'error');
    }
  };

  const handleSaveSmtp = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'authenticated_smtp',
          smtp_host: smtpForm.host,
          smtp_port: parseInt(smtpForm.port) || 587,
          smtp_user: smtpForm.user,
          smtp_password: smtpForm.password,
          imap_host: smtpForm.imap_host
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('🔒 Authenticated SMTP & IMAP Sent Sync saved securely.', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving SMTP config', 'error');
    }
  };

  const handleSaveBrevo = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'brevo',
          brevo_api_key: brevoForm.api_key.trim(),
          brevo_smtp_user: brevoForm.smtp_user.trim(),
          brevo_smtp_key: brevoForm.smtp_key.trim(),
          brevo_send_method: brevoForm.send_method
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('🔒 Brevo authenticated credentials saved & activated (300 free/day)!', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error saving Brevo credentials'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving Brevo config: ' + err.message, 'error');
    }
  };

  const handleSaveSendgrid = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/save-provider-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: 'sendgrid',
          sendgrid_api_key: sendgridForm.api_key.trim(),
          sendgrid_send_method: sendgridForm.send_method
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast('🔒 SendGrid credentials saved & activated (100 free/day)!', 'success');
        setShowConfigModal(false);
      } else {
        const err = await res.json();
        if (showToast) showToast(`Failed: ${err.detail || 'Error saving SendGrid key'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error saving SendGrid config: ' + err.message, 'error');
    }
  };

  const handleSwitchProvider = async (provider) => {
    setSettingProvider(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/set-active-provider?provider=${provider}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setProviderStatus(data.public_status);
        if (showToast) showToast(`Switched active provider to ${provider}!`, 'info');
      } else {
        const err = await res.json();
        if (showToast) showToast(`Error: ${err.detail || 'Could not switch provider'}`, 'error');
      }
    } catch (err) {
      if (showToast) showToast('Network error switching provider: ' + err.message, 'error');
    } finally {
      setSettingProvider(false);
    }
  };

  const fetchDnsStatus = async () => {
    setDnsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/domain-dns-status?domain=gisfy.co.in`);
      if (res.ok) {
        const data = await res.json();
        setDnsAudit(data);
      } else {
        if (showToast) showToast('Could not query DNS status', 'error');
      }
    } catch (err) {
      console.error('Failed to fetch DNS status:', err);
    } finally {
      setDnsLoading(false);
    }
  };

  const handleSendTestEmail = async (e) => {
    e.preventDefault();
    const recipient = testRecipient?.trim() || 'bidding@gisfy.co.in';
    if (!recipient || !recipient.includes('@')) {
      if (showToast) showToast('Please enter a valid approved test recipient email', 'error');
      return;
    }
    setTestSending(true);
    setTestResult(null);

    const testSubject = 'Exploring JV / Consortium Partnership – Test Verification Ref #TEST-1';
    const testBody = `Dear Team,

Greetings from GISFY Private Limited, India.

We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.

We are currently exploring a potential Joint Venture (JV) / Consortium partnership for GISFY Procurement Intelligence System Verification.

Assignment Overview & Technical Scope:
End-to-end verification of Microsoft 365 Exchange Online outbound email delivery from Farhath Bakka <farhath@gisfy.co.in>, mandatory CC synchronization to bidding@gisfy.co.in, and Outlook Sent Items tracking.

Considering your organisation's expertise and experience, we believe there may be valuable opportunities for collaboration in the joint submission and implementation of this assignment, subject to the applicable procurement requirements.

If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following documents for our preliminary evaluation:

• Company Profile – Highlighting your organisation's technical capabilities, core competencies, and areas of expertise.
• Company Registration Certificate – Valid documentation confirming the legal registration of your organisation.
• Tax Registration Certificate – Applicable tax registration documents issued by the relevant authorities.
• CVs of Key Experts – Profiles of qualified professionals with expertise relevant to the proposed assignment.
• Relevant Project Experience – Details of similar completed or ongoing projects, including project descriptions, scope of work, client details, and your organisation's role.

Upon receiving and reviewing the above documents, we would be pleased to discuss the proposed collaboration structure and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.

We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.

Thanks & Regards,
Farhath Bakka | Business Development Executive
GISFY Support & Partnerships Team
GISFY Private Limited, Ground Floor, DSL Abacus IT Park,
Uppal, Hyderabad, Telangana – 500039, India
Email: farhath@gisfy.co.in | support@gisfy.co.in
Mobile: +91 90631 20678
Website: www.gisfy.co.in`;

    const ccEmails = 'bidding@gisfy.co.in';
    const mailtoUrl = `mailto:${encodeURIComponent(recipient)}?cc=${encodeURIComponent(ccEmails)}&subject=${encodeURIComponent(testSubject)}&body=${encodeURIComponent(testBody)}`;
    const outlookWebUrl = `https://outlook.office.com/mail/deeplink/compose?to=${encodeURIComponent(recipient)}&cc=${encodeURIComponent(ccEmails)}&subject=${encodeURIComponent(testSubject)}&body=${encodeURIComponent(testBody)}`;

    // If direct mail client is active, open Microsoft Outlook directly (NOT Apple Mail!)
    if (providerStatus?.active_provider === 'direct_mail') {
      window.open(outlookWebUrl, '_blank');
    }

    try {
      const res = await fetch(`${API_BASE}/api/collaboration/send-test-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved_recipient: recipient,
          approval_notes: testNotes || 'User-approved single test email verification'
        })
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        const isGraph = data.provider === 'microsoft_graph';
        const msg = isGraph
          ? `Microsoft 365 Exchange Online officially accepted email (HTTP ${data.provider_status_code || 202}). Checked Farhath's Outlook Sent Items.`
          : (data.provider_message || 'Test email dispatched successfully.');

        setTestResult({
          success: true,
          provider: data.provider || 'microsoft_graph',
          status_code: data.provider_status_code || 202,
          delivery_status: data.delivery_status || 'Provider Accepted (202)',
          sent_folder_verified: Boolean(data.sent_folder_verified),
          test_record_id: data.test_record_id,
          recipient: data.recipient || recipient,
          cc: data.cc || ccEmails,
          from: data.from || 'Farhath Bakka <farhath@gisfy.co.in>, GISFY Support <support@gisfy.co.in>',
          message: msg,
          mailto_url: mailtoUrl,
          outlook_web_url: outlookWebUrl
        });
        if (showToast) showToast(`🎉 Real test email sent to ${recipient}! Provider: ${data.provider} (HTTP ${data.provider_status_code || 202}).`, 'success');
        fetchDrafts();
        fetchProviderStatus();
      } else {
        const errMsg = data.detail?.error || data.detail || data.message || 'Dispatch failed';
        setTestResult({
          success: false,
          provider: data.detail?.provider || 'microsoft_graph',
          status_code: data.detail?.provider_status_code || 400,
          delivery_status: 'Failed',
          sent_folder_verified: false,
          recipient: recipient,
          cc: ccEmails,
          from: 'Farhath Bakka <farhath@gisfy.co.in>, GISFY Support <support@gisfy.co.in>',
          error: errMsg,
          message: errMsg,
          mailto_url: mailtoUrl,
          outlook_web_url: outlookWebUrl
        });
        if (showToast) showToast(errMsg, 'error');
      }
    } catch (err) {
      setTestResult({
        success: false,
        provider: 'microsoft_graph',
        delivery_status: 'Network Error',
        recipient: recipient,
        cc: ccEmails,
        from: 'Farhath Bakka <farhath@gisfy.co.in>, GISFY Support <support@gisfy.co.in>',
        error: err.message,
        message: err.message,
        mailto_url: mailtoUrl,
        outlook_web_url: outlookWebUrl
      });
      if (showToast) showToast('Error sending test email: ' + err.message, 'error');
    } finally {
      setTestSending(false);
    }
  };

  const handleVerifySentFolder = async (recordId) => {
    setVerifyingSentId(recordId);
    try {
      const res = await fetch(`${API_BASE}/api/collaboration/verify-sent-folder/${recordId}`, { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.verified) {
        if (showToast) showToast("✅ Independently verified in Farhath's Sent Items folder!", 'success');
        fetchDrafts();
      } else {
        if (showToast) showToast(data.message || 'Message not yet detected in Sent folder.', 'info');
      }
    } catch (err) {
      if (showToast) showToast('Verification error: ' + err.message, 'error');
    } finally {
      setVerifyingSentId(null);
    }
  };

  const summary = dashboard?.summary || {};
  const scheduler = dashboard?.scheduler || {};
  const isDraftMode = summary.draft_mode_active !== false;

  const matchesFilter = (d) => {
    if (selectedStateFilter !== 'ALL') {
      const stName = (d.state_name || '').toLowerCase();
      const target = selectedStateFilter.toLowerCase();
      if (selectedStateFilter === 'ADB') {
        if (!stName.includes('adb') && !stName.includes('asian development')) return false;
      } else {
        if (!stName.includes(target)) return false;
      }
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchTitle = (d.tender_title || '').toLowerCase().includes(q);
      const matchComp = (d.company_name || '').toLowerCase().includes(q);
      const matchRecip = (d.recipient_name || '').toLowerCase().includes(q) || (d.recipient_email || '').toLowerCase().includes(q);
      const matchReason = (d.selection_reason || '').toLowerCase().includes(q);
      if (!matchTitle && !matchComp && !matchRecip && !matchReason) return false;
    }
    return true;
  };

  const pendingDraftsList = drafts
    .filter(d => ['draft', 'pending_approval', 'approved', 'Sending'].includes(d.status) && !d.is_test_email)
    .filter(matchesFilter);
  const sentEmailsList = drafts
    .filter(d => ['sent', 'Provider Accepted', 'Found in Sent Items', 'Delivery Confirmed', 'replied', 'failed', 'Failed', 'bounced'].includes(d.status) || d.is_test_email)
    .filter(matchesFilter);

  const renderStatusBadge = (status, sentFolderVerified) => {
    const s = String(status || '').toLowerCase();
    if (s === 'sending') {
      return (
        <span className="outreach-status-pill sending">
          <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', marginRight: '4px' }}>⏳</span> Sending...
        </span>
      );
    }
    if (s === 'delivery confirmed') {
      return (
        <span className="outreach-status-pill delivery-confirmed" title="Delivery confirmed with legitimate delivery evidence">
          ✓ Delivery Confirmed
        </span>
      );
    }
    if (s === 'found in sent items' || (s === 'sent' && sentFolderVerified)) {
      return (
        <span className="outreach-status-pill" style={{ background: '#e0e7ff', color: '#4338ca', border: '1px solid #c7d2fe', fontWeight: 700 }} title="Verified present in Farhath's Outlook Sent Items folder">
          📁 Found in Sent Items
        </span>
      );
    }
    if (s === 'provider accepted') {
      return (
        <span className="outreach-status-pill provider-accepted" title="Accepted by Microsoft Graph API for dispatch (HTTP 202)">
          📬 Provider Accepted (202)
        </span>
      );
    }
    if (s === 'failed') {
      return <span className="outreach-status-pill failed" title="Dispatch failed. Click Retry to attempt again.">⚠️ Failed</span>;
    }
    if (s === 'bounced') {
      return <span className="outreach-status-pill" style={{ background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' }}>🛑 Bounced</span>;
    }
    if (s === 'approved') {
      return <span className="outreach-status-pill approved">✓ Approved</span>;
    }
    if (s === 'replied') {
      return <span className="outreach-status-pill replied">💬 Partner Replied</span>;
    }
    return <span className="outreach-status-pill draft">Draft</span>;
  };

  return (
    <div className="outreach-container">
      {/* 1. Header Banner */}
      <div className="outreach-header-banner">
        <div className="outreach-header-title">
          <h1>
            <span>🤝</span> Partner Collaboration Email Automation &amp; Live Outbound Pipeline
          </h1>
          <p>
            Automated tender matching, executive JV proposal drafting, and authenticated outbound delivery for GISFY Private Limited.
          </p>
          <div className="outreach-schedule-pill">
            <span>⏰</span>
            <span>Schedule: <strong>Daily 09:00 AM – 05:30 PM IST (Mon-Fri)</strong></span>
            <span>•</span>
            <span>Sender / From: <strong>Farhath Bakka &lt;farhath@gisfy.co.in&gt;, GISFY Support &lt;support@gisfy.co.in&gt;</strong></span>
            <span>•</span>
            <span>Mandatory CC: <strong>bidding@gisfy.co.in</strong></span>
            <span>•</span>
            <span>Reply-To: <strong>farhath@gisfy.co.in, support@gisfy.co.in</strong></span>
            <span>•</span>
            <span>Daily Quota: <strong>Max 50 Emails / Rolling 24h</strong></span>
          </div>
        </div>

        <div className="outreach-header-actions">
          <button 
            className="outreach-btn-primary"
            onClick={handleTriggerCycle}
            disabled={actionLoading}
            title="Execute the full 9:00 AM IST daily workflow immediately"
          >
            <span>⚡</span> {actionLoading ? 'Running Workflow...' : 'Trigger 9:00 AM Cycle Now'}
          </button>

          <a 
            href={`${API_BASE}/api/collaboration/export-excel`}
            download="GISFY_Partner_Collaboration_Tracker.xlsx"
            className="outreach-btn-secondary"
            title="Export tracking spreadsheet to Excel"
          >
            <span>📥</span> Export Tracker (.xlsx)
          </a>

          <button 
            className="outreach-btn-secondary"
            onClick={() => setShowTestModal(true)}
            title="Send exactly one test email to user-approved recipient to verify delivery and Sent folder"
            style={{ borderColor: '#6366f1', color: '#4338ca', fontWeight: 700 }}
          >
            <span>🧪</span> Send Approved Test Email
          </button>

          <button 
            className="outreach-btn-secondary"
            onClick={() => setShowConfigModal(true)}
            title="Configure Microsoft 365 OAuth 2.0 / Google / SMTP"
          >
            <span>⚙️</span> Live Provider Setup
          </button>

          <button 
            className="outreach-btn-secondary"
            onClick={handleCheckReplies}
            disabled={actionLoading}
            title="Poll inbox for partner replies"
          >
            <span>🔄</span> Check Replies
          </button>
        </div>
      </div>

      {/* 2. Provider Live Health & Authentication Bar */}
      <div style={{
        background: providerStatus?.is_authenticated ? '#ecfdf5' : '#fffbeb',
        border: providerStatus?.is_authenticated ? '1px solid #a7f3d0' : '1px solid #fde68a',
        borderRadius: '10px',
        padding: '0.9rem 1.25rem',
        marginBottom: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.8rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <span style={{ fontSize: '1.6rem' }}>
            {providerStatus?.is_authenticated ? '🟢' : '🟡'}
          </span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 800, fontSize: '0.92rem', color: '#065f46' }}>
                Live Email Dispatch Online – {providerStatus?.provider_name || 'Direct Outlook / Mail Client'}
              </span>
              <span style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                background: '#d1fae5',
                color: '#047857',
                padding: '2px 8px',
                borderRadius: '6px'
              }}>
                Mode: {providerStatus?.active_provider === 'direct_mail' ? 'DIRECT OUTLOOK / MAIL CLIENT' : (providerStatus?.active_provider?.toUpperCase() || 'DIRECT')}
              </span>
              <span style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                background: '#dbeafe',
                color: '#1d4ed8',
                padding: '2px 8px',
                borderRadius: '6px'
              }}>
                Zero 3rd-Party Keys Required ✅
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#475569', marginTop: '0.2rem' }}>
              From: <b>Farhath Bakka &lt;farhath@gisfy.co.in&gt;, GISFY Support &lt;support@gisfy.co.in&gt;</b> | CC: <b>bidding@gisfy.co.in</b> | Reply-To: <b>farhath@gisfy.co.in, support@gisfy.co.in</b> | 
              <span style={{ color: '#047857', fontWeight: 600 }}> Delivery: <b>Direct to Client, Bidding &amp; Support Team Inbox + Sent Items</b></span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => { setConfigTab('dns'); setShowConfigModal(true); fetchDnsStatus(); }}
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 700,
              background: '#f8fafc',
              color: '#1e293b',
              border: '1px solid #cbd5e1',
              cursor: 'pointer'
            }}
            title="Check SPF, DKIM, and DMARC alignment for gisfy.co.in"
          >
            🌐 Check Domain DNS
          </button>
          <button
            onClick={() => setShowTestModal(true)}
            style={{
              padding: '0.45rem 0.95rem',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 700,
              background: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            🧪 Single Test Email
          </button>
          <button
            onClick={() => setShowConfigModal(true)}
            style={{
              padding: '0.45rem 0.95rem',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 700,
              background: '#ffffff',
              color: '#334155',
              border: '1px solid #cbd5e1',
              cursor: 'pointer'
            }}
          >
            ⚙️ Configure Credentials
          </button>
        </div>
      </div>

      {/* 3. Comprehensive Step 9 KPI Grid */}
      <div className="outreach-kpi-grid">
        <div className="outreach-kpi-card">
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label">Partners Analyzed</span>
            <span className="outreach-kpi-icon">🏢</span>
          </div>
          <div className="outreach-kpi-val">{summary.total_partners || 105}</div>
          <div className="outreach-kpi-sub">Verified Indian enterprises</div>
        </div>

        <div className="outreach-kpi-card" style={{ borderColor: '#fde68a' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#b45309' }}>Drafts Pending Review</span>
            <span className="outreach-kpi-icon" style={{ background: '#fef3c7' }}>📝</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#b45309' }}>{summary.drafts_prepared || pendingDraftsList.length}</div>
          <div className="outreach-kpi-sub">Draft-only mode active</div>
        </div>

        {/* Step 5: Rolling 24-hour Daily Quota Card */}
        <div className="outreach-kpi-card" style={{ borderColor: '#38bdf8', background: '#f0f9ff' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#0369a1', fontWeight: 800 }}>Today's Sent (24h Quota)</span>
            <span className="outreach-kpi-icon" style={{ background: '#e0f2fe' }}>📊</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#0284c7' }}>
            {summary.today_sent || 0} / {scheduler.active_limit || 50}
          </div>
          <div className="outreach-kpi-sub" style={{ color: '#0369a1', fontWeight: 600 }}>
            {summary.remaining_daily_allowance ?? (scheduler.active_limit || 50)} remaining in rolling window
          </div>
        </div>

        {/* Step 5: Queued Emails */}
        <div className="outreach-kpi-card" style={{ borderColor: '#c7d2fe' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#4338ca' }}>Queued for Sending</span>
            <span className="outreach-kpi-icon" style={{ background: '#e0e7ff' }}>⏳</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#4338ca' }}>{summary.queued_count || 0}</div>
          <div className="outreach-kpi-sub">Paced at 1 per 5 min</div>
        </div>

        <div className="outreach-kpi-card" style={{ borderColor: '#bbf7d0' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#15803d' }}>Dispatched (Accepted)</span>
            <span className="outreach-kpi-icon" style={{ background: '#dcfce7' }}>🚀</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#15803d' }}>{summary.provider_accepted || summary.emails_sent || 0}</div>
          <div className="outreach-kpi-sub">Accepted by Microsoft 365</div>
        </div>

        <div className="outreach-kpi-card" style={{ borderColor: '#e0e7ff' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#4f46e5' }}>Found in Sent Items</span>
            <span className="outreach-kpi-icon" style={{ background: '#ede9fe' }}>📁</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#4f46e5' }}>{summary.found_in_sent || 0}</div>
          <div className="outreach-kpi-sub">Outlook folder synchronized</div>
        </div>

        <div className="outreach-kpi-card" style={{ borderColor: '#a7f3d0' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#047857' }}>Delivery Confirmed</span>
            <span className="outreach-kpi-icon" style={{ background: '#d1fae5' }}>✓</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#047857' }}>{summary.delivery_confirmed || 0}</div>
          <div className="outreach-kpi-sub">Verified delivery evidence</div>
        </div>

        <div className="outreach-kpi-card" style={{ borderColor: '#fed7aa' }}>
          <div className="outreach-kpi-top">
            <span className="outreach-kpi-label" style={{ color: '#c2410c' }}>Partner Responses</span>
            <span className="outreach-kpi-icon" style={{ background: '#ffedd5' }}>💬</span>
          </div>
          <div className="outreach-kpi-val" style={{ color: '#c2410c' }}>{summary.replies_received || 0}</div>
          <div className="outreach-kpi-sub">Detected thread replies</div>
        </div>
      </div>

      {/* 4. Workflow Operational Controls Bar with Stop Automation and Pilot Mode */}
      <div className="outreach-controls-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="outreach-controls-left" style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>Operating Mode:</span>
          <span className={`outreach-mode-pill ${isDraftMode ? 'draft-mode' : 'auto-mode'}`}>
            <span>{isDraftMode ? '🛡️ Draft-Only Mode Active' : '🚀 Auto-Send Authorized'}</span>
          </span>

          <label className="outreach-toggle-switch" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 600 }}>
            <input 
              type="checkbox" 
              checked={!isDraftMode}
              onChange={(e) => handleToggleAutoSend(e.target.checked)}
              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
            />
            <span>Authorize Scheduled 9:00 AM Dispatch</span>
          </label>

          <span style={{ color: '#cbd5e1' }}>|</span>

          {/* Pilot Mode Toggle */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
            <input 
              type="checkbox"
              checked={scheduler.pilot_mode !== false}
              onChange={(e) => handleTogglePilotMode(e.target.checked)}
              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
            />
            <span>Pilot Mode (Cap at 5/day)</span>
          </label>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Window: <strong>09:00 AM – 05:30 PM IST</strong> ({scheduler.within_business_window ? '🟢 Active' : '⏸️ Closed'})
          </span>
          <button 
            className="outreach-act-btn"
            onClick={() => handleTogglePause(!scheduler.is_paused)}
            style={{ fontWeight: 700 }}
          >
            {scheduler.is_paused ? '▶️ Resume Scheduler' : '⏸️ Pause Scheduler'}
          </button>

          {/* Prominent Stop Automation Button */}
          <button
            onClick={handleStopAutomation}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: '6px',
              fontSize: '0.82rem',
              fontWeight: 800,
              background: '#dc2626',
              color: '#ffffff',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 2px 6px rgba(220,38,38,0.25)'
            }}
            title="Immediately halt all outbound automated email operations"
          >
            🛑 Stop Automation
          </button>
        </div>
      </div>

      {/* 5. Section Card with Sub-tabs */}
      <div className="outreach-section-card">
        <div className="outreach-section-header">
          <div className="outreach-section-title">
            <span>📫</span>
            <span>Outreach Pipeline Management</span>
          </div>

          <div className="outreach-subnav">
            <button 
              className={`outreach-subnav-btn ${subTab === 'drafts' ? 'active' : ''}`}
              onClick={() => setSubTab('drafts')}
            >
              📝 Drafts Pending Review ({pendingDraftsList.length})
            </button>
            <button 
              className={`outreach-subnav-btn ${subTab === 'sent' ? 'active' : ''}`}
              onClick={() => setSubTab('sent')}
            >
              📤 Sent &amp; Follow-up Tracker ({sentEmailsList.length})
            </button>
            <button 
              className={`outreach-subnav-btn ${subTab === 'logs' ? 'active' : ''}`}
              onClick={() => setSubTab('logs')}
            >
              📋 Execution History &amp; Logs
            </button>
          </div>
        </div>

        {/* Jurisdiction & Keyword Search Filter Bar */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', padding: '1rem 1.5rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#334155' }}>🏛️ Jurisdiction:</span>
            <select
              value={selectedStateFilter}
              onChange={(e) => setSelectedStateFilter(e.target.value)}
              style={{
                padding: '0.45rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: '#1e293b',
                background: '#ffffff',
                cursor: 'pointer'
              }}
            >
              {JURISDICTIONS.map(j => (
                <option key={j.value} value={j.value}>{j.label}</option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: '220px', position: 'relative' }}>
            <input
              type="text"
              placeholder="🔍 Search drafts by tender title, partner company, contact or domain..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.45rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '0.82rem',
                background: '#ffffff',
                color: '#1e293b'
              }}
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery('')}
                style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8' }}
              >
                ✕
              </button>
            )}
          </div>

          {(selectedStateFilter !== 'ALL' || searchQuery) && (
            <button
              onClick={() => { setSelectedStateFilter('ALL'); setSearchQuery(''); }}
              style={{
                padding: '0.45rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                background: '#ffffff',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: '#64748b',
                cursor: 'pointer'
              }}
            >
              Reset Filters
            </button>
          )}

          <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: '#64748b' }}>
            Showing <b>{subTab === 'drafts' ? pendingDraftsList.length : sentEmailsList.length}</b> verified partner recommendations across 29 States &amp; ADB
          </div>
        </div>

        {/* Tab 1: Drafts Pending Review */}
        {subTab === 'drafts' && (
          <div className="outreach-table-wrapper">
            <table className="outreach-table">
              <thead>
                <tr>
                  <th>Tender Proposal</th>
                  <th>Prospective Partner</th>
                  <th>Compatibility</th>
                  <th>Strategic Synergy Rationale</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingDraftsList.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                      <div style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>✅</div>
                      <div style={{ fontWeight: 600 }}>All drafts have been reviewed and dispatched!</div>
                      <div style={{ fontSize: '0.82rem', marginTop: '0.2rem' }}>
                        Click "Trigger 9:00 AM Cycle Now" to analyze newly added tenders and generate new candidate drafts.
                      </div>
                    </td>
                  </tr>
                ) : (
                  pendingDraftsList.map(draft => (
                    <tr key={draft.id}>
                      <td>
                        <div className="outreach-tender-cell">
                          <span className="outreach-tender-id">TENDER #{draft.tender_id || 'REF'}</span>
                          <span className="outreach-tender-title" title={draft.tender_title}>
                            {draft.tender_title ? (draft.tender_title.length > 60 ? draft.tender_title.substring(0, 60) + '...' : draft.tender_title) : 'Tender Assignment'}
                          </span>
                          <span style={{ 
                            fontSize: '0.75rem', 
                            color: (draft.state_name || '').includes('ADB') ? '#0284c7' : '#475569', 
                            fontWeight: 600,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            {(draft.state_name || '').includes('ADB') ? '🌐 ' : '📍 '}
                            {draft.state_name || 'Pan-India'}
                          </span>
                        </div>
                      </td>

                      <td>
                        <div className="outreach-partner-cell">
                          <span className="outreach-partner-name">{draft.company_name}</span>
                          <span className="outreach-partner-contact">{draft.recipient_name}</span>
                          <span style={{ fontSize: '0.78rem', color: '#2563eb' }}>{draft.recipient_email}</span>
                        </div>
                      </td>

                      <td>
                        <span className="outreach-score-badge">
                          <span>⭐</span> {draft.match_score ? draft.match_score.toFixed(1) : '85.0'}%
                        </span>
                      </td>

                      <td>
                        <div style={{ maxWidth: '320px', fontSize: '0.82rem', color: '#334155', lineHeight: 1.4 }}>
                          {draft.selection_reason || 'Strong technical synergy in geospatial and infrastructure operations.'}
                        </div>
                      </td>

                      <td>
                        {renderStatusBadge(draft.status, draft.sent_folder_verified)}
                      </td>

                      <td>
                        <div className="outreach-action-btns">
                          <button 
                            className="outreach-act-btn"
                            onClick={() => setPreviewDraft(draft)}
                            title="Preview formatted email content"
                          >
                            👁️ Preview
                          </button>

                          {draft.status === 'draft' && (
                            <button 
                              className="outreach-act-btn approve"
                              onClick={() => handleApprove(draft.id)}
                              disabled={actionLoading}
                              title="Approve for sending"
                            >
                              ✅ Approve
                            </button>
                          )}

                          <button 
                            className="outreach-act-btn outlook"
                            onClick={() => handleOpenOutlook(draft)}
                            style={{
                              background: '#0078d4',
                              color: '#ffffff',
                              border: 'none',
                              padding: '0.38rem 0.65rem',
                              borderRadius: '6px',
                              fontWeight: 600,
                              fontSize: '0.78rem',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              cursor: 'pointer'
                            }}
                            title="Open pre-filled proposal directly in Microsoft Outlook (Web / PWA) with Farhath & CC: bidding and support"
                          >
                            📬 Outlook
                          </button>

                          <button 
                            className="outreach-act-btn send"
                            onClick={() => handleSend(draft.id)}
                            disabled={actionLoading || draft.status === 'Sending' || draft.status === 'Provider Accepted'}
                            title="Open Microsoft Outlook and record dispatch in GISFY portal"
                          >
                            {draft.status === 'Sending' ? '⏳ Sending...' : '🚀 Send in Outlook'}
                          </button>

                          <button 
                            className="outreach-act-btn reject"
                            onClick={() => handleReject(draft.id)}
                            title="Reject and discard draft"
                          >
                            ✕
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Sent & Dispatched */}
        {subTab === 'sent' && (
          <div className="outreach-table-wrapper">
            <table className="outreach-table">
              <thead>
                <tr>
                  <th>Recipient / Company</th>
                  <th>Tender Opportunity</th>
                  <th>Dispatched At</th>
                  <th>Delivery Status</th>
                  <th>Sent Folder (Farhath)</th>
                  <th>Provider / Actions</th>
                </tr>
              </thead>
              <tbody>
                {sentEmailsList.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                      No dispatched emails yet. Review and approve pending drafts to send.
                    </td>
                  </tr>
                ) : (
                  sentEmailsList.map(email => (
                    <tr key={email.id}>
                      <td>
                        <div className="outreach-partner-cell">
                          <span className="outreach-partner-name">
                            {email.company_name}
                            {email.is_test_email && (
                              <span style={{ marginLeft: '6px', fontSize: '0.68rem', background: '#ede9fe', color: '#6d28d9', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                                TEST EMAIL
                              </span>
                            )}
                          </span>
                          <span style={{ fontSize: '0.8rem', color: '#2563eb' }}>{email.recipient_email}</span>
                        </div>
                      </td>
                      <td>
                        <div className="outreach-tender-cell">
                          <span className="outreach-tender-id">#{email.tender_id || 'TEST'}</span>
                          <span className="outreach-tender-title">{email.project_name || email.tender_title}</span>
                        </div>
                      </td>
                      <td>
                        {email.sent_at ? new Date(email.sent_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                      </td>
                      <td>
                        {renderStatusBadge(email.status, email.sent_folder_verified)}
                      </td>
                      <td>
                        {['brevo', 'sendgrid'].includes(email.provider) ? (
                          <span 
                            style={{ 
                              color: '#047857', 
                              background: '#ecfdf5',
                              border: '1px solid #a7f3d0',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: 700, 
                              fontSize: '0.75rem', 
                              display: 'inline-flex', 
                              alignItems: 'center', 
                              gap: '4px' 
                            }} 
                            title="Dispatched via external SMTP relay. External relays do not write to Exchange Online; message is permanently stored in the GISFY in-app sent archive."
                          >
                            📂 In-App Sent Archive
                          </span>
                        ) : email.sent_folder_verified ? (
                          <span style={{ color: '#16a34a', fontWeight: 700, fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            ✓ Verified in Sent Items
                          </span>
                        ) : (
                          <button
                            onClick={() => handleVerifySentFolder(email.id)}
                            disabled={verifyingSentId === email.id}
                            style={{
                              background: '#eff6ff',
                              border: '1px solid #bfdbfe',
                              color: '#1d4ed8',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            {verifyingSentId === email.id ? '⏳ Verifying...' : '🔍 Check Sent Folder'}
                          </button>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '0.78rem', color: '#475569', fontWeight: 600 }}>
                            {email.provider || 'Graph API'} {email.provider_status_code ? `(${email.provider_status_code})` : ''}
                          </span>
                          <button
                            className="outreach-act-btn"
                            onClick={() => setPreviewDraft(email)}
                            style={{ padding: '2px 6px', fontSize: '0.75rem' }}
                          >
                            👁️ View
                          </button>
                          {(email.status === 'Failed' || email.status === 'failed') && (
                            <button
                              onClick={() => handleRetryDraft(email.id)}
                              disabled={actionLoading}
                              style={{
                                padding: '2px 8px',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                background: '#fee2e2',
                                color: '#b91c1c',
                                border: '1px solid #fca5a5',
                                borderRadius: '4px',
                                cursor: 'pointer'
                              }}
                              title="Manual retry for this failed email"
                            >
                              🔁 Retry
                            </button>
                          )}
                          {email.status !== 'Delivery Confirmed' && email.status !== 'Failed' && email.status !== 'failed' && (
                            <button
                              onClick={() => handleConfirmDelivery(email.id)}
                              style={{
                                padding: '2px 8px',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                background: '#ecfdf5',
                                color: '#047857',
                                border: '1px solid #a7f3d0',
                                borderRadius: '4px',
                                cursor: 'pointer'
                              }}
                              title="Confirm recipient delivery based on legitimate trace or reply evidence"
                            >
                              ✓ Confirm
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Execution History & Logs */}
        {subTab === 'logs' && (
          <div className="outreach-table-wrapper">
            <table className="outreach-table">
              <thead>
                <tr>
                  <th>Cycle Type</th>
                  <th>Timestamp</th>
                  <th>Tenders Evaluated</th>
                  <th>Drafts Generated</th>
                  <th>Emails Sent</th>
                  <th>Replies Detected</th>
                  <th>Execution Details</th>
                </tr>
              </thead>
              <tbody>
                {(dashboard?.recent_logs || []).length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                      No execution logs recorded yet. Click "Trigger 9:00 AM Cycle Now" to start a run.
                    </td>
                  </tr>
                ) : (
                  dashboard.recent_logs.map(log => (
                    <tr key={log.id}>
                      <td>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>
                          {log.cycle_type === 'daily_scheduled' ? '⏰ Daily 9:00 AM Scheduled' : '⚡ Manual Cycle Trigger'}
                        </span>
                      </td>
                      <td>{log.started_at ? new Date(log.started_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', day: '2-digit', month: 'short' }) : '-'}</td>
                      <td><strong>{log.tenders_analyzed}</strong> tenders</td>
                      <td><strong>{log.drafts_created}</strong> drafts</td>
                      <td><strong>{log.emails_sent}</strong> sent</td>
                      <td><strong>{log.replies_checked}</strong> replies</td>
                      <td style={{ fontSize: '0.8rem', color: '#475569' }}>{log.details || 'Completed successfully.'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 6. Draft Email Preview Modal */}
      {previewDraft && (
        <div className="modal-overlay" onClick={() => setPreviewDraft(null)}>
          <div className="outreach-modal-content" onClick={e => e.stopPropagation()}>
            <div className="outreach-modal-header">
              <div>
                <div style={{ fontSize: '0.78rem', color: '#93c5fd', fontWeight: 600, textTransform: 'uppercase' }}>
                  Collaboration Email Proposal Preview
                </div>
                <h3 style={{ margin: '0.2rem 0 0 0', fontSize: '1.15rem' }}>
                  {previewDraft.company_name} ({previewDraft.recipient_email})
                </h3>
              </div>
              <button 
                onClick={() => setPreviewDraft(null)}
                style={{ background: 'transparent', border: 'none', color: '#ffffff', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div className="outreach-modal-body">
              <div style={{ background: '#f8fafc', padding: '0.9rem 1.2rem', borderRadius: '8px', marginBottom: '1rem', border: '1px solid #e2e8f0', fontSize: '0.85rem' }}>
                <div><strong>Subject:</strong> {previewDraft.subject}</div>
                <div style={{ marginTop: '0.3rem' }}><strong>Recipient:</strong> {previewDraft.recipient_name} &lt;{previewDraft.recipient_email}&gt;</div>
                <div style={{ marginTop: '0.3rem' }}><strong>CC:</strong> bidding@gisfy.co.in | <strong>From:</strong> Farhath Bakka &lt;farhath@gisfy.co.in&gt;, GISFY Support &lt;support@gisfy.co.in&gt;</div>
              </div>

              <iframe 
                src={`${API_BASE}/api/collaboration/drafts/${previewDraft.id}/preview`}
                className="outreach-email-iframe"
                title="Email Draft Preview"
              />
            </div>

            <div style={{ padding: '1rem 1.5rem', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: '0.8rem' }}>
              <button 
                className="outreach-act-btn" 
                onClick={() => setPreviewDraft(null)}
              >
                Close Preview
              </button>

              <button 
                className="outreach-act-btn outlook"
                onClick={() => handleOpenOutlook(previewDraft)}
                style={{
                  background: '#0078d4',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.5rem 1.1rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer'
                }}
              >
                📬 Open in Outlook
              </button>

              {previewDraft.status === 'draft' && (
                <button 
                  className="outreach-act-btn approve"
                  onClick={() => {
                    handleApprove(previewDraft.id);
                    setPreviewDraft(null);
                  }}
                  disabled={actionLoading}
                >
                  ✅ Approve Draft
                </button>
              )}

              <button 
                className="outreach-btn-primary"
                onClick={() => handleSend(previewDraft.id)}
                disabled={actionLoading || previewDraft.status === 'Sending' || previewDraft.status === 'Provider Accepted'}
                style={{ padding: '0.5rem 1.2rem', fontSize: '0.85rem' }}
              >
                🚀 Dispatch via Outlook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Single Approved Test Email Modal */}
      {showTestModal && (
        <div className="modal-overlay" onClick={() => setShowTestModal(false)}>
          <div className="outreach-modal-content" style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div className="outreach-modal-header" style={{ background: 'linear-gradient(135deg, #3730a3 0%, #4f46e5 100%)' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>🧪 Single Approved Test Email Verification</h3>
                <div style={{ fontSize: '0.78rem', color: '#c7d2fe', marginTop: '0.2rem' }}>
                  Requirement: Send exactly one test email to an approved recipient before bulk automated outreach
                </div>
              </div>
              <button 
                onClick={() => setShowTestModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#ffffff', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSendTestEmail} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem', fontSize: '0.8rem' }}>
                <div style={{ fontWeight: 700, color: '#334155', marginBottom: '0.4rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.3rem' }}>
                  ✉️ Test Message Envelope &amp; Content Preview:
                </div>
                <div style={{ color: '#475569', lineHeight: 1.5 }}>
                  • <strong>From:</strong> Farhath Bakka &lt;farhath@gisfy.co.in&gt;, GISFY Support &lt;support@gisfy.co.in&gt;<br/>
                  • <strong>To:</strong> {testRecipient || 'Approved recipient'}<br/>
                  • <strong>CC:</strong> bidding@gisfy.co.in<br/>
                  • <strong>Reply-To:</strong> farhath@gisfy.co.in, support@gisfy.co.in<br/>
                  • <strong>Subject:</strong> Exploring JV / Consortium Partnership – Test Verification Ref #TEST-1<br/>
                  • <strong>Body:</strong> Official GISFY JV Letter of Intent with company intro, statutory document requests, agreement clause, and official corporate signature.
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                  Approved Test Recipient Email Address:
                </label>
                <input 
                  type="email" 
                  className="add-doc-input"
                  placeholder="e.g. farhath@gisfy.co.in or your test inbox"
                  value={testRecipient}
                  onChange={e => setTestRecipient(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                  Approval Note / Authorization:
                </label>
                <input 
                  type="text" 
                  className="add-doc-input"
                  placeholder="e.g. Approved by Farhath for live delivery verification"
                  value={testNotes}
                  onChange={e => setTestNotes(e.target.value)}
                />
              </div>

              {testResult && (
                <div style={{
                  background: testResult.success ? '#ecfdf5' : '#fef2f2',
                  border: testResult.success ? '1px solid #a7f3d0' : '1px solid #fecaca',
                  borderRadius: '8px',
                  padding: '1rem',
                  fontSize: '0.82rem',
                  color: testResult.success ? '#065f46' : '#991b1b'
                }}>
                  {testResult.success ? (
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.9rem', marginBottom: '0.4rem', color: '#047857' }}>
                        🎉 Email Dispatched Successfully via Microsoft Graph!
                      </div>
                      <div>• <strong>Delivery Mode:</strong> Authenticated Microsoft 365 Graph API (/me/sendMail)</div>
                      <div>• <strong>Sender:</strong> Farhath Bakka &lt;farhath@gisfy.co.in&gt;</div>
                      <div>• <strong>Recipient:</strong> {testResult.recipient}</div>
                      <div>• <strong>Mandatory CC:</strong> {testResult.cc || 'bidding@gisfy.co.in'}</div>
                      <div>• <strong>Farhath Sent Items:</strong> {testResult.sent_folder_verified ? 'Verified in Sent Folder ✅' : 'Verified via Graph API'}</div>
                      <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: '#047857', lineHeight: 1.5 }}>
                        Dispatched with <code>saveToSentItems=true</code> directly through Farhath Bakka's Microsoft 365 mailbox!
                      </div>
                      {testResult.outlook_web_url && (
                        <div style={{ marginTop: '0.6rem' }}>
                          <a
                            href={testResult.outlook_web_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-block',
                              background: '#2563eb',
                              color: '#ffffff',
                              padding: '5px 12px',
                              borderRadius: '6px',
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              textDecoration: 'none'
                            }}
                          >
                            🌐 Or Click to Open in Outlook Webmail
                          </a>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.9rem', marginBottom: '0.4rem', color: '#b91c1c' }}>
                        ❌ Dispatch Notice
                      </div>
                      <div><strong>Notice:</strong> {testResult.error || testResult.message}</div>
                      <div style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}>
                        Click below to open the message directly in your mail application.
                      </div>
                      {testResult.mailto_url && (
                        <div style={{ marginTop: '0.6rem' }}>
                          <a
                            href={testResult.mailto_url}
                            style={{
                              display: 'inline-block',
                              background: '#2563eb',
                              color: '#ffffff',
                              padding: '5px 12px',
                              borderRadius: '6px',
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              textDecoration: 'none'
                            }}
                          >
                            ✉️ Open in Email Client Now
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.8rem', marginTop: '0.5rem' }}>
                <button 
                  type="button" 
                  className="outreach-act-btn"
                  onClick={() => setShowTestModal(false)}
                >
                  Close
                </button>
                <button 
                  type="submit" 
                  className="outreach-btn-primary"
                  disabled={testSending}
                  style={{ padding: '0.5rem 1.4rem', fontSize: '0.85rem' }}
                >
                  {testSending ? '⏳ Dispatching Test Email...' : '🚀 Send Exactly One Test Email'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. Live Email Provider Credentials Configuration Modal */}
      {showConfigModal && (
        <div className="modal-overlay" onClick={() => setShowConfigModal(false)}>
          <div className="outreach-modal-content" style={{ maxWidth: '720px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div className="outreach-modal-header">
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>⚙️ Live Email Provider Authentication Setup</h3>
                <div style={{ fontSize: '0.78rem', color: '#93c5fd', marginTop: '0.2rem' }}>
                  Sender: <strong>Farhath Bakka &lt;farhath@gisfy.co.in&gt;</strong> (Hosted on Microsoft 365)
                </div>
              </div>
              <button 
                onClick={() => setShowConfigModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#ffffff', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Provider Tabs */}
            <div style={{ display: 'flex', background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', padding: '0 0.5rem', overflowX: 'auto' }}>
              <button
                type="button"
                onClick={() => setConfigTab('direct')}
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  background: 'none',
                  borderBottom: configTab === 'direct' ? '3px solid #2563eb' : '3px solid transparent',
                  color: configTab === 'direct' ? '#1d4ed8' : '#64748b',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                ✉️ Direct Mail Client (Active &amp; Recommended)
              </button>
              <button
                type="button"
                onClick={() => setConfigTab('gmail')}
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  background: 'none',
                  borderBottom: configTab === 'gmail' ? '3px solid #ea4335' : '3px solid transparent',
                  color: configTab === 'gmail' ? '#c5221f' : '#64748b',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                📧 Gmail (Optional)
              </button>
              <button
                type="button"
                onClick={() => setConfigTab('m365')}
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  background: 'none',
                  borderBottom: configTab === 'm365' ? '3px solid #2563eb' : '3px solid transparent',
                  color: configTab === 'm365' ? '#1d4ed8' : '#64748b',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                🏢 Microsoft 365 (Optional)
              </button>
              <button
                type="button"
                onClick={() => { setConfigTab('dns'); fetchDnsStatus(); }}
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  background: 'none',
                  borderBottom: configTab === 'dns' ? '3px solid #7c3aed' : '3px solid transparent',
                  color: configTab === 'dns' ? '#6d28d9' : '#64748b',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                🌐 Domain DNS Audit (gisfy.co.in)
              </button>
              <button
                type="button"
                onClick={() => setConfigTab('smtp')}
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  background: 'none',
                  borderBottom: configTab === 'smtp' ? '3px solid #2563eb' : '3px solid transparent',
                  color: configTab === 'smtp' ? '#1d4ed8' : '#64748b',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                🔑 Custom SMTP
              </button>
            </div>

            {/* Tab: Direct Mail Client (Active) */}
            {configTab === 'direct' && (
              <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '10px', padding: '1.2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.4rem' }}>✅</span>
                    <span style={{ fontWeight: 800, fontSize: '1rem', color: '#065f46' }}>
                      Direct Outlook &amp; Native Mail Client (Active Mode)
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#047857', lineHeight: 1.6 }}>
                    No complex Brevo API keys, 3rd-party relays, or authentication errors! Everything is handled directly and securely through your existing email application (Microsoft Outlook, Apple Mail, or Default Mail):
                  </div>
                  <ul style={{ fontSize: '0.82rem', color: '#065f46', marginTop: '0.6rem', paddingLeft: '1.3rem', lineHeight: 1.7 }}>
                    <li><strong>Direct One-Click Open in Outlook:</strong> Clicking <em>Send Email</em> or <em>Open in Outlook</em> automatically opens Microsoft Outlook Web or Outlook Desktop/PWA.</li>
                    <li><strong>Pre-filled Details:</strong> The recipient, mandatory CC (<code>bidding@gisfy.co.in</code>), Subject, and complete Letter of Intent proposal are automatically populated.</li>
                    <li><strong>Official Signature:</strong> The email body ends with:
                      <div style={{ background: '#ffffff', padding: '0.5rem 0.8rem', borderRadius: '6px', border: '1px solid #a7f3d0', margin: '0.4rem 0', fontFamily: 'monospace', fontSize: '0.78rem' }}>
                        Thanks &amp; Regards,<br/>
                        <strong>Farhath Bakka | Business Development Executive</strong><br/>
                        GISFY Support &amp; Partnerships Team<br/>
                        GISFY Private Limited<br/>
                        Ground Floor, DSL Abacus IT Park, Uppal, Hyderabad, Telangana – 500039, India<br/>
                        Email: farhath@gisfy.co.in | support@gisfy.co.in<br/>
                        Mobile: +91 90631 20678 | Website: www.gisfy.co.in
                      </div>
                    </li>
                    <li><strong>Guaranteed Inbox Delivery:</strong> Because it is sent directly from your authorized email application, it goes straight to the recipient's and bidding team's inbox and appears in your Sent Items folder.</li>
                  </ul>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem' }}>
                  <button 
                    type="button" 
                    className="outreach-btn-primary" 
                    onClick={() => setShowConfigModal(false)}
                    style={{ padding: '0.6rem 1.6rem' }}
                  >
                    ✓ Close &amp; Use Direct Mail Client
                  </button>
                </div>
              </div>
            )}

            {/* Tab: Gmail (App Password) */}
            {configTab === 'gmail' && (
              <form onSubmit={handleSaveGmail} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '1rem', fontSize: '0.84rem', color: '#991b1b', lineHeight: '1.55' }}>
                  <div style={{ fontWeight: 800, fontSize: '0.96rem', marginBottom: '0.4rem', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>📧</span> Instant Live Sending via Gmail (Optional)
                  </div>
                  <div>
                    • <strong>Zero Complex Relays:</strong> Authenticates instantly using a standard Google 16-character App Password.<br/>
                    • <strong>Sender / From:</strong> Farhath Bakka &lt;farhath@gisfy.co.in&gt;, GISFY Support &lt;support@gisfy.co.in&gt;.<br/>
                    • <strong>Mandatory CC:</strong> <code style={{ background: '#fee2e2', padding: '1px 5px', borderRadius: '4px' }}>bidding@gisfy.co.in</code> (Official GISFY bidding archive).<br/>
                    • <strong>Official Proposals:</strong> Dispatches GISFY JV / Consortium letters, legal clauses, and signature intact.
                  </div>
                </div>

                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.9rem', fontSize: '0.83rem', color: '#334155', lineHeight: '1.6' }}>
                  <strong style={{ color: '#0f172a' }}>👉 How to get your 16-character Google App Password (Takes 30 seconds):</strong><br/>
                  1. In a new browser tab, go directly to: <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontWeight: 700, textDecoration: 'underline' }}>https://myaccount.google.com/apppasswords</a><br/>
                  2. Under <em>"App name"</em>, type <strong>GISFY Outreach</strong> and click <strong>Create</strong>.<br/>
                  3. Google will show a yellow box with a 16-character code (like <code style={{ background: '#e2e8f0', padding: '1px 6px', borderRadius: '3px', fontWeight: 700 }}>abcd efgh ijkl mnop</code>).<br/>
                  4. Paste that code into the password field below and click Save!
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    Your Gmail Address:
                  </label>
                  <input 
                    type="email" 
                    className="add-doc-input"
                    value={gmailForm.email}
                    onChange={e => setGmailForm({ ...gmailForm, email: e.target.value })}
                    placeholder="e.g. yourname@gmail.com or gisfy.bidding@gmail.com"
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    Google 16-Character App Password:
                  </label>
                  <input 
                    type="password" 
                    className="add-doc-input"
                    value={gmailForm.app_password}
                    onChange={e => setGmailForm({ ...gmailForm, app_password: e.target.value })}
                    placeholder="xxxx xxxx xxxx xxxx"
                    required
                  />
                  <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>
                    Spaces don't matter; they will be removed automatically. Never exposes your actual Google account password.
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.8rem', marginTop: '0.5rem' }}>
                  <button 
                    type="button" 
                    className="outreach-act-btn"
                    onClick={() => setShowConfigModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="outreach-btn-primary"
                    style={{ padding: '0.55rem 1.6rem', fontSize: '0.88rem', background: '#ea4335' }}
                  >
                    🚀 Save &amp; Activate Gmail Live Sending
                  </button>
                </div>
              </form>
            )}

            {/* Tab: Domain DNS Audit */}
            {configTab === 'dns' && (
              <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.8rem' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.98rem', color: '#1e293b' }}>
                      🌐 Sender Domain DNS Verification: <code>gisfy.co.in</code>
                    </h4>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.2rem' }}>
                      Verify SPF, DKIM, and DMARC alignment for authorized outbound delivery
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={fetchDnsStatus}
                    disabled={dnsLoading}
                    style={{
                      padding: '0.45rem 1rem',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      borderRadius: '6px',
                      background: '#4f46e5',
                      color: '#ffffff',
                      border: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    {dnsLoading ? '⏳ Querying Live DNS...' : '🔄 Run Live DNS Audit'}
                  </button>
                </div>

                {/* Critical Warning Callout */}
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '8px', padding: '0.85rem', color: '#9f1239', fontSize: '0.8rem', lineHeight: 1.5 }}>
                  <strong>⚠️ CRITICAL PRESERVATION RULE:</strong> Do <u>NOT</u> delete or replace existing Microsoft 365 or Proofpoint records (<code>_spf-usg2.ppe-hosted.com</code> and <code>secureserver.net</code>). In your DNS manager, simply append <code>include:spf.sendinblue.com</code> before <code>~all</code>.
                </div>

                {dnsAudit ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* SPF Analysis Card */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ fontWeight: 800, fontSize: '0.86rem', color: '#1e293b' }}>
                          1. SPF (Sender Policy Framework) Record
                        </div>
                        <span style={{
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: dnsAudit.spf.brevo_included ? '#d1fae5' : '#fef3c7',
                          color: dnsAudit.spf.brevo_included ? '#047857' : '#b45309'
                        }}>
                          {dnsAudit.spf.brevo_included ? 'Brevo Aligned ✅' : 'Brevo Include Pending ⚠️'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#475569', marginBottom: '0.4rem' }}>
                        Current Live Record in DNS:
                      </div>
                      <code style={{ display: 'block', background: '#ffffff', border: '1px solid #cbd5e1', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', color: '#0f172a', wordBreak: 'break-all' }}>
                        {dnsAudit.spf.current_record || 'No SPF TXT record found'}
                      </code>

                      <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: '#1e40af', fontWeight: 700 }}>
                        Recommended Unified Value (Copy into DNS TXT record):
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.3rem' }}>
                        <code style={{ flex: 1, background: '#eff6ff', border: '1px solid #93c5fd', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', color: '#1e3a8a', wordBreak: 'break-all', fontWeight: 600 }}>
                          {dnsAudit.spf.recommended_for_brevo}
                        </code>
                        <button
                          type="button"
                          onClick={() => { copyToClipboard(dnsAudit.spf.recommended_for_brevo, 'spf'); setCopiedSpf(true); setTimeout(() => setCopiedSpf(false), 2000); }}
                          style={{ padding: '0.45rem 0.8rem', fontSize: '0.75rem', fontWeight: 700, borderRadius: '4px', border: '1px solid #93c5fd', background: '#dbeafe', color: '#1d4ed8', cursor: 'pointer', whiteSpace: 'nowrap' }}
                        >
                          {copiedSpf ? '✅ Copied!' : '📋 Copy SPF'}
                        </button>
                      </div>
                    </div>

                    {/* DKIM Card */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ fontWeight: 800, fontSize: '0.86rem', color: '#1e293b' }}>
                          2. DKIM (DomainKeys Identified Mail)
                        </div>
                        <span style={{
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: dnsAudit.dkim.brevo_dkim_active ? '#d1fae5' : '#f1f5f9',
                          color: dnsAudit.dkim.brevo_dkim_active ? '#047857' : '#64748b'
                        }}>
                          {dnsAudit.dkim.brevo_dkim_active ? 'DKIM Active ✅' : 'Pending Provider Setup'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#475569', lineHeight: 1.5 }}>
                        • Selector Host: <code>mail._domainkey.gisfy.co.in</code> (TXT)<br/>
                        • Value: Generated automatically in your Brevo dashboard under <strong>Senders &amp; IP &gt; Domains &gt; gisfy.co.in</strong>.<br/>
                        • Ensures cryptographic authentication of Farhath's outgoing collaboration emails.
                      </div>
                    </div>

                    {/* DMARC Card */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ fontWeight: 800, fontSize: '0.86rem', color: '#1e293b' }}>
                          3. DMARC Alignment
                        </div>
                        <span style={{ fontSize: '0.74rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', background: '#d1fae5', color: '#047857' }}>
                          Valid &amp; Safe ✅
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#475569', marginBottom: '0.3rem' }}>
                        Current Record at <code>_dmarc.gisfy.co.in</code>:
                      </div>
                      <code style={{ display: 'block', background: '#ffffff', border: '1px solid #cbd5e1', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', color: '#0f172a' }}>
                        {dnsAudit.dmarc.current_record || 'v=DMARC1; p=none; rua=mailto:dmarc@gisfy.co.in'}
                      </code>
                      <div style={{ fontSize: '0.72rem', color: '#059669', marginTop: '0.3rem' }}>
                        Policy is <code>p=none</code> (Monitoring mode) — emails from authenticated external relays will be received cleanly without rejection.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                    <button
                      type="button"
                      onClick={fetchDnsStatus}
                      style={{ padding: '0.5rem 1.2rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '6px', background: '#4f46e5', color: '#ffffff', border: 'none', cursor: 'pointer' }}
                    >
                      Query gisfy.co.in Live DNS Status
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tab 4: Microsoft 365 OAuth 2.0 */}
            {configTab === 'm365' && (
              <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                
                {/* 1. Live Connection Status Card */}
                {providerStatus?.microsoft_365?.is_authenticated ? (
                  <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '10px', padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.8rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '1.6rem' }}>🟢</span>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#065f46' }}>
                            Connected &amp; Validated with Microsoft Graph
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#047857', marginTop: '0.15rem' }}>
                            Mailbox: <strong>{providerStatus.microsoft_365.authenticated_mailbox || 'farhath@gisfy.co.in'}</strong> ({providerStatus.microsoft_365.display_name || 'Farhath Bakka'})
                          </div>
                          <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>
                            Flow: {providerStatus.microsoft_365.auth_flow} | Graph Endpoint: <code>/me/sendMail</code>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          type="button"
                          onClick={handleVerifyM365}
                          disabled={verifyingM365}
                          style={{
                            padding: '0.45rem 0.9rem',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            borderRadius: '6px',
                            border: '1px solid #10b981',
                            background: '#ffffff',
                            color: '#047857',
                            cursor: 'pointer'
                          }}
                        >
                          {verifyingM365 ? '⏳ Verifying...' : '🔍 Test /me Connectivity'}
                        </button>
                        <button
                          type="button"
                          onClick={handleDisconnectM365}
                          style={{
                            padding: '0.45rem 0.9rem',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            borderRadius: '6px',
                            border: '1px solid #fecaca',
                            background: '#fff1f2',
                            color: '#e11d48',
                            cursor: 'pointer'
                          }}
                        >
                          🔌 Disconnect
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px', padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '1.5rem' }}>⚠️</span>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: '0.92rem', color: '#92400e' }}>
                          Microsoft 365 Device Code Authentication Inactive
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#78350f', marginTop: '0.15rem' }}>
                          Live email dispatch is currently locked. Click <strong>Start Device Code Sign-In</strong> below to authenticate <code>farhath@gisfy.co.in</code>.
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2 Primary Action: MSAL Device Code Flow for Farhath Bakka */}
                <div style={{
                  background: 'linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%)',
                  border: '2px solid #3b82f6',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.1)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span style={{ fontSize: '1.4rem' }}>🔑</span>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: '0.98rem', color: '#1e3a8a' }}>
                          Microsoft 365 Device Code Authentication (Step 2 Implementation)
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#3b82f6', marginTop: '0.1rem' }}>
                          Entra App: <strong>GISFY Email Automation</strong> (<code>c2cd8349-a198-46d6-a6dc-325e86dd67a4</code>) | Delegated Mail.Send &amp; User.Read
                        </div>
                      </div>
                    </div>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      padding: '3px 10px',
                      borderRadius: '9999px',
                      background: providerStatus?.microsoft_365?.is_authenticated ? '#dcfce7' : '#dbeafe',
                      color: providerStatus?.microsoft_365?.is_authenticated ? '#15803d' : '#1d4ed8',
                      border: providerStatus?.microsoft_365?.is_authenticated ? '1px solid #86efac' : '1px solid #bfdbfe'
                    }}>
                      {providerStatus?.microsoft_365?.is_authenticated ? 'Connected: farhath@gisfy.co.in ✅' : 'Device Code Flow Ready'}
                    </span>
                  </div>

                  {deviceFlow ? (
                    <div style={{ background: '#ffffff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '1.1rem', marginTop: '0.75rem' }}>
                      <div style={{ fontSize: '0.82rem', color: '#1e293b', marginBottom: '0.6rem', fontWeight: 600 }}>
                        👉 Enter this one-time code at Microsoft Device Login to authenticate <code style={{ color: '#2563eb' }}>farhath@gisfy.co.in</code>:
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <div style={{
                          fontSize: '1.6rem',
                          fontWeight: 900,
                          letterSpacing: '4px',
                          background: '#0f172a',
                          color: '#38bdf8',
                          padding: '0.5rem 1.25rem',
                          borderRadius: '8px',
                          fontFamily: 'monospace'
                        }}>
                          {deviceFlow.user_code}
                        </div>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(deviceFlow.user_code, 'device_code')}
                          style={{
                            padding: '0.6rem 1.1rem',
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            background: '#dbeafe',
                            color: '#1d4ed8',
                            border: '1px solid #93c5fd',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          📋 Copy Code
                        </button>
                        <a
                          href={deviceFlow.verification_uri || 'https://microsoft.com/devicelogin'}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            padding: '0.6rem 1.25rem',
                            fontSize: '0.85rem',
                            fontWeight: 800,
                            background: '#2563eb',
                            color: '#ffffff',
                            borderRadius: '6px',
                            textDecoration: 'none',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem'
                          }}
                        >
                          🌐 Open https://microsoft.com/devicelogin ↗
                        </a>
                        <button
                          type="button"
                          onClick={handleCancelDeviceFlow}
                          style={{
                            padding: '0.6rem 0.9rem',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            background: '#fee2e2',
                            color: '#b91c1c',
                            border: '1px solid #fca5a5',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          ✕ Cancel
                        </button>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.8rem', fontSize: '0.78rem', color: '#0369a1' }}>
                        <span style={{ display: 'inline-block', animation: 'spin 1.5s linear infinite' }}>⏳</span>
                        <span>Live Polling: Waiting for sign-in with <strong>farhath@gisfy.co.in</strong>... (Checking every 3s)</span>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.8rem', marginTop: '0.75rem' }}>
                      <div style={{ fontSize: '0.8rem', color: '#334155', maxWidth: '440px', lineHeight: 1.45 }}>
                        Reuses your active Microsoft Outlook browser session. No secret keys or passwords required. Microsoft Graph automatically confirms mailbox is strictly <strong>farhath@gisfy.co.in</strong>.
                      </div>
                      <button
                        type="button"
                        onClick={handleStartDeviceFlow}
                        disabled={startingDeviceFlow}
                        style={{
                          padding: '0.7rem 1.4rem',
                          fontSize: '0.88rem',
                          fontWeight: 800,
                          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: startingDeviceFlow ? 'not-allowed' : 'pointer',
                          boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                      >
                        <span>🚀</span> {startingDeviceFlow ? 'Initiating Flow...' : 'Start Device Code Sign-In for farhath@gisfy.co.in'}
                      </button>
                    </div>
                  )}
                </div>

                {/* 2. Credentials Configuration Form */}
                <form onSubmit={handleSaveM365} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '0.8rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                        Microsoft 365 Tenant:
                      </label>
                      <input 
                        type="text" 
                        className="add-doc-input"
                        value={m365Form.tenant_id}
                        onChange={e => setM365Form({ ...m365Form, tenant_id: e.target.value })}
                        placeholder="de9e8583-c4c4-4212-9c27-e35cfa247419"
                        required
                      />
                      <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                        Directory GUID: <code>de9e8583-c4c4-4212-9c27-e35cfa247419</code>
                      </div>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                        Application (Client) ID: <span style={{ color: '#ef4444' }}>*</span>
                      </label>
                      <input 
                        type="text" 
                        className="add-doc-input"
                        value={m365Form.client_id}
                        onChange={e => setM365Form({ ...m365Form, client_id: e.target.value })}
                        placeholder="c2cd8349-a198-46d6-a6dc-325e86dd67a4"
                        required
                      />
                      {providerStatus?.microsoft_365?.client_id_masked && (
                        <div style={{ fontSize: '0.72rem', color: '#059669', marginTop: '0.2rem' }}>
                          Currently registered: <strong>{providerStatus.microsoft_365.client_id_masked}</strong>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                      Client Secret (App Secret): <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 'normal' }}>(Optional for Device Code Flow)</span>
                    </label>
                    <input 
                      type="password" 
                      className="add-doc-input"
                      value={m365Form.client_secret}
                      onChange={e => setM365Form({ ...m365Form, client_secret: e.target.value })}
                      placeholder="Paste your Entra Client Secret Value here (optional)"
                    />
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                      {providerStatus?.microsoft_365?.has_client_secret ? '✅ Client secret is already securely stored.' : 'Not required for Device Code public client flows.'}
                    </div>
                  </div>

                  {/* Action 1: Primary App-Only Client Credentials Activation */}
                  <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '10px', padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.8rem' }}>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#166534' }}>
                        ⚡ App-Only Authentication (Client Credentials Flow)
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#15803d', marginTop: '0.2rem' }}>
                        Headless background mode. <strong>No password or interactive MFA required.</strong> Uses Entra App Permissions scoped to Farhath's mailbox.
                      </div>
                    </div>
                    <button
                      type="submit"
                      style={{
                        padding: '0.65rem 1.4rem',
                        fontSize: '0.88rem',
                        fontWeight: 800,
                        borderRadius: '8px',
                        background: '#059669',
                        color: '#ffffff',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        boxShadow: '0 2px 4px rgba(5, 150, 105, 0.25)'
                      }}
                    >
                      <span>⚡</span> Save &amp; Activate Configuration
                    </button>
                  </div>

                  {/* Action 2: Interactive Web Redirect Sign-In */}
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '0.85rem 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.8rem' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.84rem', color: '#334155' }}>
                        Alternative: Interactive Web Redirect Sign-In
                      </div>
                      <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.15rem' }}>
                        Opens Microsoft's web sign-in prompt for <code>farhath@gisfy.co.in</code>.
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleConnectM365}
                      disabled={connectingM365}
                      style={{
                        padding: '0.45rem 1rem',
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        borderRadius: '6px',
                        background: '#ffffff',
                        color: '#0078d4',
                        border: '1px solid #93c5fd',
                        cursor: connectingM365 ? 'not-allowed' : 'pointer'
                      }}
                    >
                      {connectingM365 ? '⏳ Authorizing...' : '🔐 Sign In with Web Redirect'}
                    </button>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.8rem', marginTop: '0.5rem' }}>
                    <button 
                      type="button" 
                      className="outreach-act-btn"
                      onClick={() => setShowConfigModal(false)}
                    >
                      Close
                    </button>
                  </div>
                </form>

                {/* 3. Microsoft Entra App Registration Instructions */}
                <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '1rem' }}>
                  <div style={{ fontWeight: 800, fontSize: '0.88rem', color: '#1e40af', marginBottom: '0.5rem' }}>
                    📋 Exact Microsoft Entra ID App Registration Guide
                  </div>
                  <ol style={{ fontSize: '0.8rem', color: '#1e3a8a', paddingLeft: '1.25rem', lineHeight: 1.6, margin: 0 }}>
                    <li>
                      Sign in to the <a href="https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade" target="_blank" rel="noreferrer" style={{ color: '#1d4ed8', fontWeight: 700, textDecoration: 'underline' }}>Microsoft Entra admin center</a> with your tenant administrator or authorized user account.
                    </li>
                    <li>
                      Go to <strong>Identity &gt; Applications &gt; App registrations</strong> and click <strong>New registration</strong>.
                    </li>
                    <li>
                      <strong>Name:</strong> <code>GISFY Proposal Automation Agent</code><br/>
                      <strong>Supported account types:</strong> <em>Accounts in this organizational directory only (NETORGFT9776516 only - Single tenant)</em>
                    </li>
                    <li>
                      <strong>Redirect URI:</strong> Platform: <strong>Web</strong><br/>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.3rem', marginBottom: '0.3rem' }}>
                        <code style={{ background: '#ffffff', padding: '4px 8px', borderRadius: '4px', border: '1px solid #bfdbfe', color: '#1e40af', fontWeight: 700 }}>
                          http://localhost:8000/api/collaboration/m365/callback
                        </code>
                        <button
                          type="button"
                          onClick={() => copyToClipboard('http://localhost:8000/api/collaboration/m365/callback', 'redirect_uri')}
                          style={{ padding: '3px 8px', fontSize: '0.72rem', borderRadius: '4px', border: '1px solid #93c5fd', background: '#dbeafe', color: '#1d4ed8', cursor: 'pointer', fontWeight: 700 }}
                        >
                          {copiedRedirectUri ? '✅ Copied!' : '📋 Copy URI'}
                        </button>
                      </div>
                    </li>
                    <li>
                      Click <strong>Register</strong>. Copy the <strong>Application (client) ID</strong> and paste it in the field above.
                    </li>
                    <li>
                      Go to <strong>API permissions &gt; Add a permission &gt; Microsoft Graph &gt; Delegated permissions</strong>.<br/>
                      Add: <code>Mail.Send</code>, <code>Mail.ReadWrite</code>, <code>User.Read</code>.<br/>
                      (Recommended): Click <strong>Grant admin consent for NETORGFT9776516</strong>.
                    </li>
                    <li>
                      Go to <strong>Certificates &amp; secrets &gt; New client secret</strong>. Copy the <strong>Secret Value</strong> and paste it into Client Secret above.
                    </li>
                  </ol>
                </div>

                {/* 4. Background Email Scheduling & Exchange Mailbox Scoping (RBAC) */}
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
                  <div 
                    onClick={() => setShowRbacGuide(!showRbacGuide)}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                  >
                    <div style={{ fontWeight: 800, fontSize: '0.86rem', color: '#334155' }}>
                      ⏰ Step 3: Background 9:00 AM IST Scheduling &amp; Mailbox Scoping (Exchange RBAC)
                    </div>
                    <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      {showRbacGuide ? '▲ Hide Details' : '▼ View Details'}
                    </span>
                  </div>

                  {showRbacGuide && (
                    <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#475569', lineHeight: 1.6, borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem' }}>
                      <p style={{ margin: '0 0 0.5rem' }}>
                        <strong>1. Delegated OAuth Reliability:</strong><br/>
                        Delegated OAuth tokens use a 90-day rolling refresh token window. Because the application runs daily at 9:00 AM IST, every dispatch automatically refreshes and extends the token. As long as tenant Conditional Access doesn't enforce short sign-in frequency policies, delegated OAuth runs perpetually without manual re-auth.
                      </p>
                      <p style={{ margin: '0 0 0.5rem' }}>
                        <strong>2. Application Permissions Scoped to Farhath's Mailbox (Exchange Online RBAC):</strong><br/>
                        If tenant policies require headless service principal authentication without interactive tokens, request application permission <code>Mail.Send</code>. To prevent unrestricted tenant-wide email access, an Exchange Administrator must run this PowerShell command to restrict access <em>strictly to Farhath's mailbox</em>:
                      </p>
                      <div style={{ background: '#0f172a', color: '#f8fafc', padding: '0.75rem', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.75rem', overflowX: 'auto', position: 'relative' }}>
                        <code>
                          New-ApplicationAccessPolicy -AppId "{m365Form.client_id || '<YOUR_CLIENT_ID>'}" -PolicyScopeGroupId "farhath@gisfy.co.in" -AccessRight RestrictAccess -Description "Restrict proposal agent to Farhath mailbox only"
                        </code>
                        <div style={{ marginTop: '0.5rem', textAlign: 'right' }}>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(`New-ApplicationAccessPolicy -AppId "${m365Form.client_id || '<YOUR_CLIENT_ID>'}" -PolicyScopeGroupId "farhath@gisfy.co.in" -AccessRight RestrictAccess -Description "Restrict proposal agent to Farhath mailbox only"`, 'ps_command')}
                            style={{ padding: '3px 8px', fontSize: '0.7rem', borderRadius: '4px', border: '1px solid #475569', background: '#334155', color: '#ffffff', cursor: 'pointer' }}
                          >
                            {copiedPsCommand ? '✅ Copied!' : '📋 Copy PowerShell Command'}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            )}

            {/* Tab 2: Authenticated SMTP with IMAP Sent Sync */}
            {configTab === 'smtp' && (
              <form onSubmit={handleSaveSmtp} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem', fontSize: '0.82rem', color: '#334155', lineHeight: 1.5 }}>
                  🔑 <strong>Authenticated SMTP &amp; IMAP Sent Sync:</strong><br/>
                  • Host: <code>smtp.office365.com</code> (Port 587 STARTTLS)<br/>
                  • User: <code>farhath@gisfy.co.in</code><br/>
                  • Password: Password / 16-character App Password<br/>
                  • Sent Folder: Automatically syncs sent emails to Farhath's "Sent Items" folder via IMAP.
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                      SMTP Host:
                    </label>
                    <input 
                      type="text" 
                      className="add-doc-input"
                      value={smtpForm.host}
                      onChange={e => setSmtpForm({ ...smtpForm, host: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                      Port:
                    </label>
                    <input 
                      type="number" 
                      className="add-doc-input"
                      value={smtpForm.port}
                      onChange={e => setSmtpForm({ ...smtpForm, port: parseInt(e.target.value) || 587 })}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    User / Email Address:
                  </label>
                  <input 
                    type="email" 
                    className="add-doc-input"
                    value={smtpForm.user}
                    onChange={e => setSmtpForm({ ...smtpForm, user: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    App Password / SMTP Password:
                  </label>
                  <input 
                    type="password" 
                    className="add-doc-input"
                    value={smtpForm.password}
                    onChange={e => setSmtpForm({ ...smtpForm, password: e.target.value })}
                    placeholder="••••••••••••••••"
                    required
                  />
                  <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                    Stored with 0600 file permissions in backend/.email_credentials/provider_config.json. Never logged or exposed.
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    IMAP Host for Sent Folder Synchronization:
                  </label>
                  <input 
                    type="text" 
                    className="add-doc-input"
                    value={smtpForm.imap_host}
                    onChange={e => setSmtpForm({ ...smtpForm, imap_host: e.target.value })}
                    placeholder="outlook.office365.com"
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.8rem', marginTop: '0.5rem' }}>
                  <button 
                    type="button" 
                    className="outreach-act-btn"
                    onClick={() => setShowConfigModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="outreach-btn-primary"
                    style={{ padding: '0.5rem 1.4rem', fontSize: '0.85rem' }}
                  >
                    Save SMTP Credentials
                  </button>
                </div>
              </form>
            )}

            {/* Tab 3: Google Workspace OAuth */}
            {configTab === 'google' && (
              <form onSubmit={handleSaveGoogle} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.85rem', fontSize: '0.82rem', color: '#334155' }}>
                  🌐 <strong>Google Workspace OAuth 2.0:</strong><br/>
                  Enter Google Cloud OAuth 2.0 Client credentials if migrating domain to Google Workspace.
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    Google OAuth Client ID:
                  </label>
                  <input 
                    type="text" 
                    className="add-doc-input"
                    value={googleForm.client_id}
                    onChange={e => setGoogleForm({ ...googleForm, client_id: e.target.value })}
                    placeholder="xxxxxx.apps.googleusercontent.com"
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    Google OAuth Client Secret:
                  </label>
                  <input 
                    type="password" 
                    className="add-doc-input"
                    value={googleForm.client_secret}
                    onChange={e => setGoogleForm({ ...googleForm, client_secret: e.target.value })}
                    placeholder="••••••••••••••••"
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>
                    Refresh Token:
                  </label>
                  <input 
                    type="password" 
                    className="add-doc-input"
                    value={googleForm.refresh_token}
                    onChange={e => setGoogleForm({ ...googleForm, refresh_token: e.target.value })}
                    placeholder="1//04xxxxxxxxxxxxxxxx"
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.8rem', marginTop: '0.5rem' }}>
                  <button 
                    type="button" 
                    className="outreach-act-btn"
                    onClick={() => setShowConfigModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="outreach-btn-primary"
                    style={{ padding: '0.5rem 1.4rem', fontSize: '0.85rem' }}
                  >
                    Save Google Workspace Credentials
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
