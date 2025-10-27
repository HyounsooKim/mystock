FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    ca-certificates \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Azure Functions Core Tools
RUN wget -q https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y azure-functions-core-tools-4 \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set up non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Configure git to trust the workspace
RUN git config --system --add safe.directory /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Create workspace directory
RUN mkdir -p /workspace && chown ${USERNAME}:${USERNAME} /workspace

WORKDIR /workspace

USER ${USERNAME}
