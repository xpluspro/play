# Requires just 1.38.0 or above

default: install

# Install dependencies
install:
  uv sync --all-extras

dev:
  streamlit run src/app.py

container_runtime := env_var_or_default('CONTAINER_RUNTIME', 'podman')

# Build container image
build version='latest':
  {{container_runtime}} build . \
    -f deploy/Containerfile \
    --tag play:{{version}}

# Compose up
[working-directory: 'deploy']
@up:
  {{container_runtime}} compose up -d

# Compose down
[working-directory: 'deploy']
@down:
  {{container_runtime}} compose down
