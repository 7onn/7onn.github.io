---
title: "TCP Connections and Buffers in Go"
date: 2024-01-12T19:00:00+01:00
tags: [engineering, go, golang, tcp, connections, buffers]
author: Tom M G
draft: false
---

## Introduction
It's a Friday, but I'm on call, so I can't go out with my friends. Also, my New Year's resolution for 2024 was to study and write more. So, here's this post.

Software engineers are are usually very keen on common internet protocols like HTTP(S), WebSocket (which is an HTTP connection that stays alive even after the server has responded), and gRPC. But then I thought "I've never written a TCP server" and I decided to do one.

## Hands on!

I have written the following server
```go
// server.go
package main

import (
	"fmt"
	"net"
	"os"
)

func main() {
	listener, err := net.Listen("tcp", "localhost:2121")
	if err != nil {
		fmt.Printf("%+v\n", err)
		os.Exit(1)
	}
	defer listener.Close()

	fmt.Println("tcp server is listening on ::2121")
	for {
		// blocks the execution until a connection arrives
		conn, err := listener.Accept()
		if err != nil {
			fmt.Printf("%+v\n", err)
			os.Exit(1)
		}

		go func(conn net.Conn) {
			defer conn.Close()
			i := 0
			for {
				i++
				buffer := make([]byte, 8)
				n, err := conn.Read(buffer)
				if err != nil {
					fmt.Printf("%+v\n", err)
					return
				}

				n, err = conn.Write(buffer[:n])
				if err != nil {
					fmt.Printf("%+v\n", err)
					return
				}
				fmt.Println("got", string(buffer[:n]), "sent", string(buffer[:n]))
			}
		}(conn)
	}

}
```

This server uses the Golang `net` package and listens via the TCP protocol on port 2121. Then it waits for a client to connect to it, and when the connection happens, it triggers a new Go routine to handle it. It can only read the first 8 bytes (8 characters) sent by the client and just reply back what it got.
```bash
$ go run server.go
...
tcp server is listening on ::2121
```

Ok, its listening and apparently ready to receive connections. Now, let's create a client to interact with it.

```go
// client.go
package main

import (
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

func main() {
	conn, err := net.Dial("tcp", "localhost:2121")
	if err != nil {
		fmt.Printf("error connecting to server %+v \n", err)
		os.Exit(1)
	}
	defer conn.Close()
	i := 0
	for {
		i++
		n, err := conn.Write([]byte(fmt.Sprintf("%d", i)))
		if err != nil {
			fmt.Printf("%+v\n", err)
			os.Exit(1)
		}

		buffer := make([]byte, 8)
		n, err = conn.Read(buffer)
		if err != nil && err != io.EOF {
			fmt.Printf("%+v\n", err)
			os.Exit(1)
		}
		fmt.Println("sent", i, "got", string(buffer[:n]))
		time.Sleep(time.Second)
	}

}

```
This client also uses the Golang `net` package and dials `localhost:2121`  using the TCP protocol. If the server is up, the connection should succeed and the client will start an infinite loop. For each iteration, it will increment an INT value and send it as a payload to the server, printing what it requested and what it got. It also sleeps briefly so we don't flood the terminal.

Open a new terminal session and run it:
```bash
$ go run client.go
...
sent 1 got 1
sent 2 got 2
sent 3 got 3
sent 4 got 4
sent 5 got 5
sent 6 got 6
sent 7 got 7
```

You should see the following server's output
```bash
tcp server is listening on ::2121
got 1 sent 1
got 2 sent 2
got 3 sent 3
got 4 sent 4
got 5 sent 5
got 6 sent 6
got 7 sent 7
```

Ok, cool! Now, what? We have established a connection between the client and the server, and they commnunicate using the TCP protocol. But, what is the problem with this code? The buffer can only handle 8 characters and nothing more. So you might think "it would break when it reached 10^9, i.e. 100 million seconds later", right? I thought so! But to my surprise something else happened. Instead of waiting for ~38 months, I decided to reduce the buffer size to 1 on the server side (server.go#L32). And then ran it again.



```bash
$ go run server.go
...
tcp server is listening on ::2121
```

```bash
$ go run client.go
...
sent 7 got 7
sent 8 got 8
sent 9 got 9
sent 10 got 10
sent 11 got 1
sent 12 got 1
sent 13 got 12
sent 14 got 13
sent 15 got 14
sent 16 got 15
```

By the moment the digit gets reaches length 2, we notice weird responses. The server filled what it could in the buffer of size 1 and proceeded with the response. Leaving for the next `conn.Read(buffer)`, in the next iteration, the job of processing the rest of the previous payload.

```bash
# server.go
got 7 sent 7
got 8 sent 8
got 9 sent 9
got 1 sent 1
got 0 sent 0
got 1 sent 1
got 1 sent 1
got 1 sent 1
got 2 sent 2
got 1 sent 1
got 3 sent 3
got 1 sent 1
got 4 sent 4
```

## Conclusion
TCP is nice, it is one of the core protocols of the IP stack, it operates on the [OSI model's L4 (transport layer)][osi-wiki], and it provides a reliable connection between two parties on a network through a "handshake", i.e. the server acknowledges the incoming client connection and the client is sure that the content will arrive at its destination. It also ensures that data  arrives in the same order as it was sent. 

However, because it abstracts nothing but byte streams, it becomes a burden to reason the payload (unlike when we send e.g. json over http).

If you only need to send short, schemaless text messages between two parties on a network, consider using TCP instead [L7 protocols][osi-app-wiki]. And if you can afford to lose some of the messages, [UDP][udp] would deliver them even with a better transmission performance, as it would skip some communication steps and "just send it".

I'll play around with UDP in Go in another post.

[osi-wiki]: https://en.wikipedia.org/wiki/OSI_model
[osi-app-wiki]: https://en.wikipedia.org/wiki/Application_layer
[udp]: https://en.wikipedia.org/wiki/User_Datagram_Protocol
