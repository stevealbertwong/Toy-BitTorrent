# Toy-BitTorrent

This project is a learning experience for me on how BitTorrent Protocol works in a Distributed System settings


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



### TODO

still needs to implement some algorithm 

```
- send outgoing block data logic(PieceMessage / BlockMessage) -> now just purely requesting data from peers

- re-requests for non-received or corrupted data

- peers periodically ping tracker for updated list of peers(seeders, leechers)

- random first piece

- rarest pieces first 

- endgame mode

- choking mechanism
```
