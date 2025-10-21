# ============================================================
# Isaac Sim + Conda (env_isaaclab) on Ubuntu 24.04
# ============================================================

FROM ubuntu:22.04

# Avoid interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# ============================================================
# Base dependencies
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    curl \
    git \
    git-lfs \
    ca-certificates \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# GCC/G++ 11 (Isaac Sim requires <=11)
# ============================================================
RUN apt-get update && apt-get install -y gcc-11 g++-11 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 200 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 200 && \
    gcc --version && g++ --version

# ============================================================
# ROS 2 Humble + CycloneDDS runtime (Ubuntu 22.04)
# ============================================================
RUN apt-get update && apt-get install -y curl gnupg2 lsb-release && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
        | tee /etc/apt/sources.list.d/ros2.list > /dev/null && \
    apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-ros-base \
        ros-humble-rmw-cyclonedds-cpp \
        python3-rosdep && \
    rosdep init && rosdep update && \
    rm -rf /var/lib/apt/lists/*

ENV ROS_DISTRO=humble
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV CYCLONEDDS_HOME=/opt/ros/humble
ENV CMAKE_PREFIX_PATH=/opt/ros/humble    

# ============================================================
# Install Miniconda
# ============================================================
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh
ENV PATH=$CONDA_DIR/bin:$PATH

# Use bash for conda activation
SHELL ["/bin/bash", "-c"]

# ============================================================
# Copy and create your Conda environment
# ============================================================
# Make sure ./env_isaaclab.yml is in the same directory as this Dockerfile
COPY env_isaaclab.yml /tmp/env_isaaclab.yml

RUN conda config --set channel_priority flexible && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda update -n base -c defaults conda -y && \
    conda create -n env_isaaclab python=3.11 && \
    echo "source activate env_isaaclab" >> ~/.bashrc

# Activate env by default
ENV CONDA_DEFAULT_ENV=env_isaaclab
ENV PATH=$CONDA_DIR/envs/env_isaaclab/bin:$PATH
RUN pip install --upgrade pip
RUN pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

# ============================================================
# Clone and build Isaac Sim
# ============================================================
WORKDIR /workspace

RUN git clone https://github.com/isaac-sim/IsaacSim.git isaacsim && \
    cd isaacsim && \
    git lfs install && \
    git lfs pull && \
    ./build.sh --skip-compiler-version-check

# ============================================================
# Environment setup
# ============================================================
ENV ISAACSIM_PATH=/workspace/isaacsim
ENV PATH=$ISAACSIM_PATH/_build/linux-x86_64/release:$PATH
WORKDIR $ISAACSIM_PATH

# ============================================================
# Optional: Create a non-root user for safety
# ============================================================
ARG USERNAME=isaac
RUN useradd -m $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER $USERNAME
WORKDIR /home/$USERNAME

# ============================================================
# Default command
# ============================================================
CMD ["/bin/bash"]
