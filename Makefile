.PHONY: protos
protos:
	cd protos && buf generate
	cd web/frontend && npm run generate-client

.PHONY: backend
backend:
	cd backend && go build .

