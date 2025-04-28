const chainContainer = document.getElementById("blockchain-visualizer");
const statusElement = document.getElementById("status");
const consensusModeElement = document.getElementById("consensus-mode");
const bftControlsElement = document.getElementById("bft-controls");
const bftStatusElement = document.getElementById("bft-status");
const bftProposeBtn = document.getElementById("bft-propose-btn");
const bftVoteBtn = document.getElementById("bft-vote-btn");
const bftCommitBtn = document.getElementById("bft-commit-btn");
const posControlsElement = document.getElementById("pos-controls");
const stakesListElement = document.getElementById("stakes-list");
const mempoolListElement = document.getElementById("mempool-list");

let currentValidators = []; // To store validator list
let selectedValidator = null;

function updateStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.style.color = isError ? 'red' : 'green';
}

async function loadChain() {
    try {
        const response = await fetch("/chain");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        chainContainer.innerHTML = ""; // Clear previous blocks
        consensusModeElement.textContent = data.consensus_mode || 'N/A'; // Update consensus mode display

        // Show/hide consensus controls based on mode
        if (data.consensus_mode === 'bft') {
            bftControlsElement.style.display = 'block';
            posControlsElement.style.display = 'none';
            resetBftControls();
            fetchValidators();
        } else if (data.consensus_mode === 'pos') {
            bftControlsElement.style.display = 'none';
            posControlsElement.style.display = 'block';
            loadStakes();
        } else {
            bftControlsElement.style.display = 'none';
            posControlsElement.style.display = 'none';
        }

        if (!data.chain || data.chain.length === 0) {
            chainContainer.innerHTML = "<p>No blocks in the chain yet.</p>";
            return;
        }

        data.chain.forEach((block) => {
            const blockElement = document.createElement("div");
            blockElement.classList.add("block");

            // Add consensus-specific class and data attribute
            const consensusMethod = block.consensus_method || 'unknown';
            blockElement.classList.add(`block-${consensusMethod}`);
            blockElement.setAttribute('data-consensus-method', consensusMethod);

            // Basic block info
            let blockHTML = `
                <h4>Block ${block.index}</h4>
                <div class="block-details">
                    <p><strong>Timestamp:</strong> ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                    <p><strong>Hash:</strong> <small>${block.hash}</small></p>
                    <p><strong>Prev Hash:</strong> <small>${block.previous_hash}</small></p>
            `;

            // Add Nonce for PoW blocks
            if (block.nonce !== undefined) {
                 blockHTML += `<p><strong>Nonce:</strong> ${block.nonce}</p>`;
            }
            // Add Validator/Proposer for BFT blocks (assuming your BFT adds this)
            if (block.validator !== undefined) {
                 blockHTML += `<p><strong>Validator:</strong> ${block.validator}</p>`;
            }
            if (block.proposer !== undefined) { // Added proposer based on your bft.py likely structure
                 blockHTML += `<p><strong>Proposer:</strong> ${block.proposer}</p>`;
            }

            // Transactions
            blockHTML += `<strong>Transactions:</strong>`;
            if (block.transactions && block.transactions.length > 0) {
                 blockHTML += `<pre>${JSON.stringify(block.transactions, null, 2)}</pre>`;
            } else {
                 blockHTML += `<p><small>No transactions in this block.</small></p>`;
            }

            blockHTML += `</div>`; // Close block-details

            // Add connector line (except for the last block - CSS handles hiding)
            blockHTML += `<div class="connector"></div>`;

            blockElement.innerHTML = blockHTML;
            chainContainer.appendChild(blockElement);
        });

        updateStatus("Blockchain loaded successfully.");

        // Also load the mempool
        loadMempool();

    } catch (error) {
        console.error("Failed to load chain:", error);
        chainContainer.innerHTML = "<p style='color: red;'>Failed to load blockchain data.</p>";
        updateStatus("Error loading blockchain: " + error.message, true);
    }
}

// Function to fetch validator list (call when switching to BFT)
async function fetchValidators() {
    try {
        const response = await fetch("/bft/validators");
        if (!response.ok) throw new Error("Failed to fetch validators");
        const data = await response.json();
        currentValidators = data.validators || [];
    } catch (error) {
        console.error("Error fetching validators:", error);
        updateStatus("Error fetching validator list.", true);
        currentValidators = [];
    }
}

// Reset BFT button states
function resetBftControls() {
    bftProposeBtn.disabled = false;
    bftVoteBtn.disabled = true;
    bftCommitBtn.disabled = true;
    bftStatusElement.innerHTML = "Waiting for BFT actions...";
}

// --- BFT Step Functions ---

async function bftPropose() {
    updateStatus("Requesting block proposal...");
    bftProposeBtn.disabled = true; // Disable while processing
    bftStatusElement.innerHTML = "Requesting proposal...";
    try {
        const response = await fetch("/bft/propose", { method: "POST" });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || data.message || "Proposal failed");

        updateStatus(data.message);
        if (data.proposal) {
            bftStatusElement.innerHTML = `Proposal Received:<br><strong>Proposer:</strong> ${data.proposal.proposer}<br><strong>Block Index:</strong> ${data.proposal.block_index}<br><strong>Block Hash:</strong> <small>${data.proposal.block_hash}</small>`;
            bftVoteBtn.disabled = false; // Enable voting
        } else {
            // Handle case like 'No pending transactions'
            bftStatusElement.innerHTML = data.message;
             bftProposeBtn.disabled = false; // Re-enable propose button
        }

    } catch (error) {
        console.error("BFT Propose failed:", error);
        updateStatus(`Proposal Error: ${error.message}`, true);
        bftStatusElement.innerHTML = `<span style="color: red;">Proposal Error: ${error.message}</span>`;
        bftProposeBtn.disabled = false; // Re-enable on error
    }
}

async function bftVote() {
    updateStatus("Simulating votes...");
    bftVoteBtn.disabled = true; // Disable while processing
    bftStatusElement.innerHTML += "<br>Simulating votes...";

    try {
        const response = await fetch("/bft/vote", { method: "POST" });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Vote simulation failed");

        updateStatus("Votes received.");

        let votesHTML = "<br><strong>Votes:</strong><br>";
        let yesVotes = 0;
        for (const validator of currentValidators) { // Use fetched list
            const vote = data.votes[validator] || 'missing'; // Handle if validator missing in response
            const voteClass = vote === 'yes' ? 'vote-yes' : 'vote-no';
            votesHTML += `<div class="validator-vote ${voteClass}">${validator}: ${vote.toUpperCase()}</div>`;
            if (vote === 'yes') yesVotes++;
        }
        votesHTML += `<br>Total Yes: ${yesVotes}/${currentValidators.length} (Threshold: ${data.required_threshold})`;
        bftStatusElement.innerHTML += votesHTML;

        bftCommitBtn.disabled = false; // Enable commit attempt

    } catch (error) {
        console.error("BFT Vote failed:", error);
        updateStatus(`Voting Error: ${error.message}`, true);
        bftStatusElement.innerHTML += `<br><span style="color: red;">Voting Error: ${error.message}</span>`;
        // Decide if we should re-enable voting or stop
        // For now, let's keep it disabled to avoid repeated errors on same proposal
    }
}

async function bftCommit() {
    updateStatus("Attempting to commit block...");
    bftCommitBtn.disabled = true; // Disable while processing
    bftStatusElement.innerHTML += "<br>Attempting commit...";

    try {
        const response = await fetch("/bft/commit", { method: "POST" });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Commit failed");

        updateStatus(data.message);
        bftStatusElement.innerHTML += `<br><strong>${data.message}</strong>`;
        if (data.block) {
            loadChain(); // Success! Reload the chain
            loadMempool(); // Refresh mempool (should be empty)
        } else {
            // Consensus failed, just update status
            resetBftControls(); // Allow trying again (propose)
        }

    } catch (error) {
        console.error("BFT Commit failed:", error);
        updateStatus(`Commit Error: ${error.message}`, true);
        bftStatusElement.innerHTML += `<br><span style="color: red;">Commit Error: ${error.message}</span>`;
        resetBftControls(); // Allow trying again on error
    }
}

async function createTransaction() {
    const sender = document.getElementById("sender").value;
    const recipient = document.getElementById("recipient").value;
    const amount = parseFloat(document.getElementById("amount").value);

    if (!sender || !recipient || isNaN(amount)) {
        updateStatus("Please fill in all transaction fields correctly.", true);
        return;
    }

    try {
        const response = await fetch("/transactions/new", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sender, recipient, amount })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        updateStatus(data.message);
        // Clear input fields after successful submission
        document.getElementById("sender").value = '';
        document.getElementById("recipient").value = '';
        document.getElementById("amount").value = '';

        // Refresh the mempool view
        loadMempool();

    } catch (error) {
        console.error("Failed to create transaction:", error);
        updateStatus("Error creating transaction: " + error.message, true);
    }
}

async function mineBlock() {
    updateStatus("Mining block... (This might take a moment)");
    try {
        // Add a dummy query param to easily identify the miner if needed later
        const response = await fetch("/mine?miner=web_ui"); 
        const data = await response.json();
         if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        updateStatus(data.message + (data.block ? ` Block Index: ${data.block.index}` : ''));
        loadChain(); // Refresh the chain view
        loadMempool(); // Refresh the mempool view (should be empty now)
    } catch (error) {
        console.error("Mining failed:", error);
        updateStatus("Mining failed: " + error.message, true);
    }
}

async function bftNextRound() {
    updateStatus("Running BFT consensus round...");
    try {
        const response = await fetch("/bft/next_round");
        const data = await response.json();
         if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        updateStatus(data.message + (data.block ? ` Block Index: ${data.block.index}` : ''));
        loadChain(); // Refresh the chain view
    } catch (error) {
        console.error("BFT round failed:", error);
        updateStatus("BFT round failed: " + error.message, true);
    }
}

async function switchConsensus(mode) {
    updateStatus(`Switching consensus mode to ${mode}...`);
    try {
        const response = await fetch("/consensus_mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: mode })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        updateStatus(data.message);
        // Explicitly call loadChain AFTER status update
        // loadChain will handle showing/hiding BFT controls
        loadChain(); 
    } catch (error) {
        console.error(`Failed to switch to ${mode}:`, error);
        updateStatus(`Error switching mode: ${error.message}`, true);
    }
}

function switchToPoW() {
    switchConsensus('pow');
}

function switchToBFT() {
    switchConsensus('bft');
}

// --- PoS Functions ---

async function loadStakes() {
    try {
        const response = await fetch("/pos/stakes");
        if (!response.ok) throw new Error("Failed to fetch stakes");
        const data = await response.json();

        let stakesHTML = `<p><strong>Minimum Stake Required:</strong> ${data.min_stake}</p>`;
        stakesHTML += '<div class="stakes-grid">';
        
        for (const [validator, stake] of Object.entries(data.stakes)) {
            const isSelected = validator === selectedValidator;
            stakesHTML += `
                <div class="validator-stake ${isSelected ? 'selected' : ''}" 
                     onclick="selectValidator('${validator}')">
                    <strong>${validator}</strong><br>
                    Stake: ${stake}
                </div>`;
        }
        stakesHTML += '</div>';
        stakesListElement.innerHTML = stakesHTML;
    } catch (error) {
        console.error("Error loading stakes:", error);
        updateStatus("Failed to load stakes: " + error.message, true);
    }
}

function selectValidator(validator) {
    selectedValidator = validator;
    loadStakes(); // Refresh display to show selection
}

async function addStake() {
    const validator = document.getElementById("stake-validator").value;
    const amount = parseFloat(document.getElementById("stake-amount").value);

    if (!validator || isNaN(amount) || amount <= 0) {
        updateStatus("Please enter valid validator address and amount", true);
        return;
    }

    try {
        const response = await fetch("/pos/stake", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ validator, amount })
        });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Failed to add stake");

        updateStatus(data.message);
        document.getElementById("stake-validator").value = "";
        document.getElementById("stake-amount").value = "";
        loadStakes();
    } catch (error) {
        console.error("Error adding stake:", error);
        updateStatus("Failed to add stake: " + error.message, true);
    }
}

async function removeStake() {
    const validator = document.getElementById("stake-validator").value;
    const amount = parseFloat(document.getElementById("stake-amount").value);

    if (!validator || isNaN(amount) || amount <= 0) {
        updateStatus("Please enter valid validator address and amount", true);
        return;
    }

    try {
        const response = await fetch("/pos/unstake", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ validator, amount })
        });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Failed to remove stake");

        updateStatus(data.message);
        document.getElementById("stake-validator").value = "";
        document.getElementById("stake-amount").value = "";
        loadStakes();
    } catch (error) {
        console.error("Error removing stake:", error);
        updateStatus("Failed to remove stake: " + error.message, true);
    }
}

async function createPosBlock(validator = null) {
    try {
        const response = await fetch("/pos/create_block", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ validator })
        });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Failed to create block");

        updateStatus(data.message);
        loadChain(); // Refresh chain
        loadMempool(); // Refresh mempool
    } catch (error) {
        console.error("Error creating PoS block:", error);
        updateStatus("Failed to create block: " + error.message, true);
    }
}

function createPosBlockWithValidator() {
    if (!selectedValidator) {
        updateStatus("Please select a validator first", true);
        return;
    }
    createPosBlock(selectedValidator);
}

async function simulatePosMalice() {
    if (!selectedValidator) {
        updateStatus("Please select a validator to simulate malice for", true);
        return;
    }

    updateStatus(`Simulating malice for validator ${selectedValidator}...`);
    try {
        const response = await fetch("/pos/simulate_malice", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ validator: selectedValidator })
        });
        const data = await response.json();

        if (!response.ok) throw new Error(data.error || "Failed to simulate malice");

        updateStatus(data.message); // Display success/slashing message
        loadStakes(); // Refresh the stakes list to show reduced stake
        selectedValidator = null; // Deselect validator after action

    } catch (error) {
        console.error("Error simulating PoS malice:", error);
        updateStatus("Failed to simulate malice: " + error.message, true);
    }
}

// --- Consensus Mode Switching ---

function switchToPoS() {
    switchConsensus('pos');
}

// Load the chain initially when the page loads
document.addEventListener('DOMContentLoaded', loadChain);

async function loadMempool() {
    try {
        const response = await fetch("/mempool");
        if (!response.ok) throw new Error("Failed to fetch mempool");
        const data = await response.json();

        mempoolListElement.innerHTML = ""; // Clear previous list
        if (data.transactions && data.transactions.length > 0) {
            data.transactions.forEach(tx => {
                const txElement = document.createElement("div");
                txElement.classList.add("mempool-tx");
                // Basic display, could be more detailed
                txElement.textContent = `From: ${tx.sender}, To: ${tx.recipient}, Amount: ${tx.amount}`;
                mempoolListElement.appendChild(txElement);
            });
        } else {
            mempoolListElement.innerHTML = "<p><small>No pending transactions.</small></p>";
        }
    } catch (error) {
        console.error("Error loading mempool:", error);
        mempoolListElement.innerHTML = `<p><small style="color: red;">Error loading mempool: ${error.message}</small></p>`;
    }
}
