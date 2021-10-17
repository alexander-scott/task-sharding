package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"

	"github.com/gorilla/mux"
)

type Article struct {
	Id      string `json:"Id"`
	Title   string `json:"title"`
	Desc    string `json:"desc"`
	Content string `json:"content"`
}

var Articles []Article

// CREATE

func createNewArticle(w http.ResponseWriter, r *http.Request) {
	// get the body of our POST request
	// return the string response containing the request body
	reqBody, _ := ioutil.ReadAll(r.Body)

	var article Article
	json.Unmarshal(reqBody, &article)

	Articles = append(Articles, article)

	json.NewEncoder(w).Encode(article)
}

// READ

func returnAllArticles(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Endpoint hit: returnAllArticles")
	json.NewEncoder(w).Encode(Articles)
}

func returnSingleArticle(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	key := vars["id"]

	for _, article := range Articles {
		if article.Id == key {
			json.NewEncoder(w).Encode(article)
		}
	}
}

// UPDATE

func updateSingleArticle(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var newArticle Article
	reqBody, _ := ioutil.ReadAll(r.Body)
	json.Unmarshal(reqBody, &newArticle)

	for index, article := range Articles {
		if article.Id == id {
			Articles[index] = newArticle
			json.NewEncoder(w).Encode(newArticle)
		}
	}
}

// DELETE

func deleteSingleArticle(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	for index, article := range Articles {
		if article.Id == id {
			json.NewEncoder(w).Encode(article)
			Articles = append(Articles[:index], Articles[index+1:]...)
		}
	}
}

func homePage(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Welcome to the HomePage!")
	fmt.Println("Endpoint Hit: homePage")
}

func handleRequests() {
	myRouter := mux.NewRouter().StrictSlash(true)
	myRouter.HandleFunc("/", homePage)
	myRouter.HandleFunc("/articles", returnAllArticles)
	myRouter.HandleFunc("/article", createNewArticle).Methods("POST")
	myRouter.HandleFunc("/article/{id}", deleteSingleArticle).Methods("DELETE")
	myRouter.HandleFunc("/article/{id}", updateSingleArticle).Methods("PUT")
	myRouter.HandleFunc("/article/{id}", returnSingleArticle)
	log.Fatal(http.ListenAndServe(":10000", myRouter))
}

func main() {
	Articles = []Article{
		{Id: "1", Title: "Hello", Desc: "World", Content: "Hello World"},
		{Id: "2", Title: "Hello 2", Desc: "World 2", Content: "Hello World 2"},
	}

	handleRequests()
}

/*
CREATE
curl \
  --request POST \
  --data '{"Id": "3", "Title": "Hello 3", "Desc": "World 3", "Content": "Hello World 3"}' \
  http://localhost:10000/article

UPDATE
curl \
  --request PUT \
  --data '{"Id": "5", "Title": "Hello 5", "Desc": "World 5", "Content": "Hello World 5"}' \
  http://localhost:10000/article/2

DELETE
curl \
  --request DELETE \
  http://localhost:10000/article/2
*/
