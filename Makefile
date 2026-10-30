.PHONY: test flash
test:
	c++ -std=c++17 -O2 -Wall -Ifirmware/safety-cutoff/include firmware/safety-cutoff/test/test_cutoff.cpp -o /tmp/test_cutoff && /tmp/test_cutoff
	python3 -m unittest -q
flash:
	cd firmware/safety-cutoff && pio run -e esp32dev -t upload
