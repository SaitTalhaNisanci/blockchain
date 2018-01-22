# blockchain

This is a simple blockchain project.
Python 3 is used during the development of this project.

`pip3 install Flask==0.12.2 requests==2.18.4`

To start the server
`python3 blockchain.py`

To mine a coin send **HTTP GET** to `http://0.0.0.0:5701/mine` you can change the port and ip from the code.

To add a new transaction send **HTTP POST** to `http://0.0.0.0:5701/transactions/new`.

```
{
'sender' : 'address',
'receiver' : 'address',
'amount' : <int>
}
```



To get the current chain send **HTTP GET** to `http://0.0.0.0:5701/chain`

To register nodes send **HTTP POST** to `http://0.0.0.0:5701/nodes/register`

To resolve conflicts between nodes send **HTTP GET** to `http://0.0.0.0:5701/consensus`

You can use **POSTMAN** our **curl** for testing it.

