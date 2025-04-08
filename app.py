from flask import Flask, request, jsonify, render_template
from blockchain import Blockchain, Transaction
from consensus import ProofOfWork, TendermintBFT
import json
import os

app = Flask(__name__)

# Global blockchain instance (not thread-safe for real usage)
blockchain = Blockchain()

# Choose consensus: "pow" or "bft"
CONSENSUS_MODE = os.environ.get("CONSENSUS_MODE", "pow")

pow_consensus = ProofOfWork()
bft_consensus = TendermintBFT(validators=["valA", "valB", "valC"])

# For demonstration, let's create a single ephemeral key pair for signing
# In real usage, each user would generate their own.
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chain", methods=["GET"])
def get_chain():
    """
    Returns the current state of the entire blockchain as JSON.
    """
    chain_data = [block.to_dict() for block in blockchain.chain]
    return jsonify({
        "chain": chain_data,
        "length": len(chain_data),
        "consensus_mode": CONSENSUS_MODE
    }), 200

@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    """
    Create a new transaction with the posted data:
    {
      "sender": "...",
      "recipient": "...",
      "amount": 5
    }
    The transaction is signed using our ephemeral private_key for demonstration.
    """
    values = request.get_json()
    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        return "Missing values", 400

    tx = Transaction(
        sender=values["sender"],
        recipient=values["recipient"],
        amount=values["amount"]
    )

    # Sign the transaction with our ephemeral key
    tx.sign_transaction(private_key)
    blockchain.add_transaction(tx)

    response = {"message": "Transaction added successfully"}
    return jsonify(response), 201

@app.route("/mine", methods=["GET"])
def mine():
    """
    If in PoW mode, attempt to mine a new block. In BFT mode, do nothing.
    """
    if CONSENSUS_MODE != "pow":
        return jsonify({"message": "Mining is only available in PoW mode"}), 400

    miner_address = request.args.get("miner", "miner_node")
    new_block = pow_consensus.mine_block(blockchain, miner_address)
    if new_block:
        response = {"message": "New Block Mined", "block": new_block.to_dict()}
        return jsonify(response), 200
    else:
        return jsonify({"message": "Mining failed"}), 400

@app.route("/consensus_mode", methods=["POST"])
def set_consensus_mode():
    """
    Dynamically switch between PoW and BFT. 
    This is not typical in real blockchains but useful for demonstration.
    """
    global CONSENSUS_MODE
    values = request.get_json()
    mode = values.get("mode")
    if mode not in ["pow", "bft"]:
        return jsonify({"message": "Invalid consensus mode"}), 400

    CONSENSUS_MODE = mode
    return jsonify({"message": f"Consensus mode set to {mode}"}), 200

@app.route("/bft/validators", methods=["GET"])
def get_bft_validators():
    if CONSENSUS_MODE != "bft":
        return jsonify({"error": "Not in BFT mode"}), 400
    return jsonify({"validators": bft_consensus.get_validators()}), 200

@app.route("/bft/propose", methods=["POST"])
def bft_propose():
    if CONSENSUS_MODE != "bft":
        return jsonify({"error": "Not in BFT mode"}), 400
    
    if not blockchain.current_transactions:
        return jsonify({"message": "No pending transactions to propose."}), 200

    proposal = bft_consensus.propose_block(blockchain)
    if not proposal:
         return jsonify({"error": "Failed to create proposal"}), 500

    return jsonify({
        "message": f"Validator {proposal['proposer']} proposed Block {proposal['block'].index}",
        "proposal": {
             "proposer": proposal['proposer'],
             "block_index": proposal['block'].index,
             "block_hash": proposal['block'].hash
        }
    }), 200

@app.route("/bft/vote", methods=["POST"])
def bft_vote():
    if CONSENSUS_MODE != "bft":
        return jsonify({"error": "Not in BFT mode"}), 400
    
    votes = bft_consensus.simulate_votes()
    if votes is None:
        return jsonify({"error": "No active proposal to vote on. Please propose first."}), 400
        
    return jsonify({
        "message": "Votes simulated.",
        "votes": votes,
        "required_threshold": (2 * len(bft_consensus.get_validators())) // 3 + 1
    }), 200

@app.route("/bft/commit", methods=["POST"])
def bft_commit():
    if CONSENSUS_MODE != "bft":
        return jsonify({"error": "Not in BFT mode"}), 400
    
    committed_block, message = bft_consensus.commit_block(blockchain)
    
    if committed_block:
        return jsonify({
            "message": message,
            "block": committed_block.to_dict()
        }), 200
    else:
        status_code = 400 if "Consensus failed" in message else 500
        return jsonify({"error": message}), status_code

if __name__ == "__main__":
    # Run Flask app
    app.run(host="0.0.0.0", port=5001, debug=True)
