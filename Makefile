SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

GODOT ?= godot
BLENDER ?= blender
PYTHON ?= python3
PROJECT := prototype

.PHONY: check reports-check syntax-check import smoke render-check mock-render-check style-render-check rebuild-assets rebuild-mock play mock style-study

check: reports-check syntax-check import smoke

reports-check:
	$(PYTHON) -m unittest discover -s tests -v

syntax-check:
	$(PYTHON) -m py_compile $(PROJECT)/tools/*.py tests/*.py
	bash -n $(PROJECT)/tools/setup_linux.sh
	gdlint $(PROJECT)/*.gd $(PROJECT)/tests/*.gd
	gdformat --check $(PROJECT)/*.gd $(PROJECT)/tests/*.gd

import:
	mkdir -p artifacts
	$(GODOT) --headless --editor --import --path $(PROJECT) 2>&1 | tee artifacts/godot-import.log
	! grep -E 'SCRIPT ERROR:|^ERROR:' artifacts/godot-import.log

smoke: import
	$(GODOT) --headless --path $(PROJECT) --script tests/smoke.gd
	$(GODOT) --headless --path $(PROJECT) --script tests/mock_smoke.gd

render-check: import
	mkdir -p artifacts
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/render.gd -- "$(CURDIR)/artifacts/storm.png" --verify 2>&1 | tee artifacts/storm-render.log
	! grep -E 'SCRIPT ERROR:|^ERROR:' artifacts/storm-render.log
	$(MAKE) mock-render-check
	$(MAKE) style-render-check
	$(MAKE) forest-render-check
	$(MAKE) grove-render-check

.PHONY: clinic-grove grove-render-check
clinic-grove:
	$(GODOT) --path $(PROJECT) res://clinic_grove.tscn

grove-render-check: import
	xvfb-run -a $(GODOT) --audio-driver Dummy --disable-vsync --resolution 720x450 --path $(PROJECT) --script tests/grove_render.gd 2>&1 | tee artifacts/grove-render.log
	! grep -E 'SCRIPT ERROR:|SHADER ERROR:|^ERROR:' artifacts/grove-render.log

.PHONY: forest-slice forest-render-check forest-assets
forest-slice:
	$(GODOT) --path $(PROJECT) res://forest_slice.tscn

forest-assets:
	$(PYTHON) $(PROJECT)/tools/build_spruce.py --atlas-only
	$(BLENDER) --background --python $(PROJECT)/tools/build_spruce.py

forest-render-check: import
	xvfb-run -a $(GODOT) --audio-driver Dummy --disable-vsync --resolution 720x450 --path $(PROJECT) --script tests/forest_render.gd

style-render-check: import
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/style_render.gd 2>&1 | tee artifacts/style-render.log
	! grep -E 'SCRIPT ERROR:|SHADER ERROR:|^ERROR:' artifacts/style-render.log
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/style_render.gd -- --arm=M1 2>&1 | tee artifacts/style-miniature-render.log
	! grep -E 'SCRIPT ERROR:|SHADER ERROR:|^ERROR:' artifacts/style-miniature-render.log
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/painted_render.gd 2>&1 | tee artifacts/painted-render.log
	! grep -E 'SCRIPT ERROR:|SHADER ERROR:|^ERROR:' artifacts/painted-render.log
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/painted_render.gd -- --ignore-aspect 2>&1 | tee artifacts/painted-stretched-render.log
	! grep -E 'SCRIPT ERROR:|SHADER ERROR:|^ERROR:' artifacts/painted-stretched-render.log

mock-render-check: import
	xvfb-run -a $(GODOT) --audio-driver Dummy --path $(PROJECT) --script tests/mock_render.gd -- "$(CURDIR)/artifacts/forest-clinic.png" 2>&1 | tee artifacts/mock-render.log
	! grep -E 'SCRIPT ERROR:|^ERROR:' artifacts/mock-render.log

rebuild-assets:
	$(BLENDER) --background --python $(PROJECT)/tools/build_scene.py
	$(GODOT) --headless --editor --import --path $(PROJECT)

rebuild-mock:
	$(BLENDER) --background --python $(PROJECT)/tools/build_mock_scene.py
	$(GODOT) --headless --editor --import --path $(PROJECT)

play:
	$(GODOT) --path $(PROJECT)

mock:
	$(GODOT) --path $(PROJECT) res://mock_scene.tscn

STYLE_ARM ?= I1

style-study:
	$(GODOT) --path $(PROJECT) res://style_study.tscn -- --arm=$(STYLE_ARM)
