TAG := ipd
SUDO := sudo
DOCKER := docker

all: build run
	
build:
	$(SUDO) $(DOCKER) build --tag $(TAG) .

run:
	$(SUDO) $(DOCKER) run $(TAG)

.PHONY: all build run
