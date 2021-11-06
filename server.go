package main

import (
	"log"
	"net"

	task_director "github.com/alexander-scott/task-director/proto"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
)

type Server struct {
	task_director.UnimplementedChatServiceServer
}

func (s *Server) SayHello(ctx context.Context, message *task_director.Message) (*task_director.Message, error) {
	log.Printf("Received message body from client: %s", message.Body)
	return &task_director.Message{Body: "Hello From the Server!"}, nil
}

func (s *Server) RegisterPeer(ctx context.Context, message *task_director.Peer) (*task_director.Message, error) {
	return &task_director.Message{Body: "Hello From the Server!"}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":9000")
	if err != nil {
		log.Fatalf("Failed to listen on port 9000: %v", err)
	}

	s := Server{}

	grpcServer := grpc.NewServer()

	task_director.RegisterChatServiceServer(grpcServer, &s)

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve gRPC server over port 9000: %v", err)
	}

}
