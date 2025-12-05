TOPO = single-topo/topology.json

BUILD_DIR = pne_out
PCAP_DIR = pcap
LOG_DIR = log

COMPILE_SCRIPT = ../backend-compile.sh

all: build

front-end:
	python3 -m lynette --config service.json

test:
	@$(COMPILE_SCRIPT) "node1"

build:  
	python3 -m lynette --config service.json
	@$(COMPILE_SCRIPT) "node1"

run: dirs
	sudo p4run --config $(TOPO)

dirs:
	mkdir -p $(PCAP_DIR) $(LOG_DIR)

clean:
	rm -rf $(BUILD_DIR)/* 
	rm -rf p4c_out/

cleanall: clean
	rm -r $(BUILD_DIR)/
