async function loadChain() {
  const response = await fetch("/chain");
  const data = await response.json();
  document.getElementById("chainData").innerHTML = JSON.stringify(data, null, 2);
}

async function createTransaction() {
  const sender = document.getElementById("sender").value;
  const recipient = document.getElementById("recipient").value;
  const amount = parseFloat(document.getElementById("amount").value);

  const response = await fetch("/transactions/new", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender, recipient, amount })
  });
  const data = await response.json();
  alert(data.message);
}

async function mineBlock() {
  const response = await fetch("/mine");
  const data = await response.json();
  alert(data.message);
  loadChain();
}

async function bftNextRound() {
  const response = await fetch("/bft/next_round");
  const data = await response.json();
  alert(data.message);
  loadChain();
}

async function switchToPoW() {
  const response = await fetch("/consensus_mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "pow" })
  });
  const data = await response.json();
  alert(data.message);
  loadChain();
}

async function switchToBFT() {
  const response = await fetch("/consensus_mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "bft" })
  });
  const data = await response.json();
  alert(data.message);
  loadChain();
}
