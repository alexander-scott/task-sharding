package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

var system = System{clients: make(map[*websocket.Conn]bool)} // connected clients
var broadcast = make(chan Message)                           // broadcast channel

// Configure the upgrader
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

type System struct {
	mu      sync.Mutex
	clients map[*websocket.Conn]bool
}

func (s *System) add(conn *websocket.Conn, val bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.clients[conn] = val
}

func (s *System) del(conn *websocket.Conn) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.clients, conn)
}

func (s *System) get() map[*websocket.Conn]bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.clients
}

// Define our message object
type Message struct {
	ID          string `json:"ID"`
	SchemaID    string `json:"schema_id"`
	MessageType int    `json:"message_type"`
}

func main() {
	// Configure websocket route
	http.HandleFunc("/ws", handleConnections)

	// Start listening for incoming chat messages
	go handleIncomingMessages()

	// Start the server on localhost port 8000 and log any errors
	log.Println("http server started on :8000")
	err := http.ListenAndServe(":8000", nil)
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}

func handleConnections(w http.ResponseWriter, r *http.Request) {
	// Upgrade initial GET request to a websocket
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Fatal(err)
	}
	// Make sure we close the connection when the function returns
	defer ws.Close()

	// Register our new client
	system.add(ws, true)

	for {
		var msg Message
		// Read in a new message as JSON and map it to a Message object
		err := ws.ReadJSON(&msg)
		if err != nil {
			log.Printf("error: %v", err)
			system.del(ws)
			break
		}

		msg_marshalled, err := json.Marshal(msg)
		if err != nil {
			log.Printf("Failed to marshall json")
		}
		log.Printf("Received msg: %v", string(msg_marshalled))

		// Send the newly received message to the broadcast channel
		broadcast <- msg
	}
}

func handleIncomingMessages() {
	for {
		// Grab the next message from the broadcast channel
		msg := <-broadcast

		clients := system.get()

		// Send it out to every client that is currently connected
		for client := range clients {
			err := client.WriteJSON(msg)
			if err != nil {
				log.Printf("error: %v", err)
				client.Close()
				system.del(client)
			}
		}
	}
}
