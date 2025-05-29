VERSION ?= 0.2.6
TAVILY_SEARCH_API_KEY ?= ""
CONTAINER_REGISTRY ?= quay.io/ecosystem-appeng
DIST_UI_DIR := $(abspath $(lastword $(MAKEFILE_LIST)/../../../frontend))

setup_local:
	mkdir -p ~/.local
	ollama run qwen2.5vl:latest --keepalive 160m &

	@if podman inspect -f '{{.State.Running}}' llamastack 2>/dev/null | grep -q true; then \
		echo "llamastack is already running."; \
	else \
		echo "Starting or restarting llamastack ..."; \
		podman rm -fv --depend llamastack 2>/dev/null || true; \
		podman run --platform linux/amd64 -d -v llamastack:/root/.llama \
			-p 8321:8321 \
			--env INFERENCE_MODEL="deepseek-v2:16b" \
			--env OLLAMA_URL=http://10.0.2.15:11434 \
			--name llamastack \
			docker.io/llamastack/distribution-ollama:0.2.6; \
	fi

run_ui:
	if podman inspect -f '{{.State.Running}}' ui 2>/dev/null | grep -q true; then \
		echo "ui is already running."; \
	else \
		echo "Starting or restarting ui ...$(PYTHONPATH)"; \
		podman rm -fv --depend ui 2>/dev/null || true; \
		podman run --platform linux/amd64 -it \
			-p 8501:8501 \
			--env LLAMA_STACK_ENDPOINT=http://host.containers.internal:8321 \
			--env TAVILY_SEARCH_API_KEY=$(TAVILY_SEARCH_API_KEY) \
			--name ui \
			docker.io/llamastack-dist-ui:$(VERSION); \
	fi

run_ui_local:
	cd ../../frontend && \
	python3.11 -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt && \
	streamlit run llama_stack/distribution/ui/app.py --server.port 7860 --server.address 0.0.0.0

build_ui:
	podman build --platform linux/amd64 -t llamastack-dist-ui:$(VERSION) -f $(DIST_UI_DIR)/Containerfile $(DIST_UI_DIR)

build_and_push_ui: build_ui
	podman login $(CONTAINER_REGISTRY)
	podman tag llamastack-dist-ui:$(VERSION) $(CONTAINER_REGISTRY)/llamastack-dist-ui:$(VERSION)
	podman push $(CONTAINER_REGISTRY)/llamastack-dist-ui:$(VERSION)
