SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

GODOT ?= godot
BLENDER ?= blender
PYTHON ?= python3
PROJECT := prototype

.PHONY: check reports-check syntax-check import smoke render-check rebuild-assets play

check: reports-check syntax-check import smoke

reports-check:
	$(PYTHON) -m unittest discover -s tests -v

syntax-check:
	$(PYTHON) -m py_compile $(PROJECT)/tools/*.py tests/*.py
	bash -n $(PROJECT)/tools/setup_linux.sh
	gdlint $(PROJECT)/main.gd $(PROJECT)/player.gd $(PROJECT)/tests/*.gd
	gdformat --check $(PROJECT)/main.gd $(PROJECT)/player.gd $(PROJECT)/tests/*.gd

import:
	mkdir -p artifacts
	$(GODOT) --headless --editor --import --path $(PROJECT) 2>&1 | tee artifacts/godot-import.log
	! grep -E 'SCRIPT ERROR:|^ERROR:' artifacts/godot-import.log

smoke: import
	$(GODOT) --headless --path $(PROJECT) --script tests/smoke.gd

render-check: import
	mkdir -p artifacts
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/render.gd -- "$(CURDIR)/artifacts/storm.png" --verify 2>&1 | tee artifacts/storm-render.log
	! grep -E 'SCRIPT ERROR:|^ERROR:' artifacts/storm-render.log

rebuild-assets:
	$(BLENDER) --background --python $(PROJECT)/tools/build_scene.py
	$(GODOT) --headless --editor --import --path $(PROJECT)

play:
	$(GODOT) --path $(PROJECT)
