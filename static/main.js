const chainContainer = document.getElementById("blockchain-visualizer");
const statusElement = document.getElementById("status");
const consensusModeElement = document.getElementById("consensus-mode");
const bftControlsElement = document.getElementById("bft-controls");
const bftStatusElement = document.getElementById("bft-status");
const bftProposeBtn = document.getElementById("bft-propose-btn");
const bftVoteBtn = document.getElementById("bft-vote-btn");
const bftCommitBtn = document.getElementById("bft-commit-btn");

let currentValidators = []; // To store validator list

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

        // Show/hide BFT controls based on mode
        if (data.consensus_mode === 'bft') {
            bftControlsElement.style.display = 'block';
            resetBftControls(); // Reset buttons on load
            fetchValidators(); // Fetch validator list for display
        } else {
            bftControlsElement.style.display = 'none';
        }

        updateStatus("Blockchain loaded successfully.");

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

// Load the chain initially when the page loads
document.addEventListener('DOMContentLoaded', loadChain);
