.PHONY: protos
protos:
	cd protos
	buf generate
	cd ..
