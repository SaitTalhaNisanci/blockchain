from time import time
from json import JSONEncoder
import hashlib
from uuid import uuid4
import json
from urllib.parse import urlparse
from flask import Flask,jsonify,request
import requests

class Blockchain(object):
    def __init__(self):


        self.chain = []
        self.current_transactions = []
        # Number of leading zeros for proof of work algorithm
        self.difficulty = 4
        self.nodes = set()
        self.create_genesis_block()

    def register_node(self,address):
        """
        Add a new node to the nodes

        :param address: <str> address of the node to be added
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netlock)

    def valid_chain(self,chain):
        """
        Checks if the given chain is valid
        :param chain: <list> a blockchain
        :return: <boolean> True if valid.
        """
        if len(chain) == 0:
            return True
        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            cur_block = chain[current_index]

            if getattr(cur_block,'previous_hash') != self.calculate_hash(previous_block):
                return False
            if not self.is_valid_proof(getattr(previous_block,'proof'),getattr(cur_block,'proof')):
                return False
            previous_block = cur_block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        The consensus algorithm used here resolves conflicts by replacing our chain with the longest one in the network
        :return: <bool> True if our chain was replaced

        """

        nodes = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in nodes:
            response = requests.get('http://'+node+'/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                length = len(chain)
                if length > max_length:
                    max_length = length
                    new_chain = chain
        if new_chain:
            return True
        return False
    def new_block(self,proof,previous_hash=None):
        """

        :param proof: <int> a proof to solve PoW algorithm
        :param previous_hash: <str> hash of the previous block
        :return: a new block object
        """
        block = Block(
            index= len(self.chain) +1,
            timestamp= time(),
            proof=proof,
            previous_hash=previous_hash,
            transactions= self.current_transactions,
        )

        # Clear the current transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, receiver, amount):
        # Adds a new transactions to current transactions
        """

        :param sender: <str> address of the sender
        :param receiver: <str> address of the receiver
        :param amount: <float> amount
        :return: <int> the index of the block that will hold the transaction
        """
        self.current_transactions.append(
            {
                'sender': sender,
                'receiver': receiver,
                'amount': amount,
            }
        )
        return self.last_block.__dict__['index']+1

    def create_genesis_block(self):
        # Creates the genesis block
        self.new_block(proof=100,previous_hash= 0)
    @staticmethod
    def calculate_hash(block):
        """
        Calculates the hash value for the given block

        :param block: a block object
        :return: <str> hash value
        """
        block_string =  json.dumps(block.__dict__,sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the lass block in the chain
        return self.chain[-1]

    def is_valid_proof(self,last_proof,nonce):
        """
        Validates the proof by checking the first 4 chars
        :param last_proof: <int> previous proof
        :param nonce: <int> current proposed proof
        :return: <bool> True if correct
        """
        guess = {
            'last_proof' :last_proof,
            'nonce' :nonce,
        }
        block_string =  json.dumps(guess,sort_keys=True).encode()
        proposed_hash = hashlib.sha256(block_string).hexdigest()
        return proposed_hash[:self.difficulty] == "0"* self.difficulty
    def proof_of_work(self,last_proof):
        """
        Find a nonce that will give 'difficult' leading zeros

        :param last_proof: <int>
        :return: <int> the found nonce
        """

        nonce = 0
        while self.is_valid_proof(last_proof,nonce) != True:
            nonce +=1

        return nonce

class Block(object):

    def __init__(self,index,timestamp,transactions,proof,previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.previous_hash =previous_hash

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-','')

block_chain = Blockchain()

@app.route('/mine',methods=['GET'])
def mine():
    last_proof = getattr(block_chain.last_block,'proof')
    proof = block_chain.proof_of_work(last_proof)

    # Give a reward for finding a proof
    block_chain.new_transaction(
        sender= '0',
        receiver = node_identifier,
        amount = 1,
    )

    previous_hash = block_chain.calculate_hash(block_chain.last_block)
    block = block_chain.new_block(proof=proof,previous_hash=previous_hash)
    block_dict = block.__dict__
    response ={
        'message':'new block is mined',
        'index':block_dict['index'],
        'transactions':block_dict['transactions'],
        'proof':block_dict['proof'],
        'previous_hash':block_dict['previous_hash'],
    }
    return jsonify(response),200


@app.route('/transactions/new',methods=['POST'])
def new_transaction():

    values = request.form

    required_fields = ['sender','receiver','amount']
    if not values or not all(rf in values for rf in required_fields):

        return 'Missing fields',400

    index_of_block = block_chain.new_transaction(
        sender=values['sender'],
        receiver=values['receiver'],
        amount=values['amount'],
    )
    response = 'transaction will be added to block ' + str(index_of_block)
    return jsonify(response),201

@app.route('/chain',methods=['GET'])
def chain():
    response = {
        'chain' : block_chain.chain,
    }
    return json.dumps(response,cls=MyEncoder),200
@app.route('/nodes/register',methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes= values.get('nodes')

    if nodes is None:
        return 'supply a valid list of nodes',400

    for node in nodes:
        block_chain.register_node(node)
    response = {
        'message' : 'New nodes have been registered',
        'nodes' : block_chain.nodes
    }
    return jsonify(response),201


@app.route('/consensus',methods=['GET'])
def consensus():
    replaced = block_chain.resolve_conflicts()

    if replaced:
        response = {
            'message' : 'Found a longer chain in the network',
            'chain' : block_chain.chain
        }
    else:
        response = {
            'message' : 'Already has the longest chain',
            'chain' : block_chain.chain
        }
    return json.dumps(response,cls=MyEncoder),200
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5701)