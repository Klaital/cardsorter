.PHONY: setup
setup:
	go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.31.0
	go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0
	go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@v2.18.0
	go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

.PHONY: migrate
migrate:
	migrate -source file://db/schema/ -database postgres://af_gil:$password@tcp(mysql.abandonedfactory.net:3306)/gilgamesh_test

deploy:
	GOOS=linux go build -o cardsorter .
	scp cardsorter kit@klaital.com:/home/kit/bin/cardsorter/
	ssh kit@klaital.com "sudo systemctl restart cardsorter.service"

