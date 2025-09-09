.PHONY: protos
protos:
	cd protos && buf generate 
	mv protos/*.py robot/software/magic_client/
