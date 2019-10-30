# Use latest arch base
FROM archlinux/base:latest

# Init pacman and install git
COPY ./.travis/aur-ci-img/mirrorlist /etc/pacman.d/mirrorlist
RUN pacman-key --init && \
    pacman -Syyu --noconfirm && \
    pacman -S --noconfirm --needed base-devel && \
    pacman -S --noconfirm git

# Install yay
RUN curl -s https://api.github.com/repos/Jguer/yay/releases/latest | \
    grep "browser_download_url.*x86_64.tar.gz" | \
    cut -d : -f 2,3 | \
    tr -d '"' | \
    xargs curl -JL | \
    tar xfz -
RUN mv yay*/yay /usr/local/bin/yay
RUN rm -rf yay*

# Install python for package script
RUN yay -S --noconfirm --needed python python-clicolor

# Add build user with sudo rights
RUN useradd -ms /bin/bash builduser
RUN echo "builduser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/builduser

# Set user to build user
USER builduser
