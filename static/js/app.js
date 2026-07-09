/* ==========================================================================
   VOTECHAIN CLIENT-SIDE JAVASCRIPT APPLICATION
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// Global state holding details
let currentUser = null;
let activeElectionId = null;

function initApp() {
    setupCommonListeners();
    
    // Identify current page context
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const voterElectionsList = document.getElementById('voter-elections-list');
    const adminElectionsTable = document.getElementById('admin-elections-table-body');

    if (loginForm) {
        setupLoginView(loginForm);
    } else if (registerForm) {
        setupRegisterView(registerForm);
    } else if (voterElectionsList) {
        setupVoterDashboard();
    } else if (adminElectionsTable) {
        setupAdminDashboard();
    }
}

// ==========================================
// COMMON & LAYOUT CONTROLS
// ==========================================

function setupCommonListeners() {
    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('app-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // Global Logout buttons
    const logoutBtn = document.getElementById('sidebar-logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

async function handleLogout() {
    try {
        const res = await fetch('/api/auth/logout', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            window.location.href = '/login';
        }
    } catch (err) {
        console.error("Logout failure:", err);
    }
}

// Utility to render alerts inside forms/panels
function showAlert(elementId, text, type = 'error') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.querySelector('.message-text').innerText = text;
    el.classList.remove('hidden', 'error', 'success');
    el.classList.add(type);
}

function hideAlert(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.classList.add('hidden');
}


// ==========================================
// AUTHENTICATION LOGIC (LOGIN & REGISTER)
// ==========================================

function setupLoginView(form) {
    const tabs = document.querySelectorAll('.auth-tab');
    const roleInput = document.getElementById('login-role');
    const registerPrompt = document.getElementById('voter-register-prompt');

    // Tab switcher between Voter and Admin logins
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const role = tab.getAttribute('data-role');
            roleInput.value = role;
            
            // Toggle voter registration prompt (admins don't register online)
            if (role === 'admin') {
                registerPrompt.classList.add('hidden');
            } else {
                registerPrompt.classList.remove('hidden');
            }
            hideAlert('login-error-msg');
        });
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('login-error-msg');
        
        const username = form.username.value.trim();
        const password = form.password.value.trim();
        const role = roleInput.value;

        const submitBtn = document.getElementById('btn-login-submit');
        submitBtn.disabled = true;
        submitBtn.querySelector('span').innerText = "Verifying Credentials...";

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role })
            });
            const data = await response.json();
            
            if (data.success) {
                window.location.href = '/dashboard';
            } else {
                showAlert('login-error-msg', data.message || "Invalid login credentials.");
                submitBtn.disabled = false;
                submitBtn.querySelector('span').innerText = "Sign In Securely";
            }
        } catch (err) {
            showAlert('login-error-msg', "Server network error. Please try again.");
            submitBtn.disabled = false;
            submitBtn.querySelector('span').innerText = "Sign In Securely";
        }
    });
}

function setupRegisterView(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('register-error-msg');
        hideAlert('register-success-msg');

        const full_name = form.full_name.value.trim();
        const email = form.email.value.trim();
        const username = form.username.value.trim();
        const password = form.password.value.trim();

        const submitBtn = document.getElementById('btn-register-submit');
        submitBtn.disabled = true;
        submitBtn.querySelector('span').innerText = "Generating Identity...";

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name, email, username, password })
            });
            const data = await response.json();
            
            if (data.success) {
                showAlert('register-success-msg', data.message, 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            } else {
                showAlert('register-error-msg', data.message || "Registration failed.");
                submitBtn.disabled = false;
                submitBtn.querySelector('span').innerText = "Generate Identity";
            }
        } catch (err) {
            showAlert('register-error-msg', "Server error occurred. Please try again.");
            submitBtn.disabled = false;
            submitBtn.querySelector('span').innerText = "Generate Identity";
        }
    });
}


// ==========================================
// VOTER DASHBOARD CONSOLE
// ==========================================

function setupVoterDashboard() {
    loadVoterElections();

    // Setup Verify Ledger Modal toggles
    const btnVerifyLedger = document.getElementById('nav-btn-explorer-voter');
    const modalExplorer = document.getElementById('modal-blockchain-explorer');
    const modalClose = document.getElementById('modal-close-btn');

    if (btnVerifyLedger && modalExplorer) {
        btnVerifyLedger.addEventListener('click', (e) => {
            e.preventDefault();
            modalExplorer.classList.remove('hidden');
            loadModalBlockchain();
        });
    }
    
    if (modalClose && modalExplorer) {
        modalClose.addEventListener('click', () => {
            modalExplorer.classList.add('hidden');
            document.getElementById('verification-log-container').classList.add('hidden');
        });
    }

    // Verify Chain button inside modal
    const verifyChainBtn = document.getElementById('modal-btn-verify-chain');
    if (verifyChainBtn) {
        verifyChainBtn.addEventListener('click', runLedgerIntegrityCheckVoter);
    }

    // Handle Cast Vote Form Submission
    const voteForm = document.getElementById('vote-submission-form');
    if (voteForm) {
        voteForm.addEventListener('submit', castVoterVote);
    }
}

async function loadVoterElections() {
    const listContainer = document.getElementById('voter-elections-list');
    try {
        const res = await fetch('/api/elections');
        const data = await res.json();
        
        if (data.success) {
            if (data.elections.length === 0) {
                listContainer.innerHTML = `
                    <div class="empty-state-list text-center padding-20">
                        <p class="text-sm text-gray">No ongoing elections registered.</p>
                    </div>`;
                return;
            }
            
            listContainer.innerHTML = '';
            data.elections.forEach(el => {
                const isClosed = el.status === 'closed';
                const elItem = document.createElement('div');
                elItem.className = 'election-item';
                elItem.dataset.id = el.id;
                
                elItem.innerHTML = `
                    <div class="election-item-header">
                        <span class="election-item-title">${el.title}</span>
                        <span class="election-status-badge ${el.status}">${el.status}</span>
                    </div>
                    <div class="election-item-header">
                        <span class="election-item-desc">${el.description || 'No description provided.'}</span>
                        ${el.voted ? '<span class="election-item-voted"><i class="fa-solid fa-check"></i> Voted</span>' : ''}
                    </div>
                `;
                
                elItem.addEventListener('click', () => {
                    // Remove selection styling from previous elements
                    document.querySelectorAll('.election-item').forEach(i => i.classList.remove('active-selection'));
                    elItem.classList.add('active-selection');
                    loadVoterElectionDetails(el.id);
                });
                
                listContainer.appendChild(elItem);
            });
        }
    } catch (err) {
        listContainer.innerHTML = `<p class="text-danger text-sm">Failed to retrieve elections list.</p>`;
    }
}

async function loadVoterElectionDetails(electionId) {
    activeElectionId = electionId;
    
    const panelEmpty = document.getElementById('voting-panel-empty');
    const panelActive = document.getElementById('voting-panel-active');
    const panelReceipt = document.getElementById('voting-panel-receipt');
    const candidatesGrid = document.getElementById('voting-candidates-grid');
    const voteForm = document.getElementById('vote-submission-form');
    
    panelEmpty.classList.add('hidden');
    panelActive.classList.add('hidden');
    panelReceipt.classList.add('hidden');
    hideAlert('vote-error-msg');
    
    try {
        const res = await fetch(`/api/elections/${electionId}`);
        const data = await res.json();
        
        if (data.success) {
            const el = data.election;
            
            // Check status and vote logic
            if (data.has_voted) {
                // Fetch user's vote block data for receipt
                const blockRes = await fetch('/api/blockchain');
                const blockData = await blockRes.json();
                
                let matchingBlock = null;
                if (blockData.success) {
                    // Try to locate user's block matching this election
                    // Since it's stored in votes table we can query blockchain too
                    // Let's iterate block sequence
                    blockData.chain.forEach(blk => {
                        try {
                            const parsedData = JSON.parse(blk.vote_data);
                            if (parsedData.election_id === electionId) {
                                // For basic demonstration matching, otherwise we use block_id from DB
                                matchingBlock = blk;
                            }
                        } catch(e) {}
                    });
                }
                
                // Show receipt panel
                document.getElementById('receipt-block-index').innerText = matchingBlock ? `#${matchingBlock.index}` : 'N/A';
                document.getElementById('receipt-block-hash').innerText = matchingBlock ? matchingBlock.hash : 'N/A';
                document.getElementById('receipt-timestamp').innerText = matchingBlock ? matchingBlock.timestamp : 'Just recorded';
                
                panelReceipt.classList.remove('hidden');
            } else if (el.status === 'closed') {
                // If closed and user didn't vote
                document.getElementById('voting-election-title').innerText = el.title;
                document.getElementById('voting-election-desc').innerText = el.description;
                document.querySelector('.election-badge').className = 'election-badge closed';
                document.querySelector('.election-badge').innerText = 'CLOSED';
                
                candidatesGrid.innerHTML = '<p class="padding-20 text-gray text-center full-width">This ballot protocol has closed. Voting is suspended.</p>';
                document.getElementById('btn-vote-submit').disabled = true;
                panelActive.classList.remove('hidden');
            } else {
                // Active voting screen
                document.getElementById('voting-election-title').innerText = el.title;
                document.getElementById('voting-election-desc').innerText = el.description;
                document.querySelector('.election-badge').className = 'election-badge active';
                document.querySelector('.election-badge').innerText = 'OPEN';
                document.getElementById('vote-election-id').value = el.id;
                document.getElementById('btn-vote-submit').disabled = false;
                
                candidatesGrid.innerHTML = '';
                if (data.candidates.length === 0) {
                    candidatesGrid.innerHTML = '<p class="padding-20 text-gray text-center full-width">No candidates registered in this election.</p>';
                    document.getElementById('btn-vote-submit').disabled = true;
                } else {
                    data.candidates.forEach(cand => {
                        const card = document.createElement('div');
                        card.className = 'candidate-select-card';
                        card.dataset.id = cand.id;
                        
                        // Extract initials for logo placeholder
                        const initials = cand.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                        
                        card.innerHTML = `
                            <div class="candidate-radio-wrap">
                                <div class="candidate-radio"></div>
                            </div>
                            <div class="candidate-avatar">${initials}</div>
                            <div class="candidate-details">
                                <span class="candidate-name">${cand.name}</span>
                                <span class="candidate-party">${cand.party}</span>
                                ${cand.details ? `<span class="candidate-manifesto">${cand.details}</span>` : ''}
                            </div>
                        `;
                        
                        card.addEventListener('click', () => {
                            document.querySelectorAll('.candidate-select-card').forEach(c => c.classList.remove('selected'));
                            card.classList.add('selected');
                        });
                        
                        candidatesGrid.appendChild(card);
                    });
                }
                
                panelActive.classList.remove('hidden');
            }
        }
    } catch (err) {
        console.error(err);
    }
}

async function castVoterVote(e) {
    e.preventDefault();
    hideAlert('vote-error-msg');

    const selectedCard = document.querySelector('.candidate-select-card.selected');
    if (!selectedCard) {
        showAlert('vote-error-msg', "Please select a candidate before casting your ballot.");
        return;
    }

    const candidateId = parseInt(selectedCard.dataset.id);
    const electionId = activeElectionId;
    const submitBtn = document.getElementById('btn-vote-submit');

    if (!confirm("Are you sure you want to cast your vote? This action is final and cryptographically linked.")) {
        return;
    }

    submitBtn.disabled = true;
    submitBtn.querySelector('span').innerText = "Minting block to Ledger...";

    try {
        const res = await fetch(`/api/elections/${electionId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_id: candidateId })
        });
        const data = await res.json();
        
        if (data.success) {
            // Re-render dashboard list & details
            loadVoterElections();
            loadVoterElectionDetails(electionId);
        } else {
            showAlert('vote-error-msg', data.message || "Failed to submit vote transaction.");
            submitBtn.disabled = false;
            submitBtn.querySelector('span').innerText = "Cast Secure Ballot";
        }
    } catch (err) {
        showAlert('vote-error-msg', "Server error. Could not record vote transaction.");
        submitBtn.disabled = false;
        submitBtn.querySelector('span').innerText = "Cast Secure Ballot";
    }
}

// ==========================================
// BLOCKCHAIN EXPLORER MODAL & VERIFICATION
// ==========================================

async function loadModalBlockchain() {
    const listContainer = document.getElementById('modal-blocks-list');
    listContainer.innerHTML = '<div class="spinner-container"><i class="fa-solid fa-spinner fa-spin"></i> Reading ledger...</div>';
    
    try {
        const res = await fetch('/api/blockchain');
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('modal-chain-length').innerText = data.length;
            listContainer.innerHTML = '';
            
            data.chain.forEach(blk => {
                const card = document.createElement('div');
                card.className = 'block-card valid-card';
                card.id = `modal-block-${blk.index}`;
                
                card.innerHTML = `
                    <div class="block-card-header">
                        <span class="idx">Block #${blk.index}</span>
                        <span class="date">${blk.timestamp}</span>
                    </div>
                    <div class="block-card-body">
                        <div class="block-data-field">
                            <span class="lbl">Previous Block Hash:</span>
                            <span class="val font-mono">${blk.previous_hash}</span>
                        </div>
                        <div class="block-data-field">
                            <span class="lbl">Block Hash:</span>
                            <span class="val font-mono text-highlight">${blk.hash}</span>
                        </div>
                        <div class="block-data-field">
                            <span class="lbl">Transaction Payload Data:</span>
                            <span class="val code-val">${blk.vote_data}</span>
                        </div>
                    </div>
                    <div class="block-status-tag">SECURE</div>
                `;
                listContainer.appendChild(card);
            });
        }
    } catch (err) {
        listContainer.innerHTML = '<p class="text-danger text-sm">Failed to retrieve ledger data.</p>';
    }
}

async function runLedgerIntegrityCheckVoter() {
    const logContainer = document.getElementById('verification-log-container');
    const logContent = document.getElementById('verification-diagnostic-log');
    const statusText = document.getElementById('modal-chain-status');
    
    logContainer.classList.remove('hidden');
    logContent.innerHTML = '<div class="text-blue">Initiating cryptographic block sequence check...</div>';
    
    try {
        const res = await fetch('/api/blockchain/verify');
        const data = await res.json();
        
        if (data.success) {
            const report = data.data;
            logContent.innerHTML = '';
            
            report.report.forEach(r => {
                const entry = document.createElement('div');
                entry.className = `log-entry ${r.status === 'VALID' ? 'log-success' : 'log-error'}`;
                entry.innerHTML = `[Block #${r.index}] Verification signature: ${r.status} ${r.error_msg ? ` - Error: ${r.error_msg}` : ''}`;
                logContent.appendChild(entry);
                
                // Update specific block visual status if tampered
                const blkCard = document.getElementById(`modal-block-${r.index}`);
                if (blkCard) {
                    if (r.status === 'TAMPERED') {
                        blkCard.className = 'block-card tampered-card';
                        blkCard.querySelector('.block-status-tag').innerText = 'ALTERED';
                    } else {
                        blkCard.className = 'block-card valid-card';
                        blkCard.querySelector('.block-status-tag').innerText = 'SECURE';
                    }
                }
            });

            if (report.is_valid) {
                statusText.innerText = "HEALTHY";
                statusText.className = "stat-value text-success";
                const fin = document.createElement('div');
                fin.className = "log-success font-semibold margin-top-10";
                fin.innerText = ">> INTEGRITY CONFIRMED: Chain ledger link signatures verified successfully.";
                logContent.appendChild(fin);
            } else {
                statusText.innerText = "TAMPERED";
                statusText.className = "stat-value text-danger";
                const fin = document.createElement('div');
                fin.className = "log-error font-semibold margin-top-10";
                fin.innerText = ">> WARNING: Chain linkage validation failed. Tampered block data identified!";
                logContent.appendChild(fin);
            }
        }
    } catch (err) {
        logContent.innerHTML = '<div class="log-error">Server communication exception during cryptographic verification.</div>';
    }
}


// ==========================================
// ADMINISTRATOR DASHBOARD CONTROL PANEL
// ==========================================

function setupAdminDashboard() {
    // Load initial counts and tables
    loadAdminMetrics();
    loadAdminElections();
    
    // Setup Admin Navigation View Switchers
    setupAdminNavigation();

    // Create Election Modal Handlers
    const openCreateModalBtn = document.getElementById('btn-open-create-election-modal');
    const modalCreate = document.getElementById('modal-create-election');
    const closeCreateBtn = document.getElementById('modal-close-create-election');
    const cancelCreateBtn = document.getElementById('btn-cancel-create-election');
    const formCreate = document.getElementById('form-create-election');

    if (openCreateModalBtn) {
        openCreateModalBtn.addEventListener('click', () => {
            modalCreate.classList.remove('hidden');
            hideAlert('create-election-error-msg');
            formCreate.reset();
        });
    }

    const hideCreateModal = () => modalCreate.classList.add('hidden');
    if (closeCreateBtn) closeCreateBtn.addEventListener('click', hideCreateModal);
    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', hideCreateModal);

    if (formCreate) {
        formCreate.addEventListener('submit', submitCreateElection);
    }

    // Add Candidate Modal Handlers
    const modalAddCand = document.getElementById('modal-add-candidate');
    const closeAddCandBtn = document.getElementById('modal-close-add-candidate');
    const cancelAddCandBtn = document.getElementById('btn-cancel-add-candidate');
    const formAddCand = document.getElementById('form-add-candidate');

    const hideAddCandModal = () => modalAddCand.classList.add('hidden');
    if (closeAddCandBtn) closeAddCandBtn.addEventListener('click', hideAddCandModal);
    if (cancelAddCandBtn) cancelAddCandBtn.addEventListener('click', hideAddCandModal);

    if (formAddCand) {
        formAddCand.addEventListener('submit', submitAddCandidate);
    }

    // Results / Controls Modal Close Handler
    const modalResults = document.getElementById('modal-election-results');
    const closeResultsBtn = document.getElementById('modal-close-election-results');
    if (closeResultsBtn) {
        closeResultsBtn.addEventListener('click', () => modalResults.classList.add('hidden'));
    }

    // Admin verify chain button handler
    const btnAdminVerifyChain = document.getElementById('btn-admin-verify-chain');
    if (btnAdminVerifyChain) {
        btnAdminVerifyChain.addEventListener('click', runLedgerIntegrityCheckAdmin);
    }

    // Admin Close Election handler
    const btnCloseElection = document.getElementById('btn-admin-close-election');
    if (btnCloseElection) {
        btnCloseElection.addEventListener('click', executeCloseElection);
    }
}

function setupAdminNavigation() {
    const navDashboard = document.querySelector('.sidebar-nav a[href="/admin"]');
    const navBlockchain = document.getElementById('nav-btn-blockchain');
    const navVoters = document.getElementById('nav-btn-voters');

    const viewElections = document.getElementById('view-elections');
    const viewBlockchain = document.getElementById('view-blockchain');
    const viewVoters = document.getElementById('view-voters');

    const navLinks = [navDashboard, navBlockchain, navVoters];
    const views = [viewElections, viewBlockchain, viewVoters];

    function toggleView(activeLink, activeView) {
        navLinks.forEach(l => { if (l) l.classList.remove('active'); });
        views.forEach(v => { if (v) v.classList.add('hidden'); });
        
        if (activeLink) activeLink.classList.add('active');
        if (activeView) activeView.classList.remove('hidden');
        
        // Hide diagnostic logs on route switch to clean view
        document.getElementById('admin-diagnostic-log-container').classList.add('hidden');
        hideAlert('admin-chain-alert-tamper');
        hideAlert('admin-chain-alert-valid');
    }

    if (navDashboard) {
        navDashboard.addEventListener('click', (e) => {
            e.preventDefault();
            toggleView(navDashboard, viewElections);
            loadAdminElections();
            loadAdminMetrics();
        });
    }

    if (navBlockchain) {
        navBlockchain.addEventListener('click', (e) => {
            e.preventDefault();
            toggleView(navBlockchain, viewBlockchain);
            loadAdminBlockchainExplorer();
        });
    }

    if (navVoters) {
        navVoters.addEventListener('click', (e) => {
            e.preventDefault();
            toggleView(navVoters, viewVoters);
            loadAdminVotersDirectory();
        });
    }
}

async function loadAdminMetrics() {
    try {
        const resElections = await fetch('/api/elections');
        const dataE = await resElections.json();
        
        const resVoters = await fetch('/api/admin/voters');
        const dataV = await resVoters.json();
        
        const resBlocks = await fetch('/api/blockchain');
        const dataB = await resBlocks.json();

        if (dataE.success) document.getElementById('metric-elections-count').innerText = dataE.elections.length;
        if (dataV.success) document.getElementById('metric-voters-count').innerText = dataV.voters.length;
        if (dataB.success) document.getElementById('metric-blocks-count').innerText = dataB.length;
    } catch(err) {
        console.error("Metric loads error: ", err);
    }
}

async function loadAdminElections() {
    const tableBody = document.getElementById('admin-elections-table-body');
    try {
        const res = await fetch('/api/elections');
        const data = await res.json();
        
        if (data.success) {
            if (data.elections.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-gray">No election protocols created.</td></tr>';
                return;
            }
            
            tableBody.innerHTML = '';
            data.elections.forEach(el => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${el.id}</td>
                    <td><b>${el.title}</b><br><span class="text-xs text-gray">${el.description || ''}</span></td>
                    <td><span class="badge-row ${el.status}">${el.status}</span></td>
                    <td class="text-center" id="cand-count-${el.id}">-</td>
                    <td>
                        <div class="actions-cell">
                            ${el.status === 'active' ? `
                            <button class="btn-action-row btn-add-cand" data-id="${el.id}">
                                <i class="fa-solid fa-user-plus"></i> Add Cand
                            </button>` : ''}
                            <button class="btn-action-row btn-view-results" data-id="${el.id}">
                                <i class="fa-solid fa-chart-simple"></i> Results & Status
                            </button>
                        </div>
                    </td>
                `;
                tableBody.appendChild(tr);
                
                // Fetch candidate counts asynchronously
                fetchCandidateCounts(el.id);
            });
            
            // Attach event listeners to newly generated row buttons
            setupElectionsTableButtons();
        }
    } catch (err) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Failed to load elections data from server.</td></tr>';
    }
}

async function fetchCandidateCounts(electionId) {
    try {
        const res = await fetch(`/api/elections/${electionId}`);
        const data = await res.json();
        if (data.success) {
            const el = document.getElementById(`cand-count-${electionId}`);
            if (el) el.innerText = data.candidates.length;
        }
    } catch(e) {}
}

function setupElectionsTableButtons() {
    // Add Candidate Buttons
    document.querySelectorAll('.btn-add-cand').forEach(btn => {
        btn.addEventListener('click', () => {
            const electionId = btn.getAttribute('data-id');
            document.getElementById('add-candidate-election-id').value = electionId;
            document.getElementById('modal-add-candidate').classList.remove('hidden');
            hideAlert('add-candidate-error-msg');
            document.getElementById('form-add-candidate').reset();
        });
    });

    // View Results Buttons
    document.querySelectorAll('.btn-view-results').forEach(btn => {
        btn.addEventListener('click', () => {
            const electionId = btn.getAttribute('data-id');
            openElectionResultsModal(electionId);
        });
    });
}

async function submitCreateElection(e) {
    e.preventDefault();
    hideAlert('create-election-error-msg');
    
    const title = document.getElementById('election-title-input').value.trim();
    const description = document.getElementById('election-desc-input').value.trim();

    try {
        const res = await fetch('/api/elections', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('modal-create-election').classList.add('hidden');
            loadAdminElections();
            loadAdminMetrics();
        } else {
            showAlert('create-election-error-msg', data.message || "Failed to create election.");
        }
    } catch(err) {
        showAlert('create-election-error-msg', "Server network error.");
    }
}

async function submitAddCandidate(e) {
    e.preventDefault();
    hideAlert('add-candidate-error-msg');

    const electionId = document.getElementById('add-candidate-election-id').value;
    const name = document.getElementById('candidate-name-input').value.trim();
    const party = document.getElementById('candidate-party-input').value.trim();
    const details = document.getElementById('candidate-details-input').value.trim();

    try {
        const res = await fetch(`/api/elections/${electionId}/candidates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, party, details })
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('modal-add-candidate').classList.add('hidden');
            loadAdminElections();
        } else {
            showAlert('add-candidate-error-msg', data.message || "Failed to register candidate.");
        }
    } catch (err) {
        showAlert('add-candidate-error-msg', "Server network error.");
    }
}

async function openElectionResultsModal(electionId) {
    activeElectionId = electionId;
    const modal = document.getElementById('modal-election-results');
    const votesList = document.getElementById('results-votes-list');
    
    votesList.innerHTML = '<div class="spinner-container"><i class="fa-solid fa-spinner fa-spin"></i> Retrieving ballot results...</div>';
    modal.classList.remove('hidden');

    try {
        const res = await fetch(`/api/elections/${electionId}/results`);
        const data = await res.json();
        
        if (data.success) {
            const el = data.election;
            document.getElementById('results-modal-title').innerText = el.title;
            document.getElementById('results-modal-subtitle').innerText = el.description || 'No description provided.';
            
            document.getElementById('results-detail-id').innerText = `#${el.id}`;
            document.getElementById('results-detail-status').innerText = el.status.toUpperCase();
            document.getElementById('results-detail-status').className = `val font-semibold ${el.status}`;
            
            // Build Results lists
            const totalVotes = data.results.reduce((sum, r) => sum + r.vote_count, 0);
            document.getElementById('results-detail-votes-count').innerText = totalVotes;

            // Setup download results PDF action in results header
            document.getElementById('results-export-actions').innerHTML = `
                <a href="/api/elections/${el.id}/results/pdf" class="btn-secondary" style="padding: 6px 12px; font-size: 12px;">
                    <i class="fa-solid fa-file-pdf text-danger"></i> Export PDF Report
                </a>
            `;

            // If election is closed, hide admin control card
            const controlsCard = document.getElementById('results-admin-controls-card');
            if (el.status === 'closed') {
                controlsCard.classList.add('hidden');
            } else {
                controlsCard.classList.remove('hidden');
            }

            votesList.innerHTML = '';
            if (data.results.length === 0) {
                votesList.innerHTML = '<p class="text-center text-sm text-gray padding-20">No candidates registered in this election protocol.</p>';
            } else {
                data.results.forEach(r => {
                    const pct = totalVotes > 0 ? ((r.vote_count / totalVotes) * 100).toFixed(1) : 0;
                    
                    const card = document.createElement('div');
                    card.className = 'result-bar-card';
                    card.innerHTML = `
                        <div class="result-bar-info">
                            <span>${r.name} (${r.party})</span>
                            <span>${r.vote_count} votes (${pct}%)</span>
                        </div>
                        <div class="result-bar-track">
                            <div class="result-bar-fill" style="width: ${pct}%"></div>
                        </div>
                    `;
                    votesList.appendChild(card);
                });
            }
        }
    } catch(err) {
        votesList.innerHTML = '<p class="text-danger text-center">Failed to fetch election results.</p>';
    }
}

async function executeCloseElection() {
    const electionId = activeElectionId;
    if (!electionId) return;

    if (!confirm("Are you sure you want to permanently close this election? All voter access will be revoked immediately.")) {
        return;
    }

    try {
        const res = await fetch(`/api/elections/${electionId}/close`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('modal-election-results').classList.add('hidden');
            loadAdminElections();
        } else {
            alert(data.message || "Failed to close election.");
        }
    } catch(err) {
        alert("Server error. Could not close election.");
    }
}

// Admin Blockchain View
async function loadAdminBlockchainExplorer() {
    const listContainer = document.getElementById('admin-blocks-list-container');
    listContainer.innerHTML = '<div class="spinner-container"><i class="fa-solid fa-spinner fa-spin"></i> Reading blocks...</div>';
    
    try {
        const res = await fetch('/api/blockchain');
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('metric-blocks-count').innerText = data.length;
            listContainer.innerHTML = '';
            
            data.chain.forEach(blk => {
                const card = document.createElement('div');
                card.className = 'block-card valid-card';
                card.id = `admin-block-${blk.index}`;
                
                card.innerHTML = `
                    <div class="block-card-header">
                        <span class="idx">Block #${blk.index}</span>
                        <span class="date">${blk.timestamp}</span>
                    </div>
                    <div class="block-card-body">
                        <div class="block-data-field">
                            <span class="lbl">Previous Block Hash:</span>
                            <span class="val font-mono">${blk.previous_hash}</span>
                        </div>
                        <div class="block-data-field">
                            <span class="lbl">Block Hash:</span>
                            <span class="val font-mono text-highlight">${blk.hash}</span>
                        </div>
                        <div class="block-data-field">
                            <span class="lbl">Transaction Payload Data:</span>
                            <span class="val code-val">${blk.vote_data}</span>
                        </div>
                    </div>
                    <div class="block-status-tag">VERIFIED</div>
                `;
                listContainer.appendChild(card);
            });
        }
    } catch (err) {
        listContainer.innerHTML = '<p class="text-danger text-sm">Failed to retrieve ledger data.</p>';
    }
}

async function runLedgerIntegrityCheckAdmin() {
    const logContainer = document.getElementById('admin-diagnostic-log-container');
    const logContent = document.getElementById('admin-diagnostic-log-content');
    const metricStatus = document.getElementById('metric-ledger-health');
    
    hideAlert('admin-chain-alert-tamper');
    hideAlert('admin-chain-alert-valid');
    
    logContainer.classList.remove('hidden');
    logContent.innerHTML = '<div class="text-blue">Initiating cryptographic block sequence check...</div>';
    
    try {
        const res = await fetch('/api/blockchain/verify');
        const data = await res.json();
        
        if (data.success) {
            const report = data.data;
            logContent.innerHTML = '';
            
            report.report.forEach(r => {
                const entry = document.createElement('div');
                entry.className = `log-entry ${r.status === 'VALID' ? 'log-success' : 'log-error'}`;
                entry.innerHTML = `[Block #${r.index}] Verification signature: ${r.status} ${r.error_msg ? ` - Error: ${r.error_msg}` : ''}`;
                logContent.appendChild(entry);
                
                // Update specific block visual status if tampered
                const blkCard = document.getElementById(`admin-block-${r.index}`);
                if (blkCard) {
                    if (r.status === 'TAMPERED') {
                        blkCard.className = 'block-card tampered-card';
                        blkCard.querySelector('.block-status-tag').innerText = 'TAMPERED';
                    } else {
                        blkCard.className = 'block-card valid-card';
                        blkCard.querySelector('.block-status-tag').innerText = 'VERIFIED';
                    }
                }
            });

            if (report.is_valid) {
                metricStatus.innerText = "HEALTHY";
                metricStatus.className = "metric-value text-success";
                showAlert('admin-chain-alert-valid', "LEDGER INTEGRITY VERIFIED: All blocks are signed, validly chained, and secure.", 'success');
                
                const fin = document.createElement('div');
                fin.className = "log-success font-semibold margin-top-10";
                fin.innerText = ">> INTEGRITY CONFIRMED: Chain ledger link signatures verified successfully.";
                logContent.appendChild(fin);
            } else {
                metricStatus.innerText = "TAMPERED";
                metricStatus.className = "metric-value text-danger";
                showAlert('admin-chain-alert-tamper', "TAMPER DETECTION WARNING: Crypto signature mismatch detected in block sequence.", 'error');
                
                const fin = document.createElement('div');
                fin.className = "log-error font-semibold margin-top-10";
                fin.innerText = ">> WARNING: Chain linkage validation failed. Tampered block data identified!";
                logContent.appendChild(fin);
            }
        }
    } catch (err) {
        logContent.innerHTML = '<div class="log-error">Server communication exception during cryptographic verification.</div>';
    }
}

// Admin Voters view
async function loadAdminVotersDirectory() {
    const tableBody = document.getElementById('admin-voters-table-body');
    tableBody.innerHTML = '<tr><td colspan="5" class="table-loading"><i class="fa-solid fa-spinner fa-spin"></i> Retrieving voter list...</td></tr>';
    
    try {
        const res = await fetch('/api/admin/voters');
        const data = await res.json();
        
        if (data.success) {
            if (data.voters.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-gray">No voters registered in the system database.</td></tr>';
                return;
            }
            
            tableBody.innerHTML = '';
            data.voters.forEach(v => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${v.id}</td>
                    <td><b>${v.full_name}</b></td>
                    <td>${v.username}</td>
                    <td>${v.email}</td>
                    <td>${v.created_at}</td>
                `;
                tableBody.appendChild(tr);
            });
        }
    } catch(err) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Failed to load voters list.</td></tr>';
    }
}
