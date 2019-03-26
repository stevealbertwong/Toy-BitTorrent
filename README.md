# Toy-BitTorrent

This project is a learning experience for me on how BitTorrent Protocol works in a Distributed System settings

## Architecture 
- 1 process 1 BitTorrent server	
	- spawn multiple processes to simulate 1 group of p2p (seeders + leechers)
	- or unit testing each major function 
- 2 threads synchronization without lock/mutex
	- 1 main thread write() variables, another thread just read() variables then run handler functions
	- no race condition

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/BitTorrent-architecture.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/torrent-file-format.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/tracker-request.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/tracker-response.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/p2p.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/p2p-2.png)

![alt text](https://raw.githubusercontent.com/stevealbertwong/Toy-BitTorrent/master/media/p2p-3.png)


## Reference
- http://dandylife.net/docs/BitTorrent-Protocol.pdf
- http://www.cs.tut.fi/kurssit/ELT-53207/lecture05.pdf
- coast project


### TODO

still needs to implement some algorithm 

```
- transport.py -> socket send() and receive()

- send outgoing block data logic(PieceMessage / BlockMessage) -> now just purely requesting data from peers

- re-requests for non-received or corrupted data

- peers periodically ping tracker for updated list of peers(seeders, leechers)

- random first piece

- rarest pieces first 

- endgame mode

- choking mechanism
```
